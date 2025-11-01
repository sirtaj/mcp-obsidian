"""Tests for the obsidian_list_headings tool."""

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport


@pytest.mark.asyncio
async def test_list_headings_flat_structure(
    obsidian_client: Client[FastMCPTransport]
):
    """Test listing headings in a file with only top-level headings."""
    filepath = "test_headings_flat.md"
    content = """# First Heading
Some content

# Second Heading
More content

# Third Heading
Final content
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": content},
        )

        result = await obsidian_client.call_tool(
            name="obsidian_list_headings",
            arguments={"filepath": filepath},
        )

        headings = result.structured_content["result"]
        assert len(headings) == 3

        # First heading
        assert headings[0]["level"] == 1
        assert headings[0]["text"] == "First Heading"
        assert headings[0]["path"] == "First Heading"
        assert headings[0]["line"] == 1

        # Second heading
        assert headings[1]["level"] == 1
        assert headings[1]["text"] == "Second Heading"
        assert headings[1]["path"] == "Second Heading"
        assert headings[1]["line"] == 4

        # Third heading
        assert headings[2]["level"] == 1
        assert headings[2]["text"] == "Third Heading"
        assert headings[2]["path"] == "Third Heading"
        assert headings[2]["line"] == 7

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_list_headings_nested_structure(
    obsidian_client: Client[FastMCPTransport]
):
    """Test listing headings in a file with nested hierarchy."""
    filepath = "test_headings_nested.md"
    content = """# Main Document
Introduction text
## First Section
Content for first section
### Subsection A
Details about A
### Subsection B
Details about B
## Second Section
Content for second section
### Subsection C
Details about C
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": content},
        )

        result = await obsidian_client.call_tool(
            name="obsidian_list_headings",
            arguments={"filepath": filepath},
        )

        headings = result.structured_content["result"]
        assert len(headings) == 6

        # Main Document
        assert headings[0]["level"] == 1
        assert headings[0]["text"] == "Main Document"
        assert headings[0]["path"] == "Main Document"

        # First Section
        assert headings[1]["level"] == 2
        assert headings[1]["text"] == "First Section"
        assert headings[1]["path"] == "Main Document::First Section"

        # Subsection A
        assert headings[2]["level"] == 3
        assert headings[2]["text"] == "Subsection A"
        assert headings[2]["path"] == "Main Document::First Section::Subsection A"

        # Subsection B
        assert headings[3]["level"] == 3
        assert headings[3]["text"] == "Subsection B"
        assert headings[3]["path"] == "Main Document::First Section::Subsection B"

        # Second Section
        assert headings[4]["level"] == 2
        assert headings[4]["text"] == "Second Section"
        assert headings[4]["path"] == "Main Document::Second Section"

        # Subsection C
        assert headings[5]["level"] == 3
        assert headings[5]["text"] == "Subsection C"
        assert headings[5]["path"] == "Main Document::Second Section::Subsection C"

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_list_headings_custom_delimiter(
    obsidian_client: Client[FastMCPTransport]
):
    """Test listing headings with a custom delimiter."""
    filepath = "test_headings_custom_delim.md"
    content = """# Parent
## Child with :: in name
### Grandchild
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": content},
        )

        result = await obsidian_client.call_tool(
            name="obsidian_list_headings",
            arguments={"filepath": filepath, "delimiter": ">>"},
        )

        headings = result.structured_content["result"]
        assert len(headings) == 3

        assert headings[0]["path"] == "Parent"
        assert headings[1]["path"] == "Parent>>Child with :: in name"
        assert headings[2]["path"] == "Parent>>Child with :: in name>>Grandchild"

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_list_headings_mixed_levels(
    obsidian_client: Client[FastMCPTransport]
):
    """Test that heading hierarchy is correctly maintained with level jumps."""
    filepath = "test_headings_mixed.md"
    content = """# Level 1
## Level 2
#### Level 4 (skipped level 3)
### Level 3 (back to level 3)
# Another Level 1
### Level 3 (jumped from level 1)
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": content},
        )

        result = await obsidian_client.call_tool(
            name="obsidian_list_headings",
            arguments={"filepath": filepath},
        )

        headings = result.structured_content["result"]
        assert len(headings) == 6

        # First level 1
        assert headings[0]["path"] == "Level 1"

        # Level 2 under Level 1
        assert headings[1]["path"] == "Level 1::Level 2"

        # Level 4 under Level 2 (skipped level 3)
        assert (
            headings[2]["path"]
            == "Level 1::Level 2::Level 4 (skipped level 3)"
        )

        # Level 3 under Level 2 (hierarchy adjusted)
        assert headings[3]["path"] == "Level 1::Level 2::Level 3 (back to level 3)"

        # New top-level heading resets hierarchy
        assert headings[4]["path"] == "Another Level 1"

        # Level 3 under new Level 1 (skipped level 2)
        assert headings[5]["path"] == "Another Level 1::Level 3 (jumped from level 1)"

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_list_headings_empty_file(obsidian_client: Client[FastMCPTransport]):
    """Test listing headings in a file with no headings."""
    filepath = "test_headings_empty.md"
    content = """Just some text without any headings.

More text here.
Even more text.
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": content},
        )

        result = await obsidian_client.call_tool(
            name="obsidian_list_headings",
            arguments={"filepath": filepath},
        )

        headings = result.structured_content["result"]
        assert len(headings) == 0

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_list_headings_with_whitespace(
    obsidian_client: Client[FastMCPTransport]
):
    """Test that headings with leading/trailing whitespace are handled correctly."""
    filepath = "test_headings_whitespace.md"
    content = """#    Heading with extra spaces
##   Nested heading
"""

    try:
        await obsidian_client.call_tool(
            name="obsidian_put_content",
            arguments={"filepath": filepath, "content": content},
        )

        result = await obsidian_client.call_tool(
            name="obsidian_list_headings",
            arguments={"filepath": filepath},
        )

        headings = result.structured_content["result"]
        assert len(headings) == 2

        # Heading text should have whitespace trimmed after the # markers
        assert headings[0]["text"] == "Heading with extra spaces"
        assert headings[0]["path"] == "Heading with extra spaces"

        assert headings[1]["text"] == "Nested heading"
        assert headings[1]["path"] == "Heading with extra spaces::Nested heading"

    finally:
        try:
            await obsidian_client.call_tool(
                name="obsidian_delete_file",
                arguments={"filepath": filepath, "confirm": True},
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_list_headings_nonexistent_file(
    obsidian_client: Client[FastMCPTransport]
):
    """Test that listing headings on a nonexistent file raises an error."""
    with pytest.raises(Exception) as exc_info:
        await obsidian_client.call_tool(
            name="obsidian_list_headings",
            arguments={"filepath": "nonexistent_headings.md"},
        )

    assert "does not exist" in str(exc_info.value).lower() or "not found" in str(
        exc_info.value
    ).lower()
