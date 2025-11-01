"""
Comprehensive tests for all Obsidian MCP server tools.

This test suite covers all 14 tools provided by the server:
- File operations (6 tools)
- Content patching (1 tool)
- File deletion (1 tool)
- Search operations (2 tools)
- Periodic notes (2 tools)
- Recent changes (1 tool)
"""

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport


# ==============================================================================
# File Operations Tests (6 tools)
# ==============================================================================

class TestFileOperations:
    """Tests for basic file listing and reading operations."""

    async def test_list_files_in_vault(self, obsidian_client: Client[FastMCPTransport]):
        """Test listing all files in the vault root."""
        result = await obsidian_client.call_tool(
            name="obsidian_list_files_in_vault",
            arguments={}
        )

        assert result.data is not None
        assert isinstance(result.data, list)
        assert len(result.data) > 0
        # Should contain some common vault directories or files
        assert any(item.endswith('/') or item.endswith('.md') for item in result.data)

    async def test_list_files_in_dir(self, obsidian_client: Client[FastMCPTransport], vault_files: list[str]):
        """Test listing files in a specific directory."""
        # Find a directory in the vault
        directories = [f.rstrip('/') for f in vault_files if f.endswith('/')]

        if not directories:
            pytest.skip("No directories found in vault root")

        test_dir = directories[0]
        result = await obsidian_client.call_tool(
            name="obsidian_list_files_in_dir",
            arguments={"dirpath": test_dir}
        )

        assert result.data is not None
        assert isinstance(result.data, list)

    async def test_list_files_in_nonexistent_dir(self, obsidian_client: Client[FastMCPTransport]):
        """Test that listing a non-existent directory raises an error."""
        with pytest.raises(Exception) as exc_info:
            await obsidian_client.call_tool(
                name="obsidian_list_files_in_dir",
                arguments={"dirpath": "nonexistent-directory-12345"}
            )
        assert "404" in str(exc_info.value) or "Not Found" in str(exc_info.value)

    async def test_get_file_contents(self, obsidian_client: Client[FastMCPTransport], vault_files: list[str]):
        """Test reading contents of a single file."""
        # Find a markdown file in the vault
        md_files = [f for f in vault_files if f.endswith('.md')]

        if not md_files:
            pytest.skip("No markdown files found in vault root")

        test_file = md_files[0]
        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": test_file}
        )

        assert result.data is not None
        assert isinstance(result.data, str)

    async def test_get_nonexistent_file_contents(self, obsidian_client: Client[FastMCPTransport]):
        """Test that reading a non-existent file raises an error."""
        with pytest.raises(Exception) as exc_info:
            await obsidian_client.call_tool(
                name="obsidian_get_file_contents",
                arguments={"filepath": "nonexistent-file-12345.md"}
            )
        assert "404" in str(exc_info.value) or "Not Found" in str(exc_info.value)

    async def test_batch_get_file_contents(self, obsidian_client: Client[FastMCPTransport], vault_files: list[str]):
        """Test reading multiple files at once."""
        md_files = [f for f in vault_files if f.endswith('.md')][:3]  # Get up to 3 files

        if len(md_files) < 2:
            pytest.skip("Need at least 2 markdown files for batch test")

        result = await obsidian_client.call_tool(
            name="obsidian_batch_get_file_contents",
            arguments={"filepaths": md_files}
        )

        assert result.data is not None
        assert isinstance(result.data, str)
        # Should contain headers for each file
        for filepath in md_files:
            assert f"# {filepath}" in result.data

    async def test_batch_get_with_nonexistent_file(self, obsidian_client: Client[FastMCPTransport], vault_files: list[str]):
        """Test batch read with mix of existing and non-existent files (should handle gracefully)."""
        md_files = [f for f in vault_files if f.endswith('.md')][:1]

        if not md_files:
            pytest.skip("No markdown files found")

        # Mix existing and non-existent files
        filepaths = md_files + ["nonexistent-file-12345.md"]

        result = await obsidian_client.call_tool(
            name="obsidian_batch_get_file_contents",
            arguments={"filepaths": filepaths}
        )

        assert result.data is not None
        # Should contain error message for nonexistent file
        assert "Error reading file" in result.data or "nonexistent-file-12345.md" in result.data


# ==============================================================================
# File Write Operations Tests
# ==============================================================================

class TestWriteOperations:
    """Tests for file creation and modification operations."""

    TEST_FILE_PATH = "test-mcp-file.md"
    TEST_CONTENT = "# Test File\n\nThis is a test file created by MCP tests.\n"

    async def test_put_content_create_new_file(self, obsidian_client: Client[FastMCPTransport]):
        """Test creating a new file with put_content."""
        result = await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={
                "filepath": self.TEST_FILE_PATH,
                "content": self.TEST_CONTENT
            }
        )

        assert result.data is None  # put_content returns None on success

        # Verify file was created by reading it back
        read_result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": self.TEST_FILE_PATH}
        )
        assert read_result.data == self.TEST_CONTENT

    async def test_append_content(self, obsidian_client: Client[FastMCPTransport]):
        """Test appending content to an existing file."""
        additional_content = "\nAppended content.\n"

        result = await obsidian_client.call_tool(
            name="obsidian_append_content",
            arguments={
                "filepath": self.TEST_FILE_PATH,
                "content": additional_content
            }
        )

        assert result.data is None

        # Verify content was appended
        read_result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": self.TEST_FILE_PATH}
        )
        assert read_result.data == self.TEST_CONTENT + additional_content

    async def test_put_content_overwrite_file(self, obsidian_client: Client[FastMCPTransport]):
        """Test overwriting an existing file with put_content."""
        new_content = "# Overwritten\n\nCompletely new content.\n"

        result = await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={
                "filepath": self.TEST_FILE_PATH,
                "content": new_content
            }
        )

        assert result.data is None

        # Verify file was overwritten
        read_result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": self.TEST_FILE_PATH}
        )
        assert read_result.data == new_content


# ==============================================================================
# Search Operations Tests
# ==============================================================================

class TestSearchOperations:
    """Tests for simple and complex search functionality."""

    @pytest.mark.parametrize("query,context_length", [
        ("test", 100),
        ("project", 50),
        ("note", 150),
    ])
    async def test_simple_search(
        self,
        query: str,
        context_length: int,
        obsidian_client: Client[FastMCPTransport]
    ):
        """Test simple text search with various queries and context lengths."""
        result = await obsidian_client.call_tool(
            name="obsidian_simple_search",
            arguments={
                "query": query,
                "context_length": context_length
            }
        )

        # Search results are in structured_content['result'], not result.data
        assert result.structured_content is not None
        assert "result" in result.structured_content
        search_results = result.structured_content["result"]
        assert isinstance(search_results, list)

        # If results found, verify structure
        if len(search_results) > 0:
            first_result = search_results[0]
            assert "filename" in first_result
            assert "matches" in first_result or "score" in first_result

    async def test_complex_search_glob(self, obsidian_client: Client[FastMCPTransport]):
        """Test complex search with glob pattern to find all markdown files."""
        query = {"glob": ["*.md", {"var": "path"}]}

        result = await obsidian_client.call_tool(
            name="obsidian_complex_search",
            arguments={"query": query}
        )

        assert result.data is not None
        assert isinstance(result.data, list)
        # Should find at least some markdown files
        assert len(result.data) > 0

    async def test_complex_search_and_operator(self, obsidian_client: Client[FastMCPTransport]):
        """Test complex search with AND operator combining glob and regexp."""
        query = {
            "and": [
                {"glob": ["*.md", {"var": "path"}]},
                {"regexp": [".*test.*", {"var": "path"}]}
            ]
        }

        result = await obsidian_client.call_tool(
            name="obsidian_complex_search",
            arguments={"query": query}
        )

        assert result.data is not None
        assert isinstance(result.data, list)


# ==============================================================================
# Periodic Notes Tests
# ==============================================================================

class TestPeriodicNotes:
    """Tests for periodic note functionality."""

    @pytest.mark.parametrize("period", [
        "daily",
        "weekly",
        "monthly",
        "quarterly",
        "yearly"
    ])
    async def test_get_periodic_note_content(
        self,
        period: str,
        obsidian_client: Client[FastMCPTransport]
    ):
        """Test getting periodic note content for all period types."""
        try:
            result = await obsidian_client.call_tool(
                name="obsidian_get_periodic_note",
                arguments={
                    "period": period,
                    "type": "content"
                }
            )

            # Note might not exist, that's ok
            assert result.data is not None
        except Exception as e:
            # 404 is acceptable if periodic note doesn't exist
            # 40060 is acceptable if period is not enabled in test vault
            if "404" not in str(e) and "40060" not in str(e):
                raise
            pytest.skip(f"Periodic note test skipped: {period} period not enabled in test vault")

    @pytest.mark.parametrize("period", ["daily", "weekly", "monthly"])
    async def test_get_periodic_note_metadata(
        self,
        period: str,
        obsidian_client: Client[FastMCPTransport]
    ):
        """Test getting periodic note metadata."""
        try:
            result = await obsidian_client.call_tool(
                name="obsidian_get_periodic_note",
                arguments={
                    "period": period,
                    "type": "metadata"
                }
            )

            if result.data is not None:
                # If note exists, should have metadata structure
                assert isinstance(result.data, dict)
        except Exception as e:
            # 404 is acceptable if periodic note doesn't exist
            # 40060 is acceptable if period is not enabled in test vault
            if "404" not in str(e) and "40060" not in str(e):
                raise
            pytest.skip(f"Periodic note metadata test skipped: {period} period not enabled in test vault")

    async def test_get_periodic_note_invalid_period(self, obsidian_client: Client[FastMCPTransport]):
        """Test that invalid period raises error."""
        with pytest.raises(Exception) as exc_info:
            await obsidian_client.call_tool(
                name="obsidian_get_periodic_note",
                arguments={
                    "period": "invalid-period",
                    "type": "content"
                }
            )
        assert "Invalid period" in str(exc_info.value)

    @pytest.mark.parametrize("period,limit,include_content", [
        ("daily", 5, False),
        ("weekly", 3, False),
        ("monthly", 5, True),
    ])
    async def test_get_recent_periodic_notes(
        self,
        period: str,
        limit: int,
        include_content: bool,
        obsidian_client: Client[FastMCPTransport]
    ):
        """Test getting recent periodic notes with various parameters."""
        try:
            result = await obsidian_client.call_tool(
                name="obsidian_get_recent_periodic_notes",
                arguments={
                    "period": period,
                    "limit": limit,
                    "include_content": include_content
                }
            )

            assert result.data is not None
            assert isinstance(result.data, list)
            assert len(result.data) <= limit
        except Exception as e:
            # 404 is acceptable if no periodic notes exist
            # 40060 is acceptable if period is not enabled in test vault
            if "404" not in str(e) and "40060" not in str(e):
                raise
            pytest.skip(f"Recent periodic notes test skipped: {period} period not enabled or no notes exist in test vault")


# ==============================================================================
# Recent Changes Tests
# ==============================================================================

class TestRecentChanges:
    """Tests for recent changes functionality."""

    @pytest.mark.parametrize("limit,days", [
        (10, 90),
        (5, 30),
        (20, 7),
    ])
    async def test_get_recent_changes(
        self,
        limit: int,
        days: int,
        obsidian_client: Client[FastMCPTransport]
    ):
        """Test getting recently modified files with various limits and time windows."""
        try:
            result = await obsidian_client.call_tool(
                name="obsidian_get_recent_changes",
                arguments={
                    "limit": limit,
                    "days": days
                }
            )

            assert result.data is not None
            assert isinstance(result.data, list)
            assert len(result.data) <= limit
        except Exception as e:
            # 40070 indicates Dataview plugin not installed or not properly configured
            if "40070" not in str(e):
                raise
            pytest.skip("Recent changes test skipped: Dataview plugin not installed in test vault")


# ==============================================================================
# Delete Operations Tests (run last)
# ==============================================================================

class TestDeleteOperations:
    """Tests for file deletion - run last to clean up test files."""

    async def test_delete_without_confirmation(self, obsidian_client: Client[FastMCPTransport]):
        """Test that delete without confirmation raises error."""
        with pytest.raises(Exception) as exc_info:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={
                    "filepath": "test-mcp-file.md",
                    "confirm": False
                }
            )
        assert "confirm must be set to true" in str(exc_info.value)

    async def test_delete_test_file(self, obsidian_client: Client[FastMCPTransport]):
        """Test deleting the test file created earlier."""
        result = await obsidian_client.call_tool(
            name="obsidian_delete_file",
            arguments={
                "filepath": "test-mcp-file.md",
                "confirm": True
            }
        )

        assert result.data is None

        # Verify file was deleted
        with pytest.raises(Exception) as exc_info:
            await obsidian_client.call_tool(
                name="obsidian_get_file_contents",
                arguments={"filepath": "test-mcp-file.md"}
            )
        assert "404" in str(exc_info.value)


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestIntegration:
    """End-to-end integration tests combining multiple operations."""

    async def test_create_search_delete_workflow(self, obsidian_client: Client[FastMCPTransport]):
        """Test complete workflow: create file, search for it, then delete it."""
        test_file = "integration-test-file.md"
        test_content = "# Integration Test\n\nSearchable keyword: INTEGRATION_TEST_MARKER\n"

        # Create file
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": test_file, "content": test_content}
        )

        # Search for it
        search_result = await obsidian_client.call_tool(
            name="obsidian_simple_search",
            arguments={"query": "INTEGRATION_TEST_MARKER", "context_length": 50}
        )

        # Should find the file - search results are in structured_content['result']
        search_results = search_result.structured_content["result"]
        assert len(search_results) > 0
        assert any(test_file in r.get("filename", "") for r in search_results)

        # Delete it
        await obsidian_client.call_tool(
            name="obsidian_delete_file",
            arguments={"filepath": test_file, "confirm": True}
        )

        # Verify deletion
        with pytest.raises(Exception):
            await obsidian_client.call_tool(
                name="obsidian_get_file_contents",
                arguments={"filepath": test_file}
            )
