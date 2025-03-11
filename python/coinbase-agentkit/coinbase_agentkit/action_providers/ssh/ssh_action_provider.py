"""SSH Action Provider.

This module implements the SSH Action Provider, which enables executing
commands on remote servers via SSH, file transfers via SFTP, and connection management.

@module ssh/ssh_action_provider
"""

import contextlib
import os
import uuid
from typing import Any

import paramiko
from pydantic import ValidationError

from ...network import Network
from ..action_decorator import create_action
from ..action_provider import ActionProvider

# Import action schemas
from .schemas import (
    ConnectionStatusSchema,
    DisconnectSchema,
    FileDownloadSchema,
    FileUploadSchema,
    ListConnectionsSchema,
    RemoteShellSchema,
)

# Import SSH implementation classes
from .ssh import (
    SSHConnectionError,
    SSHConnectionParams,
    SSHConnectionPool,
    SSHKeyError,
)


class SshActionProvider(ActionProvider):
    """SshActionProvider provides actions for SSH operations.

    This provider enables connecting to remote servers via SSH and executing commands.
    It supports managing multiple concurrent SSH connections.
    """

    def __init__(self, max_connections: int = 10):
        """Initialize the SshActionProvider."""
        super().__init__("ssh", [])
        self.connection_pool = SSHConnectionPool(max_connections=max_connections)

    @create_action(
        name="ssh_connect",
        description="""
This tool establishes an SSH connection to a remote server.

Required:
- host: Hostname or IP address
- username: SSH username

Optional:
- connection_id: Unique identifier (auto-generated if omitted)
- password: SSH password
- private_key: SSH private key as a string
- private_key_path: Path to private key file
- port: SSH port (default: 22)

Success example:
    Connection ID: my_server
    Successfully connected to host.example.com as username

Failure examples:
    SSH Connection Error: Authentication failed
    SSH Connection Error: Connection refused
    SSH Key Error: Key file not found at /path/to/key

Notes:
- Maintains multiple simultaneous connections
- Use remote_shell to execute commands once connected
- Connection remains active until disconnected
- Either password or key authentication required
- Default key path is ~/.ssh/id_rsa if not specified
""",
        schema=SSHConnectionParams,
    )
    def ssh_connect(self, args: dict[str, Any]) -> str:
        """Establish SSH connection to remote server.

        Args:
            args (dict[str, Any]): Dictionary containing:
                - connection_id: Optional unique identifier for this connection
                - host: Remote server hostname/IP
                - username: SSH username
                - password: Optional SSH password
                - private_key_path: Optional key file path
                - port: Optional port number

        Returns:
            str: Connection status message.

        """
        try:
            if args.get("connection_id") is None:
                args["connection_id"] = str(uuid.uuid4())

            validated_args = SSHConnectionParams(**args)
            connection_id = validated_args.connection_id

            with contextlib.suppress(SSHConnectionError):
                self.connection_pool.close_connection(connection_id)

            connection = self.connection_pool.create_connection(validated_args)
            connection.connect()

            output = [
                f"Connection ID: {connection_id}",
                f"Successfully connected to {connection.params.host} as {connection.params.username}",
            ]

            return "\n".join(output)

        except SSHConnectionError as e:
            return f"SSH Connection Error: {e!s}"
        except SSHKeyError as e:
            return f"SSH Key Error: {e!s}"
        except ValidationError as e:
            return f"Invalid input parameters: {e!s}"

    @create_action(
        name="remote_shell",
        description="""
This tool will execute shell commands on a remote server via SSH.

Required inputs:
- connection_id: Identifier for the SSH connection to use
- command: The shell command to execute on the remote server
- ignore_stderr: If True, stderr output won't cause exceptions
- timeout: Command execution timeout in seconds

Example successful response:
    Output from connection 'my_server':

    Command output from remote server

A failure response will return an error message like:
    Error: No active SSH connection. Please connect first.
    Error: Invalid connection ID.
    Error: Command execution failed.
    Error: SSH connection lost.

Important notes:
- Requires an active SSH connection (use ssh_connect first)
- Use 'ssh_status' to check current connection status
- Commands are executed in the connected SSH session
- Returns command output as a string
- You can install any packages you need on the remote server
""",
        schema=RemoteShellSchema,
    )
    def remote_shell(self, args: dict[str, Any]) -> str:
        """Execute a command on the remote server.

        Args:
            args (dict[str, Any]): Dictionary containing:
                - connection_id: Identifier for the SSH connection to use
                - command: The shell command to execute
                - ignore_stderr: If True, stderr output won't cause exceptions
                - timeout: Command execution timeout in seconds

        Returns:
            str: Command output or error message.

        """
        try:
            validated_args = RemoteShellSchema(**args)
            connection_id = validated_args.connection_id
            command = validated_args.command.strip()
            ignore_stderr = validated_args.ignore_stderr
            timeout = validated_args.timeout

            # Check if connection exists
            if not self.connection_pool.has_connection(connection_id):
                return f"Error: Connection ID '{connection_id}' not found. Use ssh_connect first."

            connection = self.connection_pool.get_connection(connection_id)
            if not connection.is_connected():
                return f"Error: Connection '{connection_id}' is not currently active. Use ssh_connect to establish the connection."

            try:
                result = connection.execute(command, timeout=timeout, ignore_stderr=ignore_stderr)
                return f"Output from connection '{connection_id}':\n\n{result}"

            except SSHConnectionError as e:
                return f"Error: SSH connection lost during execution: {e!s}. Please reconnect using ssh_connect."

        except ValidationError as e:
            return f"Invalid input parameters: {e}"
        except Exception as e:
            return f"Error executing remote command: {e}"

    @create_action(
        name="ssh_disconnect",
        description="""
This tool will disconnect an active SSH connection.

Required inputs:
- connection_id: Identifier for the SSH connection to disconnect

Example successful response:
    Connection ID: my_server
    Disconnected from host.example.com

A failure response will return an error message like:
    Error: Invalid connection ID.

Important notes:
- After disconnection, the connection ID is no longer valid
- You will need to establish a new connection to reconnect
""",
        schema=DisconnectSchema,
    )
    def ssh_disconnect(self, args: dict[str, Any]) -> str:
        """Disconnect from SSH server.

        Args:
            args (dict[str, Any]): Dictionary containing:
                - connection_id: Identifier for the SSH connection to disconnect

        Returns:
            str: Disconnect status message.

        """
        try:
            validated_args = DisconnectSchema(**args)
            connection_id = validated_args.connection_id

            try:
                connection = self.connection_pool.close_connection(connection_id)

                result = (
                    f"Connection ID: {connection_id}\nDisconnected from {connection.params.host}"
                    if connection
                    else f"Connection ID: {connection_id}\nNo active connection to disconnect"
                )

                return result

            except SSHConnectionError as e:
                return f"Error: {e!s}"

        except ValidationError as e:
            return f"Invalid input parameters: {e}"
        except Exception as e:
            return f"Error disconnecting: {e}"

    @create_action(
        name="ssh_status",
        description="""
This tool will check the status of a specific SSH connection.

Required inputs:
- connection_id: Identifier for the SSH connection to check

Example successful response:
    Connection ID: my_server
    Status: Connected
    Host: 192.168.1.100:22
    Username: admin
    Connected since: 2023-01-01 12:34:56

A failure response will return an error message like:
    Error: Invalid connection ID.

Important notes:
- Use this to verify connection status before executing commands
- To list all connections, use the list_connections action
""",
        schema=ConnectionStatusSchema,
    )
    def ssh_status(self, args: dict[str, Any]) -> str:
        """Get status of a specific SSH connection.

        Args:
            args (dict[str, Any]): Dictionary containing:
                - connection_id: Identifier for the SSH connection to check

        Returns:
            str: Connection status information.

        """
        try:
            validated_args = ConnectionStatusSchema(**args)
            connection_id = validated_args.connection_id

            connection = self.connection_pool.get_connection(connection_id)
            return connection.get_connection_info()
        except SSHConnectionError as e:
            return f"SSH Connection Error: {e!s}"
        except ValidationError as e:
            return f"Invalid input parameters: {e}"

    @create_action(
        name="list_connections",
        description="""
This tool will list all active SSH connections.

It does not take any inputs.

Example successful response:
    Active SSH Connections: 2

    Connection ID: server1
    Status: Connected
    Host: 192.168.1.100:22
    Username: admin

    Connection ID: server2
    Status: Not connected

If no connections exist, it will return:
    No active SSH connections
""",
        schema=ListConnectionsSchema,
    )
    def list_connections(self, args: dict[str, Any]) -> str:
        """List all SSH connections in the pool.

        Args:
            args (dict[str, Any]): Empty dictionary (no parameters)

        Returns:
            str: List of all connections with their status.

        """
        try:
            connections = self.connection_pool.get_connections()
            if not connections:
                return "No active SSH connections"

            result = [f"Active SSH Connections: {len(connections)}"]

            for conn_id, connection in connections.items():
                # Add a blank line between connections for readability
                if len(result) > 1:
                    result.append("")

                if connection.is_connected():
                    result.append(f"Connection ID: {conn_id}")
                    result.append("Status: Connected")
                    result.append(f"Host: {connection.params.host}:{connection.params.port}")
                    result.append(f"Username: {connection.params.username}")
                else:
                    result.append(f"Connection ID: {conn_id}")
                    result.append("Status: Not connected")

            return "\n".join(result)

        except Exception as e:
            return f"Error listing connections: {e}"

    @create_action(
        name="ssh_upload",
        description="""
This tool will upload a file to a remote server via SFTP.

Required inputs:
- connection_id: Identifier for the SSH connection to use
- local_path: Path to the local file to upload
- remote_path: Destination path on the remote server

Example successful response:
    File upload successful:
    Local file: /path/to/local/file.txt
    Remote destination: /path/on/server/file.txt

A failure response will return an error message like:
    Error: No active SSH connection. Please connect first.
    Error: Local file not found.
    Error: Permission denied on remote server.

Important notes:
- Requires an active SSH connection (use ssh_connect first)
- Local path must be accessible to the agent
- Remote path must include the target filename, not just a directory
- User running the agent must have permission to read the local file
- SSH user must have permission to write to the remote location
""",
        schema=FileUploadSchema,
    )
    def ssh_upload(self, args: dict[str, Any]) -> str:
        """Upload a file to the remote server.

        Args:
            args (dict[str, Any]): Dictionary containing:
                - connection_id: Identifier for the SSH connection to use
                - local_path: Path to the local file to upload
                - remote_path: Destination path on the remote server

        Returns:
            str: Upload status message.

        """
        try:
            validated_args = FileUploadSchema(**args)
            connection_id = validated_args.connection_id
            local_path = validated_args.local_path
            remote_path = validated_args.remote_path

            # Check if connection exists
            if not self.connection_pool.has_connection(connection_id):
                return f"Error: Connection ID '{connection_id}' not found. Use ssh_connect first."

            # Check if local file exists
            if not os.path.exists(local_path):
                return f"Error: Local file not found at {local_path}"

            if not os.path.isfile(local_path):
                return f"Error: {local_path} is not a file"

            # Get the connection
            connection = self.connection_pool.get_connection(connection_id)

            # Check if connected
            if not connection.is_connected():
                return f"Error: Connection '{connection_id}' is not currently active. Use ssh_connect to establish the connection."

            # Upload the file
            connection.upload_file(local_path, remote_path)

            # Success - provide upload confirmation
            return (
                f"File upload successful:\n"
                f"Local file: {local_path}\n"
                f"Remote destination: {remote_path}"
            )

        except SSHConnectionError as e:
            return f"Error: SSH connection lost during upload: {e!s}. Please reconnect using ssh_connect."
        except paramiko.SFTPError as e:
            return f"Error: SFTP error during upload: {e}"
        except OSError as e:
            return f"Error: I/O error during upload: {e}"
        except ValidationError as e:
            return f"Invalid input parameters: {e}"
        except Exception as e:
            return f"Error uploading file: {e}"

    @create_action(
        name="ssh_download",
        description="""
This tool will download a file from a remote server via SFTP.

Required inputs:
- connection_id: Identifier for the SSH connection to use
- remote_path: Path to the file on the remote server
- local_path: Destination path on the local machine

Example successful response:
    File download successful:
    Remote file: /path/on/server/file.txt
    Local destination: /path/to/local/file.txt

A failure response will return an error message like:
    Error: No active SSH connection. Please connect first.
    Error: Remote file not found.
    Error: Permission denied on local machine.

Important notes:
- Requires an active SSH connection (use ssh_connect first)
- Remote file must exist and be readable by the SSH user
- Local path must include the target filename, not just a directory
- User running the agent must have permission to write to the local path
- If the local file already exists, it will be overwritten
""",
        schema=FileDownloadSchema,
    )
    def ssh_download(self, args: dict[str, Any]) -> str:
        """Download a file from the remote server.

        Args:
            args (dict[str, Any]): Dictionary containing:
                - connection_id: Identifier for the SSH connection to use
                - remote_path: Path to the file on the remote server
                - local_path: Destination path on the local machine

        Returns:
            str: Download status message.

        """
        try:
            validated_args = FileDownloadSchema(**args)
            connection_id = validated_args.connection_id
            remote_path = validated_args.remote_path
            local_path = validated_args.local_path

            # Check if connection exists
            if not self.connection_pool.has_connection(connection_id):
                return f"Error: Connection ID '{connection_id}' not found. Use ssh_connect first."

            # Get the connection
            connection = self.connection_pool.get_connection(connection_id)

            # Check if connected
            if not connection.is_connected():
                return f"Error: Connection '{connection_id}' is not currently active. Use ssh_connect to establish the connection."

            # Expand user directory in local path if it exists
            local_path = os.path.expanduser(local_path)

            # Ensure local directory exists
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)

            # Download the file
            connection.download_file(remote_path, local_path)

            # Success - provide download confirmation
            return (
                f"File download successful:\n"
                f"Remote file: {remote_path}\n"
                f"Local destination: {local_path}"
            )

        except SSHConnectionError as e:
            return f"Error: SSH connection lost during download: {e!s}. Please reconnect using ssh_connect."
        except paramiko.SFTPError as e:
            return f"Error: SFTP error during download: {e}"
        except OSError as e:
            return f"Error: I/O error during download: {e}"
        except ValidationError as e:
            return f"Invalid input parameters: {e}"
        except Exception as e:
            return f"Error downloading file: {e}"

    def supports_network(self, network: Network) -> bool:
        """Check if this provider supports the specified network.

        Args:
            network: The network to check.

        Returns:
            bool: Always True as SSH is network-agnostic.

        """
        return True


def ssh_action_provider(
    max_connections: int = 10,
) -> SshActionProvider:
    """Create a new instance of the SshActionProvider.

    Args:
        max_connections: Maximum number of concurrent SSH connections (default: 10)

    Returns:
        An initialized SshActionProvider

    """
    return SshActionProvider(max_connections=max_connections)
