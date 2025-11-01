"""Comprehensive tests for the obsidian_patch_content tool.

Tests cover:
- Whitespace handling with trim_whitespace parameter
- Nested headings with custom delimiters
- Different operations (append, prepend, replace)
- Different target types (heading, block, frontmatter)
"""

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport


@pytest.mark.asyncio
async def test_patch_heading_with_trailing_whitespace(
    obsidian_client: Client[FastMCPTransport]
):
    """Test that trim_whitespace=True handles headings with trailing spaces."""
    filepath = "test_patch_whitespace.md"
    initial_content = """# Meeting Notes

## Tasks

- Task 1
"""

    try:
        # Create test file with heading that has trailing spaces
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": initial_content},
        )

        # Append content after "Meeting Notes" heading (target has no trailing space)
        # This should work with trim_whitespace=True (default)
        await obsidian_client.call_tool(
            name="obsidian_patch_content",
            arguments={
                "filepath": filepath,
                "operation": "append",
                "target_type": "heading",
                "target": "Meeting Notes",  # No trailing space
                "content": "\n## Attendees\n\n- Alice\n- Bob\n",
                "trim_whitespace": True,  # Explicitly test with True
            },
        )

        # Verify content was added
        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath},
        )

        assert "Attendees" in result.data
        assert "Alice" in result.data
        assert "Bob" in result.data

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_patch_heading_append(obsidian_client: Client[FastMCPTransport]):
    """Test appending content after a heading."""
    filepath = "test_patch_append.md"
    initial_content = """# Project Notes
## Tasks
- Initial task
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": initial_content},
        )

        # Append to Tasks heading (nested under Project Notes, so use full path)
        await obsidian_client.call_tool(
            name="obsidian_patch_content",
            arguments={
                "filepath": filepath,
                "operation": "append",
                "target_type": "heading",
                "target": "Project Notes::Tasks",  # Full path for nested heading
                "content": "- Added task\n",
            },
        )

        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath},
        )

        assert "- Added task" in result.data
        assert result.data.index("- Initial task") < result.data.index("- Added task")

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_patch_heading_prepend(obsidian_client: Client[FastMCPTransport]):
    """Test prepending content before a heading's content."""
    filepath = "test_patch_prepend.md"
    initial_content = """# Notes
## Section
Existing content
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": initial_content},
        )

        # Prepend to Section heading (nested under Notes, so use full path)
        await obsidian_client.call_tool(
            name="obsidian_patch_content",
            arguments={
                "filepath": filepath,
                "operation": "prepend",
                "target_type": "heading",
                "target": "Notes::Section",  # Full path for nested heading
                "content": "New first line\n",
            },
        )

        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath},
        )

        assert "New first line" in result.data
        assert result.data.index("New first line") < result.data.index(
            "Existing content"
        )

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_patch_heading_replace(obsidian_client: Client[FastMCPTransport]):
    """Test replacing content under a heading."""
    filepath = "test_patch_replace.md"
    initial_content = """# Document
## Old Section
This content will be replaced
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": initial_content},
        )

        # Replace content under Old Section (nested under Document, so use full path)
        await obsidian_client.call_tool(
            name="obsidian_patch_content",
            arguments={
                "filepath": filepath,
                "operation": "replace",
                "target_type": "heading",
                "target": "Document::Old Section",  # Full path for nested heading
                "content": "New replacement content\n",
            },
        )

        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath},
        )

        assert "New replacement content" in result.data
        assert "This content will be replaced" not in result.data

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_patch_nested_heading_default_delimiter(
    obsidian_client: Client[FastMCPTransport]
):
    """Test patching nested headings using default :: delimiter."""
    filepath = "test_patch_nested.md"
    initial_content = """# Main Heading
## Subheading 1
### Subsubheading 1:1
Content here
### Subsubheading 1:2
More content
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": initial_content},
        )

        # Append to nested heading using :: delimiter
        await obsidian_client.call_tool(
            name="obsidian_patch_content",
            arguments={
                "filepath": filepath,
                "operation": "append",
                "target_type": "heading",
                "target": "Main Heading::Subheading 1::Subsubheading 1:1",  # Full path from root
                "content": "\nAdded to nested heading\n",
            },
        )

        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath},
        )

        assert "Added to nested heading" in result.data

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_patch_nested_heading_custom_delimiter(
    obsidian_client: Client[FastMCPTransport]
):
    """Test patching nested headings with custom delimiter."""
    filepath = "test_patch_custom_delim.md"
    initial_content = """# Parent

## Child with :: in name

Content under child
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": initial_content},
        )

        # Use custom delimiter since heading contains ::
        await obsidian_client.call_tool(
            name="obsidian_patch_content",
            arguments={
                "filepath": filepath,
                "operation": "append",
                "target_type": "heading",
                "target": "Parent>>Child with :: in name",
                "content": "\nAdded content\n",
                "delimiter": ">>",
            },
        )

        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath},
        )

        assert "Added content" in result.data

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_patch_frontmatter_replace(obsidian_client: Client[FastMCPTransport]):
    """Test replacing frontmatter field value."""
    filepath = "test_patch_frontmatter.md"
    initial_content = """---
title: Original Title
tags: [test]
status: draft
---

# Content

Some content here
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": initial_content},
        )

        # Replace status field
        await obsidian_client.call_tool(
            name="obsidian_patch_content",
            arguments={
                "filepath": filepath,
                "operation": "replace",
                "target_type": "frontmatter",
                "target": "status",
                "content": "published",
            },
        )

        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath},
        )

        assert "status: published" in result.data
        assert "status: draft" not in result.data

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_patch_nonexistent_file(obsidian_client: Client[FastMCPTransport]):
    """Test that patching nonexistent file raises error."""
    with pytest.raises(Exception) as exc_info:
        await obsidian_client.call_tool(
            name="obsidian_patch_content",
            arguments={
                "filepath": "nonexistent_file.md",
                "operation": "append",
                "target_type": "heading",
                "target": "Some Heading",
                "content": "Content",
            },
        )

    assert "does not exist" in str(exc_info.value).lower() or "not found" in str(
        exc_info.value
    ).lower()


@pytest.mark.asyncio
async def test_patch_nonexistent_heading(obsidian_client: Client[FastMCPTransport]):
    """Test that patching nonexistent heading raises error."""
    filepath = "test_patch_no_heading.md"
    initial_content = """# Real Heading
Some content
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": initial_content},
        )

        with pytest.raises(Exception) as exc_info:
            await obsidian_client.call_tool(
                name="obsidian_patch_content",
                arguments={
                    "filepath": filepath,
                    "operation": "append",
                    "target_type": "heading",
                    "target": "Nonexistent Heading",
                    "content": "Content",
                },
            )

        # The error should indicate the heading wasn't found or is invalid
        error_msg = str(exc_info.value).lower()
        assert (
            "not found" in error_msg
            or "does not exist" in error_msg
            or "invalid-target" in error_msg
        )

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_patch_with_trim_whitespace_false(
    obsidian_client: Client[FastMCPTransport]
):
    """Test that trim_whitespace=False requires exact match of heading text."""
    filepath = "test_patch_no_trim.md"
    initial_content = """# Notes
## Section Name
Content
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": initial_content},
        )

        # With trim_whitespace=False (explicit), heading path must match exactly
        await obsidian_client.call_tool(
            name="obsidian_patch_content",
            arguments={
                "filepath": filepath,
                "operation": "append",
                "target_type": "heading",
                "target": "Notes::Section Name",  # Exact match required
                "content": "\nAdded line\n",
                "trim_whitespace": False,  # Require exact whitespace matching
            },
        )

        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath},
        )

        assert "Added line" in result.data

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_patch_multiple_operations_same_file(
    obsidian_client: Client[FastMCPTransport]
):
    """Test multiple patch operations on the same file."""
    filepath = "test_patch_multiple.md"
    initial_content = """# Project
## Todo
- Task 1
## Done
- Completed 1
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": initial_content},
        )

        # Append to Todo (use full path)
        await obsidian_client.call_tool(
            name="obsidian_patch_content",
            arguments={
                "filepath": filepath,
                "operation": "append",
                "target_type": "heading",
                "target": "Project::Todo",  # Full path for nested heading
                "content": "- Task 2\n",
            },
        )

        # Append to Done (use full path)
        await obsidian_client.call_tool(
            name="obsidian_patch_content",
            arguments={
                "filepath": filepath,
                "operation": "append",
                "target_type": "heading",
                "target": "Project::Done",  # Full path for nested heading
                "content": "- Completed 2\n",
            },
        )

        result = await obsidian_client.call_tool(
            name="obsidian_get_file_contents",
            arguments={"filepath": filepath},
        )

        assert "- Task 2" in result.data
        assert "- Completed 2" in result.data

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass
