"""Tests for ssh_add_host_key action.

This module tests the ssh_add_host_key action of the SshActionProvider,
which adds host keys to the SSH known_hosts file.
"""

import os
import tempfile
from unittest import mock

import pytest

from coinbase_agentkit.action_providers.ssh.ssh_action_provider import SshActionProvider


@pytest.fixture
def temp_known_hosts():
    """Create a temporary known_hosts file for testing."""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        # Write some sample entries
        temp_file.write("existing.example.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ==\n")
        temp_file.write("other.example.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHRVs==\n")
        temp_file_path = temp_file.name

    yield temp_file_path

    # Clean up after tests
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


@pytest.fixture
def ssh_provider():
    """Create a fresh SshActionProvider instance for tests."""
    return SshActionProvider()


def test_add_host_key_basic(ssh_provider, temp_known_hosts):
    """Test adding a new host key."""
    # Call the method with a new host
    result = ssh_provider.ssh_add_host_key(
        {
            "host": "test.example.com",
            "key": "AAAAB3NzaC1yc2EAAAADAQABAAABAQ==",
            "known_hosts_file": temp_known_hosts,
        }
    )

    # Verify the result
    assert "successfully added" in result
    assert "test.example.com" in result

    # Check the file content
    with open(temp_known_hosts) as f:
        content = f.read()

    assert "existing.example.com" in content
    assert "test.example.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ==" in content


def test_add_host_key_update_existing(ssh_provider, temp_known_hosts):
    """Test updating an existing host key."""
    # Call the method with an existing host
    result = ssh_provider.ssh_add_host_key(
        {
            "host": "existing.example.com",
            "key": "NEWKEY_AAAAB3NzaC1yc2EAAAADAQABAAABAQ==",
            "known_hosts_file": temp_known_hosts,
        }
    )

    # Verify the result
    assert "updated in" in result
    assert "existing.example.com" in result

    # Check the file content
    with open(temp_known_hosts) as f:
        content = f.read()

    assert "existing.example.com ssh-rsa NEWKEY_AAAAB3NzaC1yc2EAAAADAQABAAABAQ==" in content
    assert "other.example.com" in content


def test_add_host_key_with_custom_port(ssh_provider, temp_known_hosts):
    """Test adding a host key with a non-standard port."""
    # Call the method with a custom port
    result = ssh_provider.ssh_add_host_key(
        {
            "host": "port.example.com",
            "key": "AAAAB3NzaC1yc2EAAAADAQABAAABAQ==",
            "port": 2222,
            "known_hosts_file": temp_known_hosts,
        }
    )

    # Verify the result
    assert "successfully added" in result
    assert "[port.example.com]:2222" in result

    # Check the file content
    with open(temp_known_hosts) as f:
        content = f.read()

    assert "[port.example.com]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ==" in content


def test_add_host_key_with_custom_key_type(ssh_provider, temp_known_hosts):
    """Test adding a host key with a custom key type."""
    # Call the method with a custom key type
    result = ssh_provider.ssh_add_host_key(
        {
            "host": "keytype.example.com",
            "key": "AAAAC3NzaC1lZDI1NTE5AAAAIHRVs==",
            "key_type": "ssh-ed25519",
            "known_hosts_file": temp_known_hosts,
        }
    )

    # Verify the result
    assert "successfully added" in result
    assert "keytype.example.com" in result

    # Check the file content
    with open(temp_known_hosts) as f:
        content = f.read()

    assert "keytype.example.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHRVs==" in content


def test_add_host_key_create_file(ssh_provider):
    """Test adding a host key when the known_hosts file doesn't exist."""
    # Use a non-existent file path
    with tempfile.TemporaryDirectory() as temp_dir:
        new_file_path = os.path.join(temp_dir, "new_known_hosts")

        # Call the method
        result = ssh_provider.ssh_add_host_key(
            {
                "host": "new.example.com",
                "key": "AAAAB3NzaC1yc2EAAAADAQABAAABAQ==",
                "known_hosts_file": new_file_path,
            }
        )

        # Verify the result
        assert "successfully added" in result
        assert "new.example.com" in result

        # Check that the file was created with the right content
        assert os.path.exists(new_file_path)
        with open(new_file_path) as f:
            content = f.read()

        assert "new.example.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ==" in content


def test_add_host_key_invalid_params(ssh_provider):
    """Test adding a host key with invalid parameters."""
    # Call the method with missing required parameters
    result = ssh_provider.ssh_add_host_key(
        {
            # Missing 'host' and 'key'
            "key_type": "ssh-rsa",
        }
    )

    # Verify the result
    assert "Invalid input parameters" in result


@mock.patch("os.path.exists")
@mock.patch("os.makedirs")
@mock.patch("builtins.open", mock.mock_open())
def test_add_host_key_file_error(mock_makedirs, mock_exists, ssh_provider):
    """Test handling file access errors."""
    # Mock os.path.exists to return True
    mock_exists.return_value = True

    # Mock open to raise an OSError
    mock_open = mock.mock_open()
    mock_open.side_effect = OSError("Permission denied")

    with mock.patch("builtins.open", mock_open):
        # Call the method
        result = ssh_provider.ssh_add_host_key(
            {
                "host": "error.example.com",
                "key": "AAAAB3NzaC1yc2EAAAADAQABAAABAQ==",
            }
        )

    # Verify the result
    assert "Error" in result
    assert "Error: File operation:" in result
