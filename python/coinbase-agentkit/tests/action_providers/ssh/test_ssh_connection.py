"""Tests for SSH connection initialization and basic methods.

This module tests the basic functionality of the SSHConnection class, including
initialization, connection establishment, and status checking.
"""

from unittest import mock

import paramiko
import pytest

from coinbase_agentkit.action_providers.ssh.connection import (
    SSHConnection,
    SSHConnectionError,
    SSHConnectionParams,
    SSHKeyError,
)


@pytest.fixture
def connection_params():
    """Create a standard set of connection parameters for testing."""
    return SSHConnectionParams(
        connection_id="test-conn",
        host="example.com",
        username="testuser",
        password="testpass",
    )


@pytest.fixture
def ssh_connection(connection_params):
    """Create an SSH connection instance for testing."""
    return SSHConnection(connection_params)


def test_ssh_connection_initialization(ssh_connection, connection_params):
    """Test that SSH connection is initialized correctly."""
    assert ssh_connection.params == connection_params
    assert ssh_connection.ssh_client is None
    assert ssh_connection.connected is False
    assert ssh_connection.connection_time is None


def test_connect_with_password(ssh_connection):
    """Test connecting with password authentication."""
    # Setup mocks
    with mock.patch("paramiko.SSHClient") as mock_ssh_client_class:
        mock_client = mock_ssh_client_class.return_value
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b"Connection successful"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = mock.Mock()
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        # Call the method
        ssh_connection.connect()

        # Verify
        mock_client.set_missing_host_key_policy.assert_called_once()
        mock_client.connect.assert_called_once_with(
            hostname="example.com",
            username="testuser",
            password="testpass",
            port=22,
            timeout=10,
        )
        assert ssh_connection.connected is True
        assert ssh_connection.connection_time is not None


def test_connect_with_password_failure(ssh_connection):
    """Test handling connection failure with password authentication."""
    # Setup mocks
    with mock.patch("paramiko.SSHClient") as mock_ssh_client_class:
        mock_client = mock_ssh_client_class.return_value
        mock_client.connect.side_effect = paramiko.SSHException("Authentication failed")

        # Call the method and check exception
        with pytest.raises(SSHConnectionError) as exc_info:
            ssh_connection.connect()

        assert "Failed to connect with password" in str(exc_info.value)
        assert ssh_connection.connected is False


def test_connect_with_key(connection_params):
    """Test connecting with private key authentication."""
    # Setup connection params with key
    params = SSHConnectionParams(
        connection_id="test-conn",
        host="example.com",
        username="testuser",
        private_key="KEY_CONTENT",
    )
    ssh_connection = SSHConnection(params)

    # Setup mocks
    with (
        mock.patch("paramiko.SSHClient") as mock_ssh_client_class,
        mock.patch("paramiko.RSAKey") as mock_rsa_key,
    ):
        mock_client = mock_ssh_client_class.return_value
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b"Connection successful"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = mock.Mock()
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        # Mock RSA key loading
        mock_key = mock.Mock()
        mock_rsa_key.from_private_key.return_value = mock_key

        # Call the method
        ssh_connection.connect()

        # Verify
        mock_client.set_missing_host_key_policy.assert_called_once()
        mock_client.connect.assert_called_once_with(
            hostname="example.com",
            username="testuser",
            pkey=mock_key,
            port=22,
            timeout=10,
        )
        assert ssh_connection.connected is True


def test_connect_with_key_path():
    """Test connecting with key path authentication."""
    # Setup connection params with key path
    params = SSHConnectionParams(
        connection_id="test-conn",
        host="example.com",
        username="testuser",
        private_key_path="/path/to/key",
    )
    ssh_connection = SSHConnection(params)

    # Setup mocks
    with (
        mock.patch("paramiko.SSHClient") as mock_ssh_client_class,
        mock.patch("paramiko.RSAKey") as mock_rsa_key,
        mock.patch("os.path.exists") as mock_exists,
        mock.patch("os.path.expanduser") as mock_expanduser,
    ):
        mock_client = mock_ssh_client_class.return_value
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b"Connection successful"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = mock.Mock()
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        # Mock path operations
        mock_expanduser.return_value = "/expanded/path/to/key"
        mock_exists.return_value = True

        # Mock RSA key loading
        mock_key = mock.Mock()
        mock_rsa_key.from_private_key_file.return_value = mock_key

        # Call the method
        ssh_connection.connect()

        # Verify
        mock_client.set_missing_host_key_policy.assert_called_once()
        mock_client.connect.assert_called_once_with(
            hostname="example.com",
            username="testuser",
            pkey=mock_key,
            port=22,
            timeout=10,
        )
        assert ssh_connection.connected is True


def test_connect_with_nonexistent_key_file():
    """Test error when key file doesn't exist."""
    # Setup connection params with key path
    params = SSHConnectionParams(
        connection_id="test-conn",
        host="example.com",
        username="testuser",
        private_key_path="/path/to/key",
    )
    ssh_connection = SSHConnection(params)

    # Mock path operations
    with (
        mock.patch("os.path.exists") as mock_exists,
        mock.patch("os.path.expanduser") as mock_expanduser,
    ):
        mock_expanduser.return_value = "/expanded/path/to/key"
        mock_exists.return_value = False

        # Call the method and check exception
        with pytest.raises(SSHKeyError) as exc_info:
            ssh_connection.connect()

        assert "Key file not found" in str(exc_info.value)


def test_is_connected_true(ssh_connection):
    """Test is_connected when connection is active."""
    # Setup mock client and attach to connection
    with mock.patch("paramiko.SSHClient") as mock_ssh_client_class:
        mock_client = mock_ssh_client_class.return_value
        ssh_connection.ssh_client = mock_client
        ssh_connection.connected = True

        # Mock successful echo test
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b"1"
        mock_client.exec_command.return_value = (None, mock_stdout, None)

        # Call the method
        result = ssh_connection.is_connected()

        # Verify
        assert result is True
        mock_client.exec_command.assert_called_once_with("echo 1", timeout=5)


def test_is_connected_failed_command(ssh_connection):
    """Test is_connected when echo test fails."""
    # Setup mock client and attach to connection
    with mock.patch("paramiko.SSHClient") as mock_ssh_client_class:
        mock_client = mock_ssh_client_class.return_value
        ssh_connection.ssh_client = mock_client
        ssh_connection.connected = True

        # Mock failed echo test
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, None)

        # Call the method
        result = ssh_connection.is_connected()

        # Verify
        assert result is False
        assert ssh_connection.connected is False
        assert ssh_connection.ssh_client is None


def test_is_connected_no_client(ssh_connection):
    """Test is_connected when no SSH client exists."""
    assert ssh_connection.is_connected() is False


def test_is_connected_not_connected_flag(ssh_connection):
    """Test is_connected when connected flag is False."""
    ssh_connection.ssh_client = mock.Mock()
    ssh_connection.connected = False
    assert ssh_connection.is_connected() is False


def test_reset_connection(ssh_connection):
    """Test resetting a connection."""
    # Setup mock client and attach to connection
    with mock.patch("paramiko.SSHClient") as mock_ssh_client_class:
        mock_client = mock_ssh_client_class.return_value
        ssh_connection.ssh_client = mock_client
        ssh_connection.connected = True

        # Call the method
        ssh_connection.reset_connection()

        # Verify
        assert ssh_connection.connected is False
        assert ssh_connection.connection_time is None
        assert ssh_connection.ssh_client is None
        mock_client.close.assert_called_once()


def test_disconnect(ssh_connection):
    """Test disconnecting from SSH server."""
    # Mock reset_connection
    with mock.patch.object(ssh_connection, "reset_connection") as mock_reset:
        ssh_connection.disconnect()
        mock_reset.assert_called_once()


def test_get_connection_info_connected(ssh_connection):
    """Test get_connection_info when connected."""
    # Set connection properties
    ssh_connection.params.connection_id = "test-conn"
    ssh_connection.params.host = "example.com"
    ssh_connection.params.port = 22
    ssh_connection.params.username = "testuser"
    ssh_connection.connected = True

    # Mock is_connected
    with mock.patch.object(ssh_connection, "is_connected", return_value=True):
        info = ssh_connection.get_connection_info()

    # Verify content
    assert "Connection ID: test-conn" in info
    assert "Status: Connected" in info
    assert "Host: example.com:22" in info
    assert "Username: testuser" in info


def test_get_connection_info_not_connected(ssh_connection):
    """Test get_connection_info when not connected."""
    # Set connection properties
    ssh_connection.params.connection_id = "test-conn"

    # Mock is_connected
    with mock.patch.object(ssh_connection, "is_connected", return_value=False):
        info = ssh_connection.get_connection_info()

    # Verify content
    assert "Connection ID: test-conn" in info
    assert "Status: Not connected" in info


def test_connection_context_manager(ssh_connection):
    """Test using SSHConnection as a context manager."""
    # Mock disconnect method
    mock_disconnect = mock.Mock()
    ssh_connection.disconnect = mock_disconnect

    # Use as context manager
    with ssh_connection as conn:
        assert conn is ssh_connection

    # Verify disconnect was called
    mock_disconnect.assert_called_once()
