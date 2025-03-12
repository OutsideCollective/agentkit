"""Tests for SSH command execution.

This module tests the execute method of the SSHConnection class, including
error handling and result processing.
"""

from unittest import mock

import paramiko
import pytest

from coinbase_agentkit.action_providers.ssh.connection import (
    SSHConnection,
    SSHConnectionError,
    SSHConnectionParams,
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


@mock.patch("paramiko.SSHClient")
def test_execute_command_success(mock_ssh_client_class, ssh_connection):
    """Test successful command execution."""
    # Setup mock client and attach to connection
    mock_client = mock_ssh_client_class.return_value
    ssh_connection.ssh_client = mock_client
    ssh_connection.connected = True

    # Mock successful is_connected call
    with mock.patch.object(ssh_connection, "is_connected", return_value=True):
        # Mock successful command execution
        mock_stdin = mock.Mock()
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b"command output"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = mock.Mock()
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # Call the method
        result = ssh_connection.execute("ls -la")

        # Verify
        assert result == "command output"
        mock_client.exec_command.assert_called_once_with("ls -la", timeout=30)


def test_execute_not_connected(ssh_connection):
    """Test execute when not connected."""
    with pytest.raises(SSHConnectionError) as exc_info:
        ssh_connection.execute("ls -la")
    assert "No active SSH connection" in str(exc_info.value)


@mock.patch("paramiko.SSHClient")
def test_execute_command_with_stderr(mock_ssh_client_class, ssh_connection):
    """Test command execution with stderr output but success status."""
    # Setup mock client and attach to connection
    mock_client = mock_ssh_client_class.return_value
    ssh_connection.ssh_client = mock_client
    ssh_connection.connected = True

    # Mock successful is_connected call
    with mock.patch.object(ssh_connection, "is_connected", return_value=True):
        # Mock command with stderr but success status
        mock_stdin = mock.Mock()
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b"command output"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = mock.Mock()
        mock_stderr.read.return_value = b"warning message"
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # Call the method
        result = ssh_connection.execute("ls -la")

        # Verify
        assert result == "command output\n[stderr]: warning message"
        mock_client.exec_command.assert_called_once_with("ls -la", timeout=30)


@mock.patch("paramiko.SSHClient")
def test_execute_command_with_stderr_ignore(mock_ssh_client_class, ssh_connection):
    """Test command execution with stderr output and ignore_stderr=True."""
    # Setup mock client and attach to connection
    mock_client = mock_ssh_client_class.return_value
    ssh_connection.ssh_client = mock_client
    ssh_connection.connected = True

    # Mock successful is_connected call
    with mock.patch.object(ssh_connection, "is_connected", return_value=True):
        # Mock command with stderr and failure status
        mock_stdin = mock.Mock()
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b"command output"
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_stderr = mock.Mock()
        mock_stderr.read.return_value = b"warning message"
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # Call the method with ignore_stderr=True
        result = ssh_connection.execute("ls -la", ignore_stderr=True)

        # Verify
        assert result == "command output\n[stderr]: warning message"
        mock_client.exec_command.assert_called_once_with("ls -la", timeout=30)


@mock.patch("paramiko.SSHClient")
def test_execute_command_failure_stderr(mock_ssh_client_class, ssh_connection):
    """Test command execution failure with stderr output."""
    # Setup mock client and attach to connection
    mock_client = mock_ssh_client_class.return_value
    ssh_connection.ssh_client = mock_client
    ssh_connection.connected = True

    # Mock successful is_connected call
    with mock.patch.object(ssh_connection, "is_connected", return_value=True):
        # Mock failed command with stderr
        mock_stdin = mock.Mock()
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_stderr = mock.Mock()
        mock_stderr.read.return_value = b"command failed"
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # Call the method and check exception
        with pytest.raises(SSHConnectionError) as exc_info:
            ssh_connection.execute("invalid-command")

        assert "Command execution failed" in str(exc_info.value)
        assert "command failed" in str(exc_info.value)
        mock_client.exec_command.assert_called_once_with("invalid-command", timeout=30)


@mock.patch("paramiko.SSHClient")
def test_execute_command_failure_no_stderr(mock_ssh_client_class, ssh_connection):
    """Test command execution failure with no stderr output."""
    # Setup mock client and attach to connection
    mock_client = mock_ssh_client_class.return_value
    ssh_connection.ssh_client = mock_client
    ssh_connection.connected = True

    # Mock successful is_connected call
    with mock.patch.object(ssh_connection, "is_connected", return_value=True):
        # Mock failed command with no stderr
        mock_stdin = mock.Mock()
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_stderr = mock.Mock()
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # Call the method and check exception
        with pytest.raises(SSHConnectionError) as exc_info:
            ssh_connection.execute("invalid-command")

        assert "Command execution failed" in str(exc_info.value)
        assert "exit code 1" in str(exc_info.value)


@mock.patch("paramiko.SSHClient")
def test_execute_command_empty_output(mock_ssh_client_class, ssh_connection):
    """Test command execution with empty but successful output."""
    # Setup mock client and attach to connection
    mock_client = mock_ssh_client_class.return_value
    ssh_connection.ssh_client = mock_client
    ssh_connection.connected = True

    # Mock successful is_connected call
    with mock.patch.object(ssh_connection, "is_connected", return_value=True):
        # Mock successful command with empty output
        mock_stdin = mock.Mock()
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = mock.Mock()
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # Call the method
        result = ssh_connection.execute("touch file.txt")

        # Verify
        assert result == ""  # Empty but successful output
        mock_client.exec_command.assert_called_once_with("touch file.txt", timeout=30)


@mock.patch("paramiko.SSHClient")
def test_execute_command_exception(mock_ssh_client_class, ssh_connection):
    """Test handling exceptions during command execution."""
    # Setup mock client and attach to connection
    mock_client = mock_ssh_client_class.return_value
    ssh_connection.ssh_client = mock_client
    ssh_connection.connected = True

    # Mock successful is_connected call
    with mock.patch.object(ssh_connection, "is_connected", return_value=True):
        # Mock exception during exec_command
        mock_client.exec_command.side_effect = paramiko.SSHException("Connection lost")

        # Call the method and check exception
        with pytest.raises(SSHConnectionError) as exc_info:
            ssh_connection.execute("ls -la")

        assert "Command execution failed" in str(exc_info.value)
        assert "Connection lost" in str(exc_info.value)


@mock.patch("paramiko.SSHClient")
def test_execute_command_custom_timeout(mock_ssh_client_class, ssh_connection):
    """Test command execution with custom timeout."""
    # Setup mock client and attach to connection
    mock_client = mock_ssh_client_class.return_value
    ssh_connection.ssh_client = mock_client
    ssh_connection.connected = True

    # Mock successful is_connected call
    with mock.patch.object(ssh_connection, "is_connected", return_value=True):
        # Mock successful command execution
        mock_stdin = mock.Mock()
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b"command output"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = mock.Mock()
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # Call the method with custom timeout
        result = ssh_connection.execute("ls -la", timeout=60)

        # Verify
        assert result == "command output"
        mock_client.exec_command.assert_called_once_with("ls -la", timeout=60)
