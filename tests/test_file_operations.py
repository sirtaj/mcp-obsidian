"""
Advanced file operation tests for MCP Obsidian server.

Tests folder creation, file manipulation, and file movement workflows.
"""

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport


class TestFolderOperations:
    """Tests for folder/directory operations."""

    async def test_create_file_in_nested_folder(self, obsidian_client: Client[FastMCPTransport]):
        """Test creating a file in a nested folder structure (creates folders automatically)."""
        nested_path = "test-folders/subfolder1/subfolder2/nested-file.md"
        content = "# Nested File\n\nThis file is in a nested folder structure.\n"

        # Create file - should create all parent directories
        result = await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": nested_path, "content": content}
        )

        assert result.data is None  # Success

        # Verify file was created
        read_result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": nested_path}
        )
        assert read_result.data == content

        # Verify parent directory exists and contains the file
        list_result = await obsidian_client.call_tool(
            name="obsidian_list_files_in_dir",
            arguments={"dirpath": "test-folders/subfolder1/subfolder2"}
        )
        assert "nested-file.md" in list_result.data["files"]

    async def test_create_multiple_files_in_folder(self, obsidian_client: Client[FastMCPTransport]):
        """Test creating multiple files in the same folder."""
        folder = "test-folders/multi-files"
        files = {
            f"{folder}/file1.md": "# File 1\n\nFirst file.\n",
            f"{folder}/file2.md": "# File 2\n\nSecond file.\n",
            f"{folder}/file3.md": "# File 3\n\nThird file.\n",
        }

        # Create all files
        for filepath, content in files.items():
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": content}
            )

        # Verify all files exist in the folder
        list_result = await obsidian_client.call_tool(
            name="obsidian_list_files_in_dir",
            arguments={"dirpath": folder}
        )

        assert "file1.md" in list_result.data["files"]
        assert "file2.md" in list_result.data["files"]
        assert "file3.md" in list_result.data["files"]
        assert len(list_result.data["files"]) >= 3

    async def test_create_folder_hierarchy(self, obsidian_client: Client[FastMCPTransport]):
        """Test creating a complex folder hierarchy with files at different levels."""
        structure = {
            "test-folders/hierarchy/README.md": "# Hierarchy Root\n",
            "test-folders/hierarchy/level1/file.md": "# Level 1\n",
            "test-folders/hierarchy/level1/level2/file.md": "# Level 2\n",
            "test-folders/hierarchy/level1/level2/level3/deep-file.md": "# Level 3\n",
        }

        # Create entire structure
        for filepath, content in structure.items():
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": content}
            )

        # Verify each level
        root_files = await obsidian_client.call_tool(
            name="obsidian_list_files_in_dir",
            arguments={"dirpath": "test-folders/hierarchy"}
        )
        assert "README.md" in root_files.data["files"]
        assert "level1" in root_files.data["directories"]

        level1_files = await obsidian_client.call_tool(
            name="obsidian_list_files_in_dir",
            arguments={"dirpath": "test-folders/hierarchy/level1"}
        )
        assert "file.md" in level1_files.data["files"]
        assert "level2" in level1_files.data["directories"]


class TestFileEditWorkflows:
    """Tests for file creation and editing workflows."""

    async def test_create_edit_append_workflow(self, obsidian_client: Client[FastMCPTransport]):
        """Test complete workflow: create, edit (overwrite), and append to a file."""
        filepath = "test-folders/edit-workflow.md"

        # Step 1: Create initial file
        initial_content = "# Edit Workflow Test\n\nInitial content.\n"
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": initial_content}
        )

        # Verify initial content
        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath}
        )
        assert result.data == initial_content

        # Step 2: Overwrite with new content
        edited_content = "# Edit Workflow Test\n\nEdited content - completely replaced.\n"
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": edited_content}
        )

        # Verify edited content
        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath}
        )
        assert result.data == edited_content

        # Step 3: Append additional content
        appended_text = "\n## Appended Section\n\nThis was appended to the file.\n"
        await obsidian_client.call_tool(
            name="obsidian_append_content",
            arguments={"filepath": filepath, "content": appended_text}
        )

        # Verify final content contains both
        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath}
        )
        assert result.data == edited_content + appended_text
        assert "Edited content" in result.data
        assert "Appended Section" in result.data

    async def test_incremental_content_building(self, obsidian_client: Client[FastMCPTransport]):
        """Test building file content incrementally with multiple appends."""
        filepath = "test-folders/incremental-build.md"

        # Create initial file
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": "# Daily Log\n\n"}
        )

        # Append multiple entries
        entries = [
            "## 10:00 AM\nMorning meeting\n\n",
            "## 2:00 PM\nAfternoon work session\n\n",
            "## 5:00 PM\nEnd of day review\n\n",
        ]

        for entry in entries:
            await obsidian_client.call_tool(
                name="obsidian_append_content",
                arguments={"filepath": filepath, "content": entry}
            )

        # Verify all entries are present
        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath}
        )

        for entry in entries:
            assert entry in result.data
        assert result.data.startswith("# Daily Log")

    @pytest.mark.skip(reason="Patch content requires complex heading syntax - tested separately")
    async def test_patch_content_workflow(self, obsidian_client: Client[FastMCPTransport]):
        """Test using patch_content to insert content at specific locations."""
        filepath = "test-folders/patch-test.md"

        # Create initial file with structure
        initial = """# Main Document

## Introduction
This is the introduction.

## Section 1
First section content.

## Section 2
Second section content.

## Conclusion
Final thoughts.
"""

        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": initial}
        )

        # Patch: Append content after Section 1 heading
        new_content = "\n### Subsection 1.1\nAdded via patch.\n"
        await obsidian_client.call_tool(
            name="obsidian_patch_content",
            arguments={
                "filepath": filepath,
                "operation": "append",
                "target_type": "heading",
                "target": "Section 1",
                "content": new_content
            }
        )

        # Verify patch was applied
        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath}
        )

        assert "Subsection 1.1" in result.data
        assert "Added via patch" in result.data


class TestFileMoveWorkflows:
    """Tests for simulating file move operations (copy + delete)."""

    async def test_move_file_simulation(self, obsidian_client: Client[FastMCPTransport]):
        """Test 'moving' a file by creating at new location and deleting old."""
        source_path = "test-folders/source/original-file.md"
        dest_path = "test-folders/destination/moved-file.md"
        content = "# Original File\n\nThis file will be moved.\n"

        # Create source file
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": source_path, "content": content}
        )

        # Verify source exists
        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": source_path}
        )
        assert result.data == content

        # "Move" by creating at destination
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": dest_path, "content": content}
        )

        # Verify destination exists
        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": dest_path}
        )
        assert result.data == content

        # Delete source to complete "move"
        await obsidian_client.call_tool(
            name="obsidian_delete_file",
            arguments={"filepath": source_path, "confirm": True}
        )

        # Verify source is deleted
        with pytest.raises(Exception) as exc_info:
            await obsidian_client.call_tool(
                name="obsidian_get_file_contents",
                arguments={"filepath": source_path}
            )
        assert "404" in str(exc_info.value)

        # Verify destination still exists
        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": dest_path}
        )
        assert result.data == content

    async def test_rename_file_simulation(self, obsidian_client: Client[FastMCPTransport]):
        """Test 'renaming' a file in the same directory."""
        old_path = "test-folders/rename-test/old-name.md"
        new_path = "test-folders/rename-test/new-name.md"
        content = "# File to Rename\n\nContent stays the same.\n"

        # Create original file
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": old_path, "content": content}
        )

        # Read content
        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": old_path}
        )

        # "Rename" by creating with new name
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": new_path, "content": result.data}
        )

        # Delete old file
        await obsidian_client.call_tool(
            name="obsidian_delete_file",
            arguments={"filepath": old_path, "confirm": True}
        )

        # Verify new file exists with same content
        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": new_path}
        )
        assert result.data == content

        # Verify old file is gone
        with pytest.raises(Exception):
            await obsidian_client.call_tool(
                name="obsidian_get_file_contents",
                arguments={"filepath": old_path}
            )

    async def test_reorganize_multiple_files(self, obsidian_client: Client[FastMCPTransport]):
        """Test reorganizing multiple files into a new folder structure."""
        # Create files in old location
        old_files = {
            "test-folders/old-location/doc1.md": "# Document 1\n",
            "test-folders/old-location/doc2.md": "# Document 2\n",
            "test-folders/old-location/doc3.md": "# Document 3\n",
        }

        for filepath, content in old_files.items():
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": content}
            )

        # Reorganize to new location
        new_location = "test-folders/organized/documents"
        for old_path, content in old_files.items():
            filename = old_path.split("/")[-1]
            new_path = f"{new_location}/{filename}"

            # Copy to new location
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": new_path, "content": content}
            )

        # Verify all files in new location
        result = await obsidian_client.call_tool(
            name="obsidian_list_files_in_dir",
            arguments={"dirpath": new_location}
        )

        assert "doc1.md" in result.data["files"]
        assert "doc2.md" in result.data["files"]
        assert "doc3.md" in result.data["files"]

        # Verify content is intact
        for filename, expected_content in [("doc1.md", "# Document 1\n"),
                                           ("doc2.md", "# Document 2\n"),
                                           ("doc3.md", "# Document 3\n")]:
            result = await obsidian_client.call_tool(
                name="obsidian_get_file_contents",
                arguments={"filepath": f"{new_location}/{filename}"}
            )
            assert result.data == expected_content


class TestFolderSearch:
    """Tests for folder search functionality."""

    async def test_search_folders_case_insensitive(self, obsidian_client: Client[FastMCPTransport]):
        """Test case-insensitive folder search."""
        # Create test folder structure with actual content files
        test_files = [
            ("test-folders/search-test/Project/note1.md", "# Project Note"),
            ("test-folders/search-test/MyProject/note2.md", "# My Project Note"),
            ("test-folders/search-test/project-2024/note3.md", "# 2024 Project"),
            ("test-folders/search-test/Documents/doc1.md", "# Document"),
        ]

        for filepath, content in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": content}
            )

        try:
            # Search for "project" (case-insensitive) from within test-folders
            result = await obsidian_client.call_tool(
                name="obsidian_search_folders",
                arguments={"folder_name": "project", "root_path": "test-folders"}
            )

            assert result.data is not None
            assert isinstance(result.data, list)

            # Should find folders containing "project" (case-insensitive)
            matching = [f for f in result.data if "project" in f.lower()]
            assert len(matching) >= 3, f"Expected >= 3 folders with 'project', found {len(matching)}: {matching}"

        finally:
            # Cleanup
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": "test-folders/search-test", "confirm": True}
                )
            except Exception:
                pass

    async def test_search_folders_with_root_path(self, obsidian_client: Client[FastMCPTransport]):
        """Test folder search from a specific root path."""
        # Create nested folder structure with actual content
        test_files = [
            ("test-folders/root-search/Archives/archive-2023/file.md", "# 2023"),
            ("test-folders/root-search/Archives/archive-2024/file.md", "# 2024"),
            ("test-folders/root-search/Projects/archive-old/file.md", "# Old"),
        ]

        for filepath, content in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": content}
            )

        try:
            # Search for "archive" only in Archives folder
            result = await obsidian_client.call_tool(
                name="obsidian_search_folders",
                arguments={"folder_name": "archive", "root_path": "test-folders/root-search/Archives"}
            )

            assert result.data is not None
            assert isinstance(result.data, list)

            # Should only find archives under Archives folder
            for folder_path in result.data:
                if "archive" in folder_path.lower():
                    assert "Archives" in folder_path

        finally:
            # Cleanup
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": "test-folders/root-search", "confirm": True}
                )
            except Exception:
                pass

    async def test_search_folders_substring_match(self, obsidian_client: Client[FastMCPTransport]):
        """Test that folder search matches substrings."""
        # Create folders with year in name and actual content
        test_files = [
            ("test-folders/year-search/Notes-2024/note.md", "# 2024 Notes"),
            ("test-folders/year-search/Archive-2024-Q1/archive.md", "# Q1 Archive"),
            ("test-folders/year-search/Projects-2023/project.md", "# 2023 Projects"),
        ]

        for filepath, content in test_files:
            await obsidian_client.call_tool(
                name="obsidian_put_content",
                arguments={"filepath": filepath, "content": content}
            )

        try:
            # Search for "2024" substring from within test-folders/year-search
            result = await obsidian_client.call_tool(
                name="obsidian_search_folders",
                arguments={"folder_name": "2024", "root_path": "test-folders/year-search"}
            )

            assert result.data is not None
            assert isinstance(result.data, list)

            # Should find folders containing "2024"
            matching = [f for f in result.data if "2024" in f]
            assert len(matching) >= 2, f"Expected >= 2 folders with '2024', found {len(matching)}: {matching}"

        finally:
            # Cleanup
            try:
                await obsidian_client.call_tool(
                    name="obsidian_delete_file",
                    arguments={"filepath": "test-folders/year-search", "confirm": True}
                )
            except Exception:
                pass


class TestCleanup:
    """Cleanup tests - run last to remove test folders."""

    async def test_cleanup_test_folders(self, obsidian_client: Client[FastMCPTransport]):
        """Delete all test folders created during testing."""
        # Delete the entire test-folders directory
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": "test-folders", "confirm": True}
            )
            print("✓ Cleaned up test-folders directory")
        except Exception as e:
            # If folder doesn't exist or can't be deleted, that's ok
            if "404" not in str(e):
                print(f"⚠ Could not delete test-folders: {e}")

        # Verify cleanup
        try:
            await obsidian_client.call_tool(
                name="obsidian_list_files_in_dir",
                arguments={"dirpath": "test-folders"}
            )
            print("⚠ test-folders still exists")
        except Exception:
            # Expected - folder should not exist
            print("✓ test-folders successfully removed")
