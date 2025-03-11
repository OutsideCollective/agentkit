"""SSH Connection.

This module implements the SSHConnection class, which manages SSH connections
to remote servers and provides functionality for executing commands.

@module ssh/ssh
"""

import contextlib
import io
import os
from datetime import datetime

import paramiko
from pydantic import BaseModel, Field, model_validator


class SSHConnectionError(Exception):
    """Exception raised for SSH connection errors."""

    pass


class SSHKeyError(Exception):
    """Exception raised for SSH key-related errors."""

    pass


class SSHConnectionParams(BaseModel):
    """Validates SSH connection parameters."""

    connection_id: str = Field(description="Unique identifier for this connection")
    host: str = Field(description="Remote server hostname/IP")
    username: str = Field(description="SSH username")
    password: str | None = Field(None, description="SSH password for authentication")
    private_key: str | None = Field(None, description="SSH private key content as a string")
    private_key_path: str | None = Field(
        None, description="Path to private key file for authentication"
    )
    port: int = Field(22, description="SSH port number")

    @classmethod
    @model_validator(mode="after")
    def check_auth_method_provided(cls):
        """Validates that at least one auth method is provided."""
        if not any([cls.password, cls.private_key, cls.private_key_path]):
            raise ValueError(
                "At least one authentication method must be provided (password, private_key, or private_key_path)"
            )

        # Ensure host and username are not None
        if not cls.host:
            raise ValueError("Host must be provided")
        if not cls.username:
            raise ValueError("Username must be provided")

        return cls


class SSHConnection:
    """Manages an SSH connection to a remote server.

    This class encapsulates all SSH connection functionality including
    establishing connections, executing commands, and managing the connection state.
    """

    def __init__(self, params: SSHConnectionParams):
        """Initialize SSH connection.

        Args:
            params: SSH connection parameters

        Raises:
            ValueError: If the parameters are invalid

        """
        self.params = params
        self.ssh_client = None
        self.connected = False
        self.connection_time = None

    def is_connected(self) -> bool:
        """Check if there's an active SSH connection.

        Returns:
            bool: Whether the connection is active

        """
        if not self.ssh_client:
            return False

        if not self.connected:
            return False

        result = None

        try:
            _, stdout, _ = self.ssh_client.exec_command("echo 1", timeout=5)
            result = stdout.read().decode().strip()
        except Exception:
            pass

        if result != "1":
            self.reset_connection()
            return False

        return True

    def reset_connection(self) -> None:
        """Reset the connection state."""
        self.connected = False
        self.connection_time = None

        if not self.ssh_client:
            return

        with contextlib.suppress(Exception):
            self.ssh_client.close()

        self.ssh_client = None

    def connect(self) -> None:
        """Establish SSH connection using instance attributes.

        Raises:
            SSHKeyError: If there's an issue with the SSH key
            SSHConnectionError: If the connection fails

        """
        params = self.params
        self.disconnect()

        # Connect using the appropriate method based on available credentials
        if params.password:
            self.connect_with_password(params.host, params.username, params.password, params.port)
        elif params.private_key:
            self.connect_with_key(
                params.host,
                params.username,
                params.private_key,
                params.port,
                password=params.password,
            )
        else:
            private_key_path = params.private_key_path or os.getenv(
                "SSH_PRIVATE_KEY_PATH", "~/.ssh/id_rsa"
            )
            private_key_path = os.path.expanduser(private_key_path)
            self.connect_with_key_path(
                params.host,
                params.username,
                private_key_path,
                params.port,
                password=params.password,
            )

        # Verify connection is working
        _, stdout, stderr = self.ssh_client.exec_command('echo "Connection successful"', timeout=5)
        result = stdout.read().decode().strip()

        if result != "Connection successful":
            e = stderr.read().decode().strip()
            self.connected = False
            raise SSHConnectionError(f"Connection test failed: {e!s}")

        self.connected = True
        self.connection_time = datetime.now()

    def _load_key_from_string(self, key_string: str, password: str | None = None) -> paramiko.RSAKey:
        """Load an RSA key from a string.

        Args:
            key_string: Private key content as a string
            password: Optional password for encrypted keys

        Returns:
            paramiko.RSAKey: The loaded key

        Raises:
            SSHKeyError: If there's an issue with the key

        """
        key_file = io.StringIO(key_string)

        try:
            # Try with provided password or None
            return paramiko.RSAKey.from_private_key(key_file, password=password)
        except paramiko.ssh_exception.PasswordRequiredException:
            # If password is required but not provided or incorrect
            raise SSHKeyError("Password-protected key provided but no password was given")
        except Exception as e:
            raise SSHKeyError(f"Failed to load key from string: {e!s}")

    def connect_with_key(
        self,
        host: str,
        username: str,
        private_key: str | paramiko.RSAKey,
        port: int = 22,
        timeout: int = 10,
        password: str | None = None,
    ) -> None:
        """Connect to a remote server using a private key.

        Args:
            host: Remote server hostname/IP
            username: SSH username
            private_key: SSH private key as string or paramiko.RSAKey object
            port: SSH port number (default: 22)
            timeout: Connection timeout in seconds (default: 10)
            password: Optional password for encrypted keys

        """
        try:
            self.disconnect()

            # Initialize the SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # If private_key is a string, load it into a key object
            if isinstance(private_key, str):
                key_obj = self._load_key_from_string(private_key, password=password)
            else:
                key_obj = private_key

            self.ssh_client.connect(
                hostname=host, username=username, pkey=key_obj, port=port, timeout=timeout
            )
        except SSHKeyError:
            # Pass through key errors
            raise
        except Exception as e:
            raise SSHConnectionError(f"Failed to connect with key: {e!s}")

    def connect_with_key_path(
        self,
        host: str,
        username: str,
        private_key_path: str,
        port: int = 22,
        timeout: int = 10,
        password: str | None = None,
    ) -> None:
        """Connect to a remote server using a private key path.

        Args:
            host: Remote server hostname/IP
            username: SSH username
            private_key_path: Path to private key file
            port: SSH port number (default: 22)
            timeout: Connection timeout in seconds (default: 10)
            password: Optional password for encrypted keys

        """
        private_key_path = os.path.expanduser(private_key_path)
        if not os.path.exists(private_key_path):
            raise SSHKeyError(f"Key file not found at {private_key_path}")

        try:
            key_obj = self._load_key_from_file(private_key_path, password=password)
            self.connect_with_key(host, username, key_obj, port=port, timeout=timeout)
        except Exception as e:
            if isinstance(e, SSHKeyError | SSHConnectionError):
                # Pass through SSH-specific errors
                raise
            else:
                raise SSHConnectionError(f"Failed to connect with key file: {e!s}")

    def _load_key_from_file(self, key_path: str, password: str | None = None) -> paramiko.RSAKey:
        """Load an RSA key from a file path.

        Args:
            key_path: Path to the private key file
            password: Optional password for encrypted keys

        Returns:
            paramiko.RSAKey: The loaded key

        Raises:
            SSHKeyError: If there's an issue with the key

        """
        try:
            # Try with provided password or None
            return paramiko.RSAKey.from_private_key_file(key_path, password=password)
        except paramiko.ssh_exception.PasswordRequiredException:
            # If password is required but not provided or incorrect
            raise SSHKeyError("Password-protected key file requires a password")
        except Exception as e:
            raise SSHKeyError(f"Failed to load key file: {e!s}")

    def connect_with_password(
        self, host: str, username: str, password: str, port: int = 22, timeout: int = 10
    ) -> None:
        """Connect to a remote server using a password.

        Args:
            host: Remote server hostname/IP
            username: SSH username
            password: SSH password
            port: SSH port number (default: 22)
            timeout: Connection timeout in seconds (default: 10)

        """
        try:
            self.disconnect()

            # Initialize the SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.ssh_client.connect(
                hostname=host, username=username, password=password, port=port, timeout=timeout
            )
        except Exception as e:
            raise SSHConnectionError(f"Failed to connect with password: {e!s}")

    def execute(self, command: str, timeout: int = 30, ignore_stderr: bool = False) -> str:
        """Execute command on connected server.

        Args:
            command: Shell command to execute
            timeout: Command execution timeout in seconds
            ignore_stderr: If True, stderr output won't cause exceptions

        Returns:
            str: Command output (stdout) and optionally stderr if present

        Raises:
            SSHConnectionError: If connection is lost or command execution fails

        """
        params = self.params
        if not self.is_connected():
            raise SSHConnectionError(
                f"No active SSH connection for {params.connection_id}. Please connect first."
            )

        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            # Get exit status
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error_output = stderr.read().decode()

            # Combine output if stderr has content and we're ignoring stderr
            # or if the command executed successfully despite stderr output
            if error_output and (ignore_stderr or exit_status == 0):
                if output:
                    return f"{output}\n[stderr]: {error_output}"
                return error_output

            # Command failed with stderr output
            if exit_status != 0 and error_output:
                raise SSHConnectionError(
                    f"Command execution failed on {params.connection_id} (exit code {exit_status}): {error_output}"
                )

            # Command failed with no stderr output
            if exit_status != 0:
                raise SSHConnectionError(
                    f"Command execution failed on {params.connection_id} with exit code {exit_status}"
                )

            # No output but successful execution
            if not output and exit_status == 0:
                return ""  # Command executed successfully with no output

            return output

        except Exception as e:
            self.reset_connection()
            raise SSHConnectionError(f"Command execution failed on {params.connection_id}: {e!s}")

    def disconnect(self) -> None:
        """Close SSH connection.

        Raises:
            SSHConnectionError: If disconnection fails

        """
        self.reset_connection()

    def get_connection_info(self) -> str:
        """Get information about the current connection.

        Returns:
            str: Connection information as a formatted string

        """
        params = self.params
        output = [
            f"Connection ID: {params.connection_id}",
        ]

        if self.is_connected():
            connection_time = (
                self.connection_time.strftime("%Y-%m-%d %H:%M:%S")
                if self.connection_time
                else "Unknown"
            )
            output.extend(
                [
                    "Status: Connected",
                    f"Host: {params.host}:{params.port}",
                    f"Username: {params.username}",
                    f"Connected since: {connection_time}",
                ]
            )
        else:
            output.append("Status: Not connected")

        return "\n".join(output)

    def get_sftp_client(self) -> paramiko.SFTPClient:
        """Get an SFTP client from the current SSH connection.

        Returns:
            paramiko.SFTPClient: SFTP client object

        Raises:
            SSHConnectionError: If there's no active connection or SFTP initialization fails

        """
        if not self.is_connected():
            raise SSHConnectionError("No active SSH connection. Please connect first.")

        try:
            return self.ssh_client.open_sftp()
        except Exception as e:
            self.reset_connection()
            raise SSHConnectionError(f"Failed to initialize SFTP client: {e!s}")

    def upload_file(self, local_path: str, remote_path: str) -> None:
        """Upload a local file to the remote server.

        Args:
            local_path: Path to the local file
            remote_path: Destination path on the remote server

        Raises:
            SSHConnectionError: If connection is lost or file transfer fails
            FileNotFoundError: If the local file doesn't exist

        """
        params = self.params
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")

        try:
            sftp = self.get_sftp_client()
            sftp.put(local_path, remote_path)
            sftp.close()
        except Exception as e:
            self.reset_connection()
            raise SSHConnectionError(f"File upload failed for {params.connection_id}: {e!s}")

    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download a file from the remote server.

        Args:
            remote_path: Path to the file on the remote server
            local_path: Destination path on the local machine

        Raises:
            SSHConnectionError: If connection is lost or file transfer fails

        """
        params = self.params
        try:
            sftp = self.get_sftp_client()
            sftp.get(remote_path, local_path)
            sftp.close()
        except Exception as e:
            self.reset_connection()
            raise SSHConnectionError(f"File download failed for {params.connection_id}: {e!s}")

    def list_directory(self, remote_path: str) -> list[str]:
        """List contents of a directory on the remote server.

        Args:
            remote_path: Path to the directory on the remote server

        Returns:
            list[str]: List of filenames in the directory

        Raises:
            SSHConnectionError: If connection is lost or directory listing fails

        """
        params = self.params
        try:
            sftp = self.get_sftp_client()
            files = sftp.listdir(remote_path)
            sftp.close()
            return files
        except Exception as e:
            self.reset_connection()
            raise SSHConnectionError(f"Directory listing failed on {params.connection_id}: {e!s}")

    def __enter__(self):
        """Enter context manager.

        Returns:
            SSHConnection: The connection instance

        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and close all connections.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback

        """
        self.clear_connection_pool()


class SSHConnectionPool:
    """Manages multiple SSH connections.

    This class maintains a pool of SSH connections, limits the total number
    of connections, and provides methods to create, retrieve, and close connections.
    """

    def __init__(self, max_connections: int = 5):
        """Initialize connection pool.

        Args:
            max_connections: Maximum number of concurrent connections

        """
        self.connections = {}
        self.max_connections = max_connections
        # Store connection parameters for reconnection
        self.connection_params = {}

    def has_connection(self, connection_id: str) -> bool:
        """Check if a connection exists in the pool.

        Args:
            connection_id: Unique identifier for the connection

        Returns:
            bool: True if the connection exists in the pool

        """
        return connection_id in self.connections

    def get_connection(self, connection_id: str) -> SSHConnection:
        """Get an existing connection from the pool.

        Args:
            connection_id: Unique identifier for the connection

        Returns:
            SSHConnection: The connection object

        Raises:
            SSHConnectionError: If the connection ID is not found

        """
        if connection_id not in self.connections:
            # If we have params stored but no connection, recreate it
            params = self._get_connection_params(connection_id)
            if params:
                return self.create_connection(params)
            raise SSHConnectionError(f"Connection ID '{connection_id}' not found")
        return self.connections[connection_id]

    def close_idle_connections(self) -> int:
        """Close any idle connections in the pool.

        Returns:
            int: Number of closed connections

        """
        closed_count = 0
        for conn_id, conn in list(self.connections.items()):
            if not conn.is_connected():
                self.close_connection(conn_id)
                closed_count += 1
        return closed_count

    def create_connection(self, params: SSHConnectionParams) -> SSHConnection:
        """Create a new connection and add it to the pool.

        Args:
            params: SSH connection parameters

        Returns:
            SSHConnection: The newly created SSH connection

        Raises:
            SSHConnectionError: If the connection limit is reached
            ValueError: If the connection parameters are invalid

        """
        # Close any idle connections first
        self.close_idle_connections()

        # Check if we're at the connection limit
        if len(self.connections) >= self.max_connections:
            raise SSHConnectionError(f"Connection limit reached ({self.max_connections})")

        try:
            # Store connection parameters for reconnection
            stored_params = self._set_connection_params(params)

            # Create new connection using the parameters object
            connection = SSHConnection(stored_params)

            self.connections[params.connection_id] = connection

            return connection
        except ValueError as e:
            # Remove stored parameters on validation error
            self._remove_connection_params(params.connection_id)
            raise ValueError(
                f"Invalid connection parameters for '{params.connection_id}': {e!s}"
            )

    def close_connection(self, connection_id: str) -> SSHConnection | None:
        """Close and remove a connection from the pool.

        Args:
            connection_id: Unique identifier for the connection

        """
        if connection_id not in self.connections:
            return None

        connection = self.connections[connection_id]
        connection.disconnect()

        del self.connections[connection_id]

        return connection

    def close_and_remove_connection(self, connection_id: str) -> None:
        """Close a connection and remove it completely from the pool including parameters.

        Args:
            connection_id: Unique identifier for the connection

        """
        self.close_connection(connection_id)

        # Also remove stored parameters
        self._remove_connection_params(connection_id)

    def close_all_connections(self) -> None:
        """Close all active connections in the pool."""
        for connection_id in list(self.connections.keys()):
            self.close_connection(connection_id)

    def clear_connection_pool(self) -> None:
        """Close all connections and clear all stored parameters."""
        self.close_all_connections()
        self.connection_params.clear()

    def get_connections(self):
        """Get all connections in the pool.

        Returns:
            dict: Dictionary of all connections

        """
        return self.connections

    def __enter__(self):
        """Enter context manager.

        Returns:
            SSHConnectionPool: The connection pool instance

        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and close all connections.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback

        """
        self.clear_connection_pool()

    def _get_connection_params(self, connection_id: str) -> SSHConnectionParams | None:
        """Get stored connection parameters.

        Args:
            connection_id: Unique identifier for the connection

        Returns:
            SSHConnectionParams: The stored parameters or None if not found

        """
        return self.connection_params.get(connection_id)

    def _set_connection_params(self, params: SSHConnectionParams) -> SSHConnectionParams:
        """Store connection parameters.

        Args:
            params: SSH connection parameters

        Returns:
            SSHConnectionParams: The stored parameters

        Raises:
            ValueError: If the parameters are invalid

        """
        self.connection_params[params.connection_id] = params
        return params

    def _remove_connection_params(self, connection_id: str) -> None:
        """Remove stored connection parameters.

        Args:
            connection_id: Unique identifier for the connection

        """
        if connection_id in self.connection_params:
            del self.connection_params[connection_id]
