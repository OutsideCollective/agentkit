"""Tests for SSH connect action.

This module tests the ssh_connect action of the SshActionProvider, including
successful connections, validation, and error handling.
"""

import uuid
from unittest import mock

from coinbase_agentkit.action_providers.ssh.connection import (
    SSHConnectionError,
    SSHKeyError,
    UnknownHostKeyError,
)
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
    # Note: We can't directly check the parameters for create_connection because
    # the validated args are created inside the method via SSHConnectionSchema
    mock_pool.create_connection.assert_called_once()
    mock_connection.connect.assert_called_once_with()


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
    # Note: We can't directly check the parameters for create_connection because
    # the validated args are created inside the method via SSHConnectionSchema
    mock_pool.create_connection.assert_called_once()
    mock_connection.connect.assert_called_once_with()


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
    assert "Error: Connection:" in result


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


def test_ssh_connect_with_private_key(ssh_provider):
    """Test SSH connection using private key authentication."""
    # Access the mock pool from the fixture
    mock_pool = ssh_provider.connection_pool
    mock_connection = mock.Mock()
    # Mock required properties
    mock_connection.params.host = "example.com"
    mock_connection.params.username = "testuser"
    mock_pool.create_connection.return_value = mock_connection

    # Call the method with private key content
    result = ssh_provider.ssh_connect(
        {
            "connection_id": "test-conn",
            "host": "example.com",
            "username": "testuser",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMockKeyContent\n-----END RSA PRIVATE KEY-----",
        }
    )

    # Verify
    assert "Successfully connected to" in result
    assert "Connection ID: test-conn" in result
    # Note: We can't directly check the parameters for create_connection because
    # the validated args are created inside the method via SSHConnectionSchema
    mock_pool.create_connection.assert_called_once()
    mock_connection.connect.assert_called_once_with()


def test_ssh_connect_with_key_path(ssh_provider):
    """Test SSH connection using private key file path."""
    # Access the mock pool from the fixture
    mock_pool = ssh_provider.connection_pool
    mock_connection = mock.Mock()
    # Mock required properties
    mock_connection.params.host = "example.com"
    mock_connection.params.username = "testuser"
    mock_pool.create_connection.return_value = mock_connection

    # Call the method with key path
    result = ssh_provider.ssh_connect(
        {
            "connection_id": "test-conn",
            "host": "example.com",
            "username": "testuser",
            "private_key_path": "~/.ssh/test_key",
        }
    )

    # Verify
    assert "Successfully connected to" in result
    assert "Connection ID: test-conn" in result
    # Note: We can't directly check the parameters for create_connection because
    # the validated args are created inside the method via SSHConnectionSchema
    mock_pool.create_connection.assert_called_once()
    mock_connection.connect.assert_called_once_with()


def test_ssh_connect_key_error(ssh_provider):
    """Test SSH connection with key file error."""
    # Access the mock pool from the fixture
    mock_pool = ssh_provider.connection_pool
    # Simulate a key error
    mock_pool.create_connection.side_effect = SSHKeyError("Key file not found")

    # Call the method with key path
    result = ssh_provider.ssh_connect(
        {
            "connection_id": "test-conn",
            "host": "example.com",
            "username": "testuser",
            "private_key_path": "~/.ssh/nonexistent_key",
        }
    )

    # Verify
    assert "Error: SSH key issue:" in result


def test_ssh_connect_with_custom_port(ssh_provider):
    """Test SSH connection using a custom port."""
    # Access the mock pool from the fixture
    mock_pool = ssh_provider.connection_pool
    mock_connection = mock.Mock()
    # Mock required properties
    mock_connection.params.host = "example.com"
    mock_connection.params.username = "testuser"
    mock_connection.params.port = 2222
    mock_pool.create_connection.return_value = mock_connection

    # Call the method with custom port
    result = ssh_provider.ssh_connect(
        {
            "connection_id": "test-conn",
            "host": "example.com",
            "username": "testuser",
            "password": "testpass",
            "port": 2222,
        }
    )

    # Verify
    assert "Successfully connected to" in result
    assert "Connection ID: test-conn" in result
    # Note: We can't directly check the parameters for create_connection because
    # the validated args are created inside the method via SSHConnectionSchema
    mock_pool.create_connection.assert_called_once()
    mock_connection.connect.assert_called_once_with()


def test_ssh_connect_unknown_host_key(ssh_provider):
    """Test handling of unknown host keys."""
    # Access the mock pool from the fixture
    mock_pool = ssh_provider.connection_pool

    # Mock the key
    mock_key = mock.Mock()
    mock_key.get_name.return_value = "ssh-rsa"
    mock_key.get_base64.return_value = "AAAAB3NzaC1yc2EAAAADAQABAAABAQ=="

    # Simulate an unknown host key error
    mock_pool.create_connection.side_effect = UnknownHostKeyError("example.com", mock_key)

    # Call the method
    result = ssh_provider.ssh_connect(
        {
            "connection_id": "test-conn",
            "host": "example.com",
            "username": "testuser",
            "password": "testpass",
        }
    )

    # Verify the result contains useful information
    assert "Host key verification failed" in result
    assert "example.com" in result
    assert "ssh-rsa" in result
    assert "AAAAB3NzaC1yc2EAAAADAQABAAABAQ==" in result
    assert "ssh_add_host_key" in result

    # Verify it includes the parameters needed to add the key
    assert "host: example.com" in result
    assert "key: AAAAB3NzaC1yc2EAAAADAQABAAABAQ==" in result
    assert "key_type: ssh-rsa" in result
