"""Schemas for ssh Action Provider.

This file contains the Pydantic schemas that define the input types
for the ssh action provider's actions.

@module ssh/schemas
"""

from pydantic import BaseModel, Field


class RemoteShellSchema(BaseModel):
    """Schema for remote_shell action."""

    connection_id: str = Field(description="Identifier for the SSH connection to use")
    command: str = Field(
        description="The shell command to execute on the remote server",
        min_length=1,
    )
    ignore_stderr: bool = Field(False, description="If True, stderr output won't cause exceptions")
    timeout: int = Field(30, description="Command execution timeout in seconds")


class DisconnectSchema(BaseModel):
    """Schema for ssh_disconnect action."""

    connection_id: str = Field(description="Identifier for the SSH connection to disconnect")


class ConnectionStatusSchema(BaseModel):
    """Schema for ssh_status action."""

    connection_id: str = Field(description="Identifier for the SSH connection to check status")


class ListConnectionsSchema(BaseModel):
    """Schema for list_connections action."""

    # No parameters needed
    pass


class FileUploadSchema(BaseModel):
    """Schema for ssh_upload action."""

    connection_id: str = Field(description="Identifier for the SSH connection to use")
    local_path: str = Field(description="Path to the local file to upload")
    remote_path: str = Field(description="Destination path on the remote server")


class FileDownloadSchema(BaseModel):
    """Schema for ssh_download action."""

    connection_id: str = Field(description="Identifier for the SSH connection to use")
    remote_path: str = Field(description="Path to the file on the remote server")
    local_path: str = Field(description="Destination path on the local machine")
