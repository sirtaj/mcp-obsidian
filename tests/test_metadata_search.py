"""
Tests for metadata resources and search tools.

This test suite covers:
- Metadata resources (4 resources)
- Tag search tool
- Frontmatter search tool
- List all tags tool
"""

import json
import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport


def parse_resource_data(result):
    """Helper to parse resource data from FastMCP resource response."""
    # read_resource returns a list of ResourceContents directly
    if isinstance(result, list) and len(result) > 0:
        content_data = result[0]
        if hasattr(content_data, 'text'):
            return json.loads(content_data.text)
        elif hasattr(content_data, 'blob'):
            return json.loads(content_data.blob)
    # Fallback for other formats
    if hasattr(result, 'contents') and result.contents and len(result.contents) > 0:
        content_data = result.contents[0]
        if hasattr(content_data, 'text'):
            return json.loads(content_data.text)
        elif hasattr(content_data, 'blob'):
            return json.loads(content_data.blob)
    if hasattr(result, 'data'):
        return result.data
    return result


# ==============================================================================
# Metadata Resources Tests
# ==============================================================================

class TestMetadataResources:
    """Tests for metadata resource access."""

    async def test_get_file_metadata_resource(self, obsidian_client: Client[FastMCPTransport], vault_files: list[str]):
        """Test getting complete file metadata via resource."""
        md_files = [f for f in vault_files if f.endswith('.md')]

        if not md_files:
            pytest.skip("No markdown files found")

        test_file = md_files[0]

        # Access the resource
        result = await obsidian_client.read_resource(
            uri=f"obsidian://vault/{test_file}/metadata"
        )

        # Parse resource data
        metadata = parse_resource_data(result)
        assert isinstance(metadata, dict)

        # Verify NoteJson structure
        assert 'content' in metadata
        assert 'frontmatter' in metadata
        assert 'tags' in metadata
        assert 'stat' in metadata
        assert 'path' in metadata

        # Verify stat structure
        stat = metadata['stat']
        assert 'ctime' in stat
        assert 'mtime' in stat
        assert 'size' in stat

    async def test_get_file_content_resource(self, obsidian_client: Client[FastMCPTransport], vault_files: list[str]):
        """Test getting only file content via resource."""
        md_files = [f for f in vault_files if f.endswith('.md')]

        if not md_files:
            pytest.skip("No markdown files found")

        test_file = md_files[0]

        # Access the resource
        result = await obsidian_client.read_resource(
            uri=f"obsidian://vault/{test_file}/content"
        )

        # Content resource returns plain text directly (not JSON)
        assert isinstance(result, list) and len(result) > 0
        content_data = result[0]
        assert hasattr(content_data, 'text')
        content = content_data.text

        assert content is not None
        assert isinstance(content, str)
        # Content should be non-empty for markdown files
        assert len(content) > 0

    async def test_metadata_resource_nonexistent_file(self, obsidian_client: Client[FastMCPTransport]):
        """Test that accessing metadata for non-existent file raises error."""
        with pytest.raises(Exception) as exc_info:
            await obsidian_client.read_resource(
                uri="obsidian://vault/nonexistent-file-12345.md/metadata"
            )
        assert "404" in str(exc_info.value) or "Not Found" in str(exc_info.value)


# ==============================================================================
# Search Tools Tests
# ==============================================================================

class TestSearchByTags:
    """Tests for tag-based search functionality."""

    async def test_search_by_tags_single_tag_or(self, obsidian_client: Client[FastMCPTransport]):
        """Test searching for files with a single tag (OR logic)."""
        result = await obsidian_client.call_tool(
            name="obsidian_search_by_tags",
            arguments={"tags": ["test"], "match_all": False}
        )

        # Result should be a list (may be empty if no files have the tag)
        assert result.data is not None
        assert isinstance(result.data, list)

    async def test_search_by_tags_multiple_tags_or(self, obsidian_client: Client[FastMCPTransport]):
        """Test searching for files with any of multiple tags (OR logic)."""
        result = await obsidian_client.call_tool(
            name="obsidian_search_by_tags",
            arguments={"tags": ["test", "project", "important"], "match_all": False}
        )

        assert result.data is not None
        assert isinstance(result.data, list)

    async def test_search_by_tags_multiple_tags_and(self, obsidian_client: Client[FastMCPTransport]):
        """Test searching for files with all of multiple tags (AND logic)."""
        result = await obsidian_client.call_tool(
            name="obsidian_search_by_tags",
            arguments={"tags": ["test", "project"], "match_all": True}
        )

        assert result.data is not None
        assert isinstance(result.data, list)

    async def test_search_by_tags_integration(self, obsidian_client: Client[FastMCPTransport]):
        """Integration test: create file with tags, search for it, delete it."""
        test_file = "test-tag-search.md"
        test_content = """---
tags: [test-search, integration-test]
---

# Test File for Tag Search

This file is created to test tag search functionality.
"""

        # Create file with tags
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": test_file, "content": test_content}
        )

        try:
            # Search for file by tag (OR logic)
            result = await obsidian_client.call_tool(
                name="obsidian_search_by_tags",
                arguments={"tags": ["test-search"], "match_all": False}
            )

            # Should find the file
            assert isinstance(result.data, list)
            assert len(result.data) > 0

            # Search for file by multiple tags (AND logic)
            result_and = await obsidian_client.call_tool(
                name="obsidian_search_by_tags",
                arguments={"tags": ["test-search", "integration-test"], "match_all": True}
            )

            # Should find the file
            assert isinstance(result_and.data, list)
            assert len(result_and.data) > 0

        finally:
            # Clean up
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": test_file, "confirm": True}
            )


class TestSearchByFrontmatter:
    """Tests for frontmatter-based search functionality."""

    async def test_search_by_frontmatter_exists(self, obsidian_client: Client[FastMCPTransport]):
        """Test searching for files that have a specific frontmatter field."""
        result = await obsidian_client.call_tool(
            name="obsidian_search_by_frontmatter",
            arguments={"field": "title", "operator": "exists"}
        )

        assert result.data is not None
        assert isinstance(result.data, list)

    async def test_search_by_frontmatter_equals(self, obsidian_client: Client[FastMCPTransport]):
        """Test searching for files where frontmatter field equals a value."""
        test_file = "test-frontmatter-search.md"
        test_content = """---
status: done
priority: high
---

# Test File for Frontmatter Search
"""

        # Create file with frontmatter
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": test_file, "content": test_content}
        )

        try:
            # Search for file by frontmatter
            result = await obsidian_client.call_tool(
                name="obsidian_search_by_frontmatter",
                arguments={"field": "status", "value": "done", "operator": "equals"}
            )

            # Should find the file
            assert isinstance(result.data, list)
            assert len(result.data) > 0

        finally:
            # Clean up
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": test_file, "confirm": True}
            )

    async def test_search_by_frontmatter_contains(self, obsidian_client: Client[FastMCPTransport]):
        """Test searching for files where frontmatter contains a value."""
        test_file = "test-frontmatter-contains.md"
        test_content = """---
tags: [python, testing, automation]
---

# Test File for Contains Search
"""

        # Create file with frontmatter array
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": test_file, "content": test_content}
        )

        try:
            # Search for file where tags contains "testing"
            result = await obsidian_client.call_tool(
                name="obsidian_search_by_frontmatter",
                arguments={"field": "tags", "value": "testing", "operator": "contains"}
            )

            # Should find the file
            assert isinstance(result.data, list)
            assert len(result.data) > 0

        finally:
            # Clean up
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": test_file, "confirm": True}
            )


class TestListAllTags:
    """Tests for list_all_tags tool."""

    async def test_list_all_tags(self, obsidian_client: Client[FastMCPTransport]):
        """Test listing all tags in the vault."""
        result = await obsidian_client.call_tool(
            name="obsidian_list_all_tags",
            arguments={}
        )

        # Check structured_content if data is None (empty dict case)
        tags_data = result.data if result.data is not None else result.structured_content.get('result', {})

        assert tags_data is not None
        assert isinstance(tags_data, dict)

        # If there are tags, validate their structure
        for tag, count in tags_data.items():
            assert isinstance(tag, str)
            assert isinstance(count, int)
            assert count > 0  # Count should be at least 1

    async def test_list_all_tags_integration(self, obsidian_client: Client[FastMCPTransport]):
        """Integration test: create files with tags, list tags, verify counts."""
        test_files = [
            ("test-tags-1.md", "---\ntags: [integration-tag-test]\n---\n# File 1"),
            ("test-tags-2.md", "---\ntags: [integration-tag-test, another-tag]\n---\n# File 2"),
            ("test-tags-3.md", "---\ntags: [another-tag]\n---\n# File 3"),
        ]

        try:
            # Create test files
            for filepath, content in test_files:
                await obsidian_client.call_tool(
                    name="obsidian_put_content",
                    arguments={"filepath": filepath, "content": content}
                )

            # List all tags
            result = await obsidian_client.call_tool(
                name="obsidian_list_all_tags",
                arguments={}
            )

            assert isinstance(result.data, dict)

            # Verify our test tags are present
            if "integration-tag-test" in result.data:
                assert result.data["integration-tag-test"] >= 2
            if "another-tag" in result.data:
                assert result.data["another-tag"] >= 2

        finally:
            # Clean up
            for filepath, _ in test_files:
                try:
                    await obsidian_client.call_tool(
                        name="obsidian_delete_file",
                        arguments={"filepath": filepath, "confirm": True}
                    )
                except Exception:
                    pass  # Ignore cleanup errors


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestMetadataSearchIntegration:
    """End-to-end integration tests combining metadata resources and search."""

    async def test_create_file_search_by_tags_access_metadata(self, obsidian_client: Client[FastMCPTransport]):
        """Complete workflow: create file with tags, search, access metadata via resource."""
        test_file = "integration-metadata-test.md"
        test_content = """---
title: Integration Test
tags: [integration, metadata-test]
status: testing
---

# Integration Test File

This file tests the complete metadata and search workflow.
"""

        # Create file
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": test_file, "content": test_content}
        )

        try:
            # Search by tag
            search_result = await obsidian_client.call_tool(
                name="obsidian_search_by_tags",
                arguments={"tags": ["metadata-test"], "match_all": False}
            )
            assert len(search_result.data) > 0

            # Access metadata via resource
            metadata_result = await obsidian_client.read_resource(
                uri=f"obsidian://vault/{test_file}/metadata"
            )
            metadata = parse_resource_data(metadata_result)
            assert metadata is not None
            assert "integration" in metadata['tags']
            assert "metadata-test" in metadata['tags']
            assert metadata['frontmatter']['title'] == "Integration Test"
            assert metadata['frontmatter']['status'] == "testing"

            # Access tags via resource
            tags_result = await obsidian_client.read_resource(
                uri=f"obsidian://vault/{test_file}/tags"
            )
            tags = parse_resource_data(tags_result)
            assert "integration" in tags
            assert "metadata-test" in tags

            # Search by frontmatter
            frontmatter_result = await obsidian_client.call_tool(
                name="obsidian_search_by_frontmatter",
                arguments={"field": "status", "value": "testing", "operator": "equals"}
            )
            assert len(frontmatter_result.data) > 0

        finally:
            # Clean up
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": test_file, "confirm": True}
            )
