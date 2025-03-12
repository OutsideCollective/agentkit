"""Tests for remote_shell action.

This module tests the remote_shell action of the SshActionProvider, which allows
executing commands on a remote server.
"""

from coinbase_agentkit.action_providers.ssh.connection import SSHConnectionError


def test_remote_shell_success(ssh_provider):
    """Test successful remote shell command execution."""
    # Access the mocked connection pool
    mock_pool = ssh_provider.connection_pool
    mock_connection = mock_pool.get_connection.return_value

    # Configure the mocks for this test
    mock_connection.execute.return_value = "Command output"
    mock_pool.has_connection.return_value = True
    mock_connection.is_connected.return_value = True

    # Call the method
    result = ssh_provider.remote_shell(
        {
            "connection_id": "test-conn",
            "command": "ls -la",
        }
    )

    # Verify
    assert "Output from connection 'test-conn':" in result
    assert "Command output" in result
    mock_pool.get_connection.assert_called_once_with("test-conn")
    mock_connection.execute.assert_called_once_with("ls -la", timeout=30, ignore_stderr=False)


def test_remote_shell_connection_not_found(ssh_provider):
    """Test remote shell with connection not found."""
    # Access the mocked connection pool
    mock_pool = ssh_provider.connection_pool

    # Configure the mocks for connection not found
    mock_pool.has_connection.return_value = False

    # Call the method
    result = ssh_provider.remote_shell(
        {
            "connection_id": "test-conn",
            "command": "ls -la",
        }
    )

    # Verify
    assert "Error: Connection ID 'test-conn' not found" in result
    mock_pool.has_connection.assert_called_once_with("test-conn")
    # The get_connection method should not be called if has_connection returns False
    mock_pool.get_connection.assert_not_called()


def test_remote_shell_not_connected(ssh_provider):
    """Test remote shell with inactive connection."""
    # Access the mocked connection pool
    mock_pool = ssh_provider.connection_pool
    mock_connection = mock_pool.get_connection.return_value

    # Configure the mocks for inactive connection
    mock_pool.has_connection.return_value = True
    mock_connection.is_connected.return_value = False

    # Call the method
    result = ssh_provider.remote_shell(
        {
            "connection_id": "test-conn",
            "command": "ls -la",
        }
    )

    # Verify
    assert "Error: Connection state:" in result
    mock_pool.get_connection.assert_called_once_with("test-conn")
    mock_connection.is_connected.assert_called_once()
    # execute should not be called on an inactive connection
    mock_connection.execute.assert_not_called()


def test_remote_shell_execution_error(ssh_provider):
    """Test remote shell with command execution error."""
    # Access the mocked connection pool
    mock_pool = ssh_provider.connection_pool
    mock_connection = mock_pool.get_connection.return_value

    # Configure the mocks for execution error
    mock_pool.has_connection.return_value = True
    mock_connection.is_connected.return_value = True
    mock_connection.execute.side_effect = SSHConnectionError("Command execution failed")

    # Call the method
    result = ssh_provider.remote_shell(
        {
            "connection_id": "test-conn",
            "command": "ls -la",
        }
    )

    # Verify
    assert "Error: Connection:" in result
    assert "Command execution failed" in result
    mock_pool.get_connection.assert_called_once_with("test-conn")
    mock_connection.execute.assert_called_once_with("ls -la", timeout=30, ignore_stderr=False)


def test_remote_shell_missing_command(ssh_provider):
    """Test remote shell with missing command parameter."""
    # Call the method without providing a command
    result = ssh_provider.remote_shell(
        {
            "connection_id": "test-conn",
            # Missing command parameter
        }
    )

    # Verify validation error is returned in the result
    assert "Error: Invalid parameters:" in result
    assert "Field required" in result or "command" in result


def test_remote_shell_empty_command(ssh_provider):
    """Test remote shell with empty command."""
    # Call the method with an empty command
    result = ssh_provider.remote_shell(
        {
            "connection_id": "test-conn",
            "command": "",  # Empty command
        }
    )

    # Verify validation error is returned in the result
    assert "Error: Invalid parameters:" in result
    assert "min_length" in result or "at least" in result or "length" in result
