"""Tests for SSH connect action.

This module tests the ssh_connect action of the SshActionProvider, including
successful connections, validation, and error handling.
"""

import uuid
from unittest import mock

from coinbase_agentkit.action_providers.ssh.connection import SSHConnectionError
from coinbase_agentkit.action_providers.ssh.ssh_action_provider import SshActionProvider


def test_ssh_connect_success(ssh_provider):
    """Test successful SSH connection."""
    # Access the mock pool from the fixture
    mock_pool = ssh_provider.connection_pool
    mock_connection = mock.Mock()
    # Mock required properties
    mock_connection.params.host = "example.com"
    mock_connection.params.username = "testuser"
    mock_pool.create_connection.return_value = mock_connection

    # Call the method
    result = ssh_provider.ssh_connect(
        {
            "connection_id": "test-conn",
            "host": "example.com",
            "username": "testuser",
            "password": "testpass",
        }
    )

    # Verify
    assert "Successfully connected to" in result
    assert "Connection ID: test-conn" in result
    mock_pool.create_connection.assert_called_once()
    mock_connection.connect.assert_called_once()


def test_ssh_connect_with_auto_id(ssh_provider):
    """Test SSH connection with auto-generated ID."""
    # Access the mock pool from the fixture
    mock_pool = ssh_provider.connection_pool
    mock_connection = mock.Mock()
    # Mock required properties
    mock_connection.params.host = "example.com"
    mock_connection.params.username = "testuser"
    mock_pool.create_connection.return_value = mock_connection

    # Mock uuid generation to get predictable result
    mock_uuid = "mock-uuid-1234"
    with mock.patch.object(uuid, "uuid4", return_value=mock_uuid):
        # Call the method without connection_id
        result = ssh_provider.ssh_connect(
            {
                "host": "example.com",
                "username": "testuser",
                "password": "testpass",
            }
        )

    # Verify
    assert mock_uuid in result
    assert "Successfully connected to" in result
    mock_pool.create_connection.assert_called_once()
    mock_connection.connect.assert_called_once()


def test_ssh_connect_connection_error(ssh_provider):
    """Test SSH connection with connection error."""
    # Access the mock pool from the fixture
    mock_pool = ssh_provider.connection_pool
    # Simulate a connection error
    mock_pool.create_connection.side_effect = SSHConnectionError("Connection failed")

    # Call the method
    result = ssh_provider.ssh_connect(
        {
            "connection_id": "test-conn",
            "host": "example.com",
            "username": "testuser",
            "password": "testpass",
        }
    )

    # Verify
    assert "SSH Connection Error" in result
    assert "Connection failed" in result


def test_ssh_connect_validation_error():
    """Test SSH connection with validation error."""
    # Create a fresh provider for this test (not using the fixture)
    provider = SshActionProvider()

    # Create minimal inputs that will trigger a validation error
    result = provider.ssh_connect(
        {
            # Missing required fields 'host' and 'username'
            "connection_id": "test-conn"
        }
    )

    # Verify
    assert "Invalid input parameters" in result
