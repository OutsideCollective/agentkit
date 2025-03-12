# SSH Action Provider

This directory contains the **SshActionProvider** implementation, which provides actions for interacting with remote servers via SSH.

## Directory Structure

```
ssh/
├── ssh_action_provider.py    # SSH action provider implementation
├── connection.py             # SSH connection management
├── connection_pool.py        # Pool for managing multiple connections
├── schemas.py                # SSH action schemas
├── __init__.py               # Main exports
└── README.md                 # This file

# From python/coinbase-agentkit/
tests/action_providers/ssh/
├── conftest.py               # Test configuration
├── test_ssh_connect.py       # Test SSH connection
├── test_ssh_execute.py       # Test remote command execution
├── test_ssh_status.py        # Test connection status checks
├── test_ssh_disconnect.py    # Test disconnection
├── test_ssh_keys.py          # Test SSH key handling
├── test_ssh_upload.py        # Test file uploads via SFTP
├── test_ssh_download.py      # Test file downloads via SFTP
├── test_ssh_sftp.py          # Test SFTP operations
├── test_remote_shell.py      # Test remote shell commands
├── test_add_host_key.py      # Test adding host keys
├── test_list_connections.py  # Test listing active connections
├── test_ssh_params.py        # Test SSH parameters
├── test_connection_pool.py   # Test connection pool management
└── test_action_provider.py   # Test action provider functionality
```

## Actions

- `ssh_connect`: Establish an SSH connection to a remote server
  - Supports password and key-based authentication
  - Generates a connection ID for future operations if one is not provided

- `remote_shell`: Execute shell commands on the remote server
  - Uses an established connection
  - Returns command output

- `ssh_disconnect`: Close an SSH connection
  - Frees up resources

- `ssh_status`: Check the status of an SSH connection
  - Shows connection details

- `list_connections`: List all active SSH connections
  - Shows connection details for all active connections

- `ssh_upload`: Upload a file to the remote server via SFTP
  - Requires full local and remote paths

- `ssh_download`: Download a file from the remote server via SFTP
  - Requires full local and remote paths

- `ssh_add_host_key`: Add a host key to the known hosts file
  - Useful for host verification

## Adding New Actions

To add new SSH actions:

1. Define your action schema in `schemas.py`
2. Implement the action in `ssh_action_provider.py`
3. Implement tests in a new file in `tests/action_providers/ssh/`

## Notes

- The SSH action provider maintains a pool of connections for efficient management
- Actions like `remote_shell`, `ssh_upload`, and `ssh_download` require an active connection established via `ssh_connect`
- For file transfers (`ssh_upload` and `ssh_download`), full local and remote paths are required

## Prompts

### *Please open an SSH connection to example.com as admin user*

<details>
<summary>Tool Output</summary>

```
Connection ID: conn-123456
Successfully connected to example.com as admin
```
</details>

<details>
<summary>Agent Output</summary>

```
I've established an SSH connection to example.com using the admin user credentials. The connection has been assigned ID conn-123456, which you'll need to reference for any commands or file transfers you want to perform on this server.
```
</details>

### *Run the ls -la command on the remote server*

<details>
<summary>Tool Output</summary>

```
Output from connection 'conn-123456':

total 20
drwxr-xr-x  5 admin admin 4096 Dec 10 12:34 .
drwxr-xr-x 22 root  root  4096 Dec  1 09:00 ..
-rw-r--r--  1 admin admin  220 Dec  1 09:00 .bash_logout
-rw-r--r--  1 admin admin 3771 Dec  1 09:00 .bashrc
-rw-r--r--  1 admin admin  807 Dec  1 09:00 .profile
```
</details>

<details>
<summary>Agent Output</summary>

```
I've executed the 'ls -la' command on the remote server, which shows a detailed listing of all files in the current directory, including hidden files. The output shows the home directory contains the standard bash configuration files (.bash_logout, .bashrc, and .profile) with appropriate permissions.
```
</details>

### *Create a file on the remote server with the current date*

<details>
<summary>Tool Output</summary>

```
Output from connection 'conn-123456':

The file was created successfully.
```
</details>

<details>
<summary>Agent Output</summary>

```
I've created a new file on the remote server containing the current date. I used the 'date' command to get the current date and time, and then redirected its output to a file named 'current_date.txt' in your home directory on the server. The file was created successfully.
```
</details>

### *Upload a local file data.txt to the remote server*

<details>
<summary>Tool Output</summary>

```
File successfully uploaded to /home/admin/data.txt on connection 'conn-123456'
```
</details>

<details>
<summary>Agent Output</summary>

```
I've uploaded the data.txt file to the remote server. The file is now available at /home/admin/data.txt on example.com. If you need to modify this file on the remote server, you can use the remote_shell command to edit it, or download it again after making changes.
```
</details>

### *Download the logs.txt file from the remote server*

<details>
<summary>Tool Output</summary>

```
File successfully downloaded from /home/admin/logs.txt to /home/user/logs.txt on connection 'conn-123456'
```
</details>

<details>
<summary>Agent Output</summary>

```
I've downloaded the logs.txt file from the remote server to your local machine. The file was located at /home/admin/logs.txt on the server and has been saved to /home/user/logs.txt on your local machine. You can now access and analyze these logs locally.
```
</details>

### *Close the SSH connection to example.com*

<details>
<summary>Tool Output</summary>

```
Connection 'conn-123456' successfully closed.
```
</details>

<details>
<summary>Agent Output</summary>

```
I've closed the SSH connection to example.com (connection ID: conn-123456). All resources associated with this connection have been released. If you need to connect again, I can establish a new SSH connection for you.
```
</details>