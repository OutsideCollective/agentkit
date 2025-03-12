"""Tests for ssh_status action.

This module tests the ssh_status action of the SshActionProvider, which allows
checking the status of active SSH connections.
"""

from unittest import mock

from coinbase_agentkit.action_providers.ssh.connection import SSHConnectionError


def test_ssh_status_success(ssh_provider):
    """Test successful SSH status check."""
    # Access the mock pool from the fixture
    mock_pool = ssh_provider.connection_pool
    mock_connection = mock.Mock()
    # Return a string value for connection info rather than a mock
    connection_info = (
        "Connection ID: test-conn\nStatus: Connected\nHost: example.com:22\nUsername: user"
    )
    mock_connection.get_connection_info.return_value = connection_info
    mock_pool.has_connection.return_value = True
    mock_pool.get_connection.return_value = mock_connection

    # Call the method
    result = ssh_provider.ssh_status(
        {
            "connection_id": "test-conn",
        }
    )

    # Verify the result contains the expected connection info
    assert result == connection_info
    mock_pool.get_connection.assert_called_once_with("test-conn")
    mock_connection.get_connection_info.assert_called_once()


def test_ssh_status_not_found(ssh_provider):
    """Test SSH status with connection not found."""
    # Access the mock pool from the fixture
    mock_pool = ssh_provider.connection_pool
    # Mock the get_connection method to raise SSHConnectionError
    error_message = "Connection ID 'test-conn' not found"
    mock_pool.get_connection.side_effect = SSHConnectionError(error_message)

    # Call the method
    result = ssh_provider.ssh_status(
        {
            "connection_id": "test-conn",
        }
    )

    # Verify
    assert "Error: Connection not found:" in result
    mock_pool.get_connection.assert_called_once_with("test-conn")
