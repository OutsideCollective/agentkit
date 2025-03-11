"""Tests for ssh_disconnect action.

This module tests the ssh_disconnect action of the SshActionProvider, which allows
terminating SSH connections and removing them from the connection pool.
"""

from unittest import mock


def test_ssh_disconnect_success(ssh_provider):
    """Test successful SSH disconnection."""
    # Access the mock pool from the fixture
    mock_pool = ssh_provider.connection_pool
    mock_connection = mock.Mock()
    mock_connection.params.host = "example.com"
    mock_pool.has_connection.return_value = True
    mock_pool.close_connection.return_value = mock_connection

    # Call the method
    result = ssh_provider.ssh_disconnect({"connection_id": "test-conn"})

    # Verify
    assert "Connection ID: test-conn" in result
    assert "Disconnected from example.com" in result
    mock_pool.close_connection.assert_called_once_with("test-conn")


def test_ssh_disconnect_not_found(ssh_provider):
    """Test SSH disconnection with connection not found."""
    # Access the mock pool from the fixture
    mock_pool = ssh_provider.connection_pool
    mock_pool.has_connection.return_value = False
    # Return None to indicate no connection was found to close
    mock_pool.close_connection.return_value = None

    # Call the method
    result = ssh_provider.ssh_disconnect({"connection_id": "test-conn"})

    # Verify
    assert "Connection ID: test-conn" in result
    assert "No active connection to disconnect" in result
    mock_pool.close_connection.assert_called_once_with("test-conn")
