"""Tests for recursive and folders_only options in file listing tools."""

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport


@pytest.mark.asyncio
async def test_list_vault_depth_zero(obsidian_client: Client[FastMCPTransport]):
    """Test listing with max_depth=0 (default behavior - current directory only)."""
    # Create nested structure
    test_files = [
        "root_file.md",
        "subdir1/nested_file1.md",
        "subdir1/nested_file2.md",
        "subdir2/deeply/nested/file.md",
    ]

    try:
        # Create test files
        for filepath in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": f"# {filepath}"},
            )

        # List files with max_depth=0 (no recursion)
        result = await obsidian_client.call_tool(
            name="obsidian_list_files_in_vault",
            arguments={"max_depth": 0},
        )

        files = result.data["files"]
        directories = result.data["directories"]

        # Should only see root-level file
        assert "root_file.md" in files

        # Should see subdirectories
        assert "subdir1" in directories or "subdir1/" in [
            d + "/" for d in directories
        ]
        assert "subdir2" in directories or "subdir2/" in [
            d + "/" for d in directories
        ]

        # Should NOT see nested files
        assert "subdir1/nested_file1.md" not in files
        assert "subdir2/deeply/nested/file.md" not in files

    finally:
        # Cleanup
        for filepath in test_files:
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": filepath, "confirm": True},
                )
            except Exception:
                pass


@pytest.mark.asyncio
async def test_list_vault_unlimited_depth(obsidian_client: Client[FastMCPTransport]):
    """Test listing with max_depth=-1 (unlimited recursion)."""
    test_files = [
        "recursive_root.md",
        "rec_sub1/file1.md",
        "rec_sub1/file2.md",
        "rec_sub2/nested/file3.md",
    ]

    try:
        # Create test files
        for filepath in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": f"# {filepath}"},
            )

        # List files recursively
        result = await obsidian_client.call_tool(
            name="obsidian_list_files_in_vault",
            arguments={"max_depth": -1},
        )

        files = result.data["files"]
        directories = result.data["directories"]

        # Should see root file
        assert "recursive_root.md" in files

        # Should see all nested files
        assert "rec_sub1/file1.md" in files
        assert "rec_sub1/file2.md" in files
        assert "rec_sub2/nested/file3.md" in files

        # Should see all directories
        assert "rec_sub1" in directories
        assert "rec_sub2" in directories
        assert "rec_sub2/nested" in directories

    finally:
        # Cleanup
        for filepath in test_files:
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": filepath, "confirm": True},
                )
            except Exception:
                pass


@pytest.mark.asyncio
async def test_list_dir_unlimited_depth(obsidian_client: Client[FastMCPTransport]):
    """Test listing a directory with max_depth=-1 (unlimited recursion)."""
    base_dir = "test_recursive_dir"
    test_files = [
        f"{base_dir}/file1.md",
        f"{base_dir}/sub1/file2.md",
        f"{base_dir}/sub1/sub2/file3.md",
        f"{base_dir}/sub1/sub2/file4.md",
    ]

    try:
        # Create test files
        for filepath in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": f"# {filepath}"},
            )

        # List directory recursively
        result = await obsidian_client.call_tool(
            name="obsidian_list_files_in_dir",
            arguments={"dirpath": base_dir, "max_depth": -1},
        )

        files = result.data["files"]
        directories = result.data["directories"]

        # Should see all files (paths relative to base_dir)
        assert "file1.md" in files
        assert "sub1/file2.md" in files
        assert "sub1/sub2/file3.md" in files
        assert "sub1/sub2/file4.md" in files

        # Should see nested directories
        assert "sub1" in directories
        assert "sub1/sub2" in directories

    finally:
        # Cleanup
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": base_dir, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_folders_only_vault(obsidian_client: Client[FastMCPTransport]):
    """Test folders_only option for vault listing."""
    test_files = [
        "folders_test1.md",
        "folders_dir1/file.md",
        "folders_dir2/nested/file.md",
    ]

    try:
        # Create test files
        for filepath in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": f"# {filepath}"},
            )

        # List with folders_only=True
        result = await obsidian_client.call_tool(
            name="obsidian_list_files_in_vault",
            arguments={"max_depth": 0, "folders_only": True},
        )

        files = result.data["files"]
        directories = result.data["directories"]

        # Files array should be empty
        assert len(files) == 0

        # Should still see directories
        assert "folders_dir1" in directories
        assert "folders_dir2" in directories

    finally:
        # Cleanup
        for filepath in test_files:
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": filepath, "confirm": True},
                )
            except Exception:
                pass


@pytest.mark.asyncio
async def test_folders_only_unlimited_depth(obsidian_client: Client[FastMCPTransport]):
    """Test combining folders_only with unlimited depth listing."""
    test_files = [
        "combo_test.md",
        "combo_dir1/file1.md",
        "combo_dir1/sub1/file2.md",
        "combo_dir2/file3.md",
    ]

    try:
        # Create test files
        for filepath in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": f"# {filepath}"},
            )

        # List recursively with folders_only=True
        result = await obsidian_client.call_tool(
            name="obsidian_list_files_in_vault",
            arguments={"max_depth": -1, "folders_only": True},
        )

        files = result.data["files"]
        directories = result.data["directories"]

        # Files array should be empty
        assert len(files) == 0

        # Should see all directories including nested ones
        assert "combo_dir1" in directories
        assert "combo_dir1/sub1" in directories
        assert "combo_dir2" in directories

    finally:
        # Cleanup
        for filepath in test_files:
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": filepath, "confirm": True},
                )
            except Exception:
                pass


@pytest.mark.asyncio
async def test_list_dir_folders_only(obsidian_client: Client[FastMCPTransport]):
    """Test folders_only option for directory listing."""
    base_dir = "test_dir_folders"
    test_files = [
        f"{base_dir}/file1.md",
        f"{base_dir}/file2.md",
        f"{base_dir}/subdir1/file.md",
        f"{base_dir}/subdir2/file.md",
    ]

    try:
        # Create test files
        for filepath in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": f"# {filepath}"},
            )

        # List directory with folders_only=True
        result = await obsidian_client.call_tool(
            name="obsidian_list_files_in_dir",
            arguments={"dirpath": base_dir, "max_depth": 0, "folders_only": True},
        )

        files = result.data["files"]
        directories = result.data["directories"]

        # Files should be empty
        assert len(files) == 0

        # Should see subdirectories
        assert "subdir1" in directories
        assert "subdir2" in directories

    finally:
        # Cleanup
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": base_dir, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_default_behavior_unchanged(
    obsidian_client: Client[FastMCPTransport]
):
    """Test that default behavior (no parameters) is unchanged."""
    test_files = [
        "default_test.md",
        "default_dir/nested.md",
    ]

    try:
        # Create test files
        for filepath in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": f"# {filepath}"},
            )

        # Call without any parameters (default behavior)
        result = await obsidian_client.call_tool(
            name="obsidian_list_files_in_vault",
            arguments={},
        )

        files = result.data["files"]
        directories = result.data["directories"]

        # Should see root file
        assert "default_test.md" in files

        # Should see directory but not nested file
        assert "default_dir" in directories
        assert "default_dir/nested.md" not in files

    finally:
        # Cleanup
        for filepath in test_files:
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": filepath, "confirm": True},
                )
            except Exception:
                pass
