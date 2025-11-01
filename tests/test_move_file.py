"""Tests for the obsidian_move_file tool."""

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport


@pytest.mark.asyncio
async def test_move_file_success(obsidian_client: Client[FastMCPTransport]):
    """Test successful file move operation."""
    source_path = "test_move_source.md"
    destination_path = "test_move_destination.md"
    test_content = "# Test Move File\n\nThis file will be moved."

    try:
        # Create source file
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": source_path, "content": test_content},
        )

        # Move the file
        result = await obsidian_client.call_tool(
            name="obsidian_move_file",
            arguments={
                "source_path": source_path,
                "destination_path": destination_path,
                "confirm": True,
            },
        )

        # Verify result structure
        assert result.data["success"] is True
        assert result.data["source_path"] == source_path
        assert result.data["destination_path"] == destination_path

        # Verify destination file exists with correct content
        dest_content = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": destination_path},
        )
        assert dest_content.data == test_content

        # Verify source file no longer exists
        with pytest.raises(Exception):
            await obsidian_client.call_tool(
                name="obsidian_get_file_contents",
                arguments={"filepath": source_path},
            )

    finally:
        # Cleanup - delete destination file if it exists
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": destination_path, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_move_file_requires_confirm(obsidian_client: Client[FastMCPTransport]):
    """Test that move operation requires confirmation."""
    with pytest.raises(Exception) as exc_info:
        await obsidian_client.call_tool(
            name="obsidian_move_file",
            arguments={
                "source_path": "source.md",
                "destination_path": "dest.md",
                "confirm": False,
            },
        )
    assert "confirm must be set to true" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_move_file_source_not_found(obsidian_client: Client[FastMCPTransport]):
    """Test move operation fails gracefully when source doesn't exist."""
    with pytest.raises(Exception) as exc_info:
        await obsidian_client.call_tool(
            name="obsidian_move_file",
            arguments={
                "source_path": "nonexistent_source.md",
                "destination_path": "dest.md",
                "confirm": True,
            },
        )
    assert "failed to read source file" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_move_file_to_subdirectory(obsidian_client: Client[FastMCPTransport]):
    """Test moving file to a subdirectory (creates directory automatically)."""
    source_path = "test_move_to_subdir.md"
    destination_path = "test_subdir/moved_file.md"
    test_content = "# Moving to Subdirectory\n\nThis tests directory creation."

    try:
        # Create source file
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": source_path, "content": test_content},
        )

        # Move to subdirectory
        result = await obsidian_client.call_tool(
            name="obsidian_move_file",
            arguments={
                "source_path": source_path,
                "destination_path": destination_path,
                "confirm": True,
            },
        )

        assert result.data["success"] is True

        # Verify destination file exists
        dest_content = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": destination_path},
        )
        assert dest_content.data == test_content

    finally:
        # Cleanup
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": destination_path, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_rename_file_same_directory(obsidian_client: Client[FastMCPTransport]):
    """Test renaming a file in the same directory."""
    source_path = "original_name.md"
    destination_path = "renamed_file.md"
    test_content = "# Rename Test\n\nTesting rename in same directory."

    try:
        # Create source file
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": source_path, "content": test_content},
        )

        # Rename the file
        result = await obsidian_client.call_tool(
            name="obsidian_move_file",
            arguments={
                "source_path": source_path,
                "destination_path": destination_path,
                "confirm": True,
            },
        )

        assert result.data["success"] is True

        # Verify new name exists with correct content
        dest_content = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": destination_path},
        )
        assert dest_content.data == test_content

    finally:
        # Cleanup
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": destination_path, "confirm": True},
            )
        except Exception:
            pass
