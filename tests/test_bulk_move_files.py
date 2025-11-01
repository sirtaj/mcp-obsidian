"""Tests for the obsidian_bulk_move_files tool."""

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport


@pytest.mark.asyncio
async def test_bulk_move_success(obsidian_client: Client[FastMCPTransport]):
    """Test successful bulk move operation."""
    # Create test files
    test_files = [
        ("bulk_test_1.md", "bulk_moved_1.md", "# File 1\n\nContent 1"),
        ("bulk_test_2.md", "bulk_moved_2.md", "# File 2\n\nContent 2"),
        ("bulk_test_3.md", "bulk_moved_3.md", "# File 3\n\nContent 3"),
    ]

    try:
        # Create source files
        for source, _, content in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": source, "content": content},
            )

        # Perform bulk move
        moves = [
            {"source": source, "destination": dest}
            for source, dest, _ in test_files
        ]

        result = await obsidian_client.call_tool(
            name="obsidian_bulk_move_files",
            arguments={"moves": moves, "confirm": True},
        )

        # Verify result structure
        assert result.data["total"] == 3
        assert result.data["successful"] == 3
        assert result.data["failed"] == 0
        assert result.data["success_rate"] == 100.0
        assert len(result.data["results"]) == 3

        # Verify all operations succeeded
        for i, res in enumerate(result.data["results"]):
            assert res["success"] is True
            assert res["index"] == i
            assert "error" not in res

        # Verify destination files exist with correct content
        for _, dest, expected_content in test_files:
            dest_content = await obsidian_client.call_tool(
                name="obsidian_get_file_contents",
                arguments={"filepath": dest},
            )
            assert dest_content.data == expected_content

        # Verify source files no longer exist
        for source, _, _ in test_files:
            with pytest.raises(Exception):
                await obsidian_client.call_tool(
                    name="obsidian_get_file_contents",
                    arguments={"filepath": source},
                )

    finally:
        # Cleanup - delete all destination files
        for _, dest, _ in test_files:
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": dest, "confirm": True},
                )
            except Exception:
                pass


@pytest.mark.asyncio
async def test_bulk_move_requires_confirm(obsidian_client: Client[FastMCPTransport]):
    """Test that bulk move requires confirmation."""
    with pytest.raises(Exception) as exc_info:
        await obsidian_client.call_tool(
            name="obsidian_bulk_move_files",
            arguments={
                "moves": [{"source": "a.md", "destination": "b.md"}],
                "confirm": False,
            },
        )
    assert "confirm must be set to true" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_bulk_move_empty_list(obsidian_client: Client[FastMCPTransport]):
    """Test that bulk move rejects empty list."""
    with pytest.raises(Exception) as exc_info:
        await obsidian_client.call_tool(
            name="obsidian_bulk_move_files",
            arguments={"moves": [], "confirm": True},
        )
    assert "cannot be empty" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_bulk_move_missing_keys(obsidian_client: Client[FastMCPTransport]):
    """Test validation of move operation structure."""
    # Missing 'destination' key
    with pytest.raises(Exception) as exc_info:
        await obsidian_client.call_tool(
            name="obsidian_bulk_move_files",
            arguments={
                "moves": [{"source": "a.md"}],
                "confirm": True,
            },
        )
    assert "missing 'destination' key" in str(exc_info.value).lower()

    # Missing 'source' key
    with pytest.raises(Exception) as exc_info:
        await obsidian_client.call_tool(
            name="obsidian_bulk_move_files",
            arguments={
                "moves": [{"destination": "b.md"}],
                "confirm": True,
            },
        )
    assert "missing 'source' key" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_bulk_move_partial_failure(obsidian_client: Client[FastMCPTransport]):
    """Test that bulk move continues on individual failures."""
    test_files = [
        ("bulk_partial_1.md", "bulk_partial_moved_1.md", "# File 1"),
        # This source doesn't exist - will fail
        ("nonexistent.md", "bulk_partial_moved_2.md", None),
        ("bulk_partial_3.md", "bulk_partial_moved_3.md", "# File 3"),
    ]

    try:
        # Create only the first and third source files
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={
                "filepath": test_files[0][0],
                "content": test_files[0][2],
            },
        )
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={
                "filepath": test_files[2][0],
                "content": test_files[2][2],
            },
        )

        # Perform bulk move
        moves = [
            {"source": source, "destination": dest}
            for source, dest, _ in test_files
        ]

        result = await obsidian_client.call_tool(
            name="obsidian_bulk_move_files",
            arguments={"moves": moves, "confirm": True},
        )

        # Verify results
        assert result.data["total"] == 3
        assert result.data["successful"] == 2
        assert result.data["failed"] == 1
        assert result.data["success_rate"] < 100.0

        # Verify first operation succeeded
        assert result.data["results"][0]["success"] is True
        assert result.data["results"][0]["source"] == test_files[0][0]

        # Verify second operation failed
        assert result.data["results"][1]["success"] is False
        assert "error" in result.data["results"][1]

        # Verify third operation succeeded
        assert result.data["results"][2]["success"] is True
        assert result.data["results"][2]["source"] == test_files[2][0]

    finally:
        # Cleanup
        for _, dest, _ in test_files:
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": dest, "confirm": True},
                )
            except Exception:
                pass


@pytest.mark.asyncio
async def test_bulk_move_to_subdirectories(obsidian_client: Client[FastMCPTransport]):
    """Test bulk moving files to subdirectories (auto-creates directories)."""
    test_files = [
        ("bulk_subdir_1.md", "test_bulk_dir/file1.md", "# File 1"),
        ("bulk_subdir_2.md", "test_bulk_dir/file2.md", "# File 2"),
        ("bulk_subdir_3.md", "test_bulk_dir/nested/file3.md", "# File 3"),
    ]

    try:
        # Create source files
        for source, _, content in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": source, "content": content},
            )

        # Perform bulk move to subdirectories
        moves = [
            {"source": source, "destination": dest}
            for source, dest, _ in test_files
        ]

        result = await obsidian_client.call_tool(
            name="obsidian_bulk_move_files",
            arguments={"moves": moves, "confirm": True},
        )

        assert result.data["successful"] == 3
        assert result.data["failed"] == 0

        # Verify destination files exist
        for _, dest, expected_content in test_files:
            dest_content = await obsidian_client.call_tool(
                name="obsidian_get_file_contents",
                arguments={"filepath": dest},
            )
            assert dest_content.data == expected_content

    finally:
        # Cleanup
        for _, dest, _ in test_files:
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": dest, "confirm": True},
                )
            except Exception:
                pass


@pytest.mark.asyncio
async def test_bulk_rename_same_directory(obsidian_client: Client[FastMCPTransport]):
    """Test bulk renaming files in the same directory."""
    test_files = [
        ("old_name_1.md", "new_name_1.md", "# Content 1"),
        ("old_name_2.md", "new_name_2.md", "# Content 2"),
        ("old_name_3.md", "new_name_3.md", "# Content 3"),
    ]

    try:
        # Create source files
        for source, _, content in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": source, "content": content},
            )

        # Perform bulk rename
        moves = [
            {"source": source, "destination": dest}
            for source, dest, _ in test_files
        ]

        result = await obsidian_client.call_tool(
            name="obsidian_bulk_move_files",
            arguments={"moves": moves, "confirm": True},
        )

        assert result.data["successful"] == 3
        assert result.data["failed"] == 0

        # Verify renamed files exist with correct content
        for _, dest, expected_content in test_files:
            dest_content = await obsidian_client.call_tool(
                name="obsidian_get_file_contents",
                arguments={"filepath": dest},
            )
            assert dest_content.data == expected_content

    finally:
        # Cleanup
        for _, dest, _ in test_files:
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": dest, "confirm": True},
                )
            except Exception:
                pass


@pytest.mark.asyncio
async def test_bulk_move_large_batch(obsidian_client: Client[FastMCPTransport]):
    """Test bulk moving a larger batch of files (10 files)."""
    test_files = [
        (f"bulk_large_{i}.md", f"bulk_large_moved_{i}.md", f"# File {i}\n\nContent {i}")
        for i in range(10)
    ]

    try:
        # Create source files
        for source, _, content in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": source, "content": content},
            )

        # Perform bulk move
        moves = [
            {"source": source, "destination": dest}
            for source, dest, _ in test_files
        ]

        result = await obsidian_client.call_tool(
            name="obsidian_bulk_move_files",
            arguments={"moves": moves, "confirm": True},
        )

        assert result.data["total"] == 10
        assert result.data["successful"] == 10
        assert result.data["failed"] == 0
        assert result.data["success_rate"] == 100.0

        # Verify all destination files exist
        for _, dest, expected_content in test_files:
            dest_content = await obsidian_client.call_tool(
                name="obsidian_get_file_contents",
                arguments={"filepath": dest},
            )
            assert dest_content.data == expected_content

    finally:
        # Cleanup
        for _, dest, _ in test_files:
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": dest, "confirm": True},
                )
            except Exception:
                pass
