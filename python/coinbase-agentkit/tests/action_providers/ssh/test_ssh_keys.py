"""Tests for SSH key handling.

This module tests the key handling functionality of the SSHConnection class,
including loading keys from files and strings.
"""

from unittest import mock

import paramiko
import pytest

from coinbase_agentkit.action_providers.ssh.connection import (
    SSHConnection,
    SSHConnectionParams,
    SSHKeyError,
)


@pytest.fixture
def ssh_connection():
    """Create an SSH connection instance for testing."""
    params = SSHConnectionParams(
        connection_id="test-conn",
        host="example.com",
        username="testuser",
        password="testpass",
    )
    return SSHConnection(params)


@mock.patch("paramiko.RSAKey")
def test_load_key_from_string_success(mock_rsa_key, ssh_connection):
    """Test loading an RSA key from a string successfully."""
    # Setup mock
    mock_key = mock.Mock()
    mock_rsa_key.from_private_key.return_value = mock_key

    # Call the method
    key = ssh_connection._load_key_from_string("KEY_CONTENT")

    # Verify
    assert key == mock_key
    assert mock_rsa_key.from_private_key.called


@mock.patch("paramiko.RSAKey")
def test_load_key_from_string_password_required(mock_rsa_key, ssh_connection):
    """Test loading an RSA key that requires a password without providing one."""
    # Setup mock to raise password required exception
    mock_rsa_key.from_private_key.side_effect = paramiko.ssh_exception.PasswordRequiredException()

    # Call the method and check exception
    with pytest.raises(SSHKeyError) as exc_info:
        ssh_connection._load_key_from_string("KEY_CONTENT")

    assert "Password-protected key provided but no password was given" in str(exc_info.value)


@mock.patch("paramiko.RSAKey")
def test_load_key_from_string_other_error(mock_rsa_key, ssh_connection):
    """Test handling other errors when loading an RSA key from a string."""
    # Setup mock to raise generic exception
    mock_rsa_key.from_private_key.side_effect = Exception("Invalid key format")

    # Call the method and check exception
    with pytest.raises(SSHKeyError) as exc_info:
        ssh_connection._load_key_from_string("KEY_CONTENT")

    assert "Failed to load key from string" in str(exc_info.value)


@mock.patch("paramiko.RSAKey")
def test_load_key_from_file_success(mock_rsa_key, ssh_connection):
    """Test loading an RSA key from a file successfully."""
    # Setup mock
    mock_key = mock.Mock()
    mock_rsa_key.from_private_key_file.return_value = mock_key

    # Call the method
    key = ssh_connection._load_key_from_file("/path/to/key")

    # Verify
    assert key == mock_key
    assert mock_rsa_key.from_private_key_file.called


@mock.patch("paramiko.RSAKey")
def test_load_key_from_file_password_required(mock_rsa_key, ssh_connection):
    """Test loading an RSA key file that requires a password without providing one."""
    # Setup mock to raise password required exception
    mock_rsa_key.from_private_key_file.side_effect = (
        paramiko.ssh_exception.PasswordRequiredException()
    )

    # Call the method and check exception
    with pytest.raises(SSHKeyError) as exc_info:
        ssh_connection._load_key_from_file("/path/to/key")

    assert "Password-protected key file requires a password" in str(exc_info.value)


@mock.patch("paramiko.RSAKey")
def test_load_key_from_file_other_error(mock_rsa_key, ssh_connection):
    """Test handling other errors when loading an RSA key from a file."""
    # Setup mock to raise generic exception
    mock_rsa_key.from_private_key_file.side_effect = Exception("Invalid key format")

    # Call the method and check exception
    with pytest.raises(SSHKeyError) as exc_info:
        ssh_connection._load_key_from_file("/path/to/key")

    assert "Failed to load key file" in str(exc_info.value)


@mock.patch("paramiko.RSAKey")
def test_load_key_from_string_with_password(mock_rsa_key, ssh_connection):
    """Test loading a password-protected key from string with password."""
    # Setup mock
    mock_key = mock.Mock()
    mock_rsa_key.from_private_key.return_value = mock_key

    # Call the method
    key = ssh_connection._load_key_from_string("KEY_CONTENT", password="keypass")

    # Verify
    assert key == mock_key
    mock_rsa_key.from_private_key.assert_called_with(mock.ANY, password="keypass")


@mock.patch("paramiko.RSAKey")
def test_load_key_from_file_with_password(mock_rsa_key, ssh_connection):
    """Test loading a password-protected key file with password."""
    # Setup mock
    mock_key = mock.Mock()
    mock_rsa_key.from_private_key_file.return_value = mock_key

    # Call the method
    key = ssh_connection._load_key_from_file("/path/to/key", password="keypass")

    # Verify
    assert key == mock_key
    mock_rsa_key.from_private_key_file.assert_called_with("/path/to/key", password="keypass")
