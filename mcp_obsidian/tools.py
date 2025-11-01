
__all__ = ["mcp"]

import os
from typing import Any, Annotated, List, Dict
from . import obsidian
from fastmcp import FastMCP
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("OBSIDIAN_API_KEY", "")
obsidian_host = os.getenv("OBSIDIAN_HOST", "127.0.0.1")
obsidian_protocol = os.getenv("OBSIDIAN_PROTOCOL", "https")
obsidian_port = int(os.getenv("OBSIDIAN_PORT", "27124"))

mcp = FastMCP(name="ObsidianServer",
              instructions="""
                Use these tools to interact with your Obsidian vault.
                The vault is the root directory of your Obsidian notes.
            """)

if api_key == "":
    raise ValueError(f"OBSIDIAN_API_KEY environment variable required. Working directory: {os.getcwd()}")

def _get_client() -> obsidian.Obsidian:
    """Get configured Obsidian API client.

    Returns:
        Configured Obsidian client instance
    """
    return obsidian.Obsidian(
        api_key=api_key,
        protocol=obsidian_protocol,
        host=obsidian_host,
        port=obsidian_port
    )

TOOL_LIST_FILES_IN_VAULT = "obsidian_list_files_in_vault"
TOOL_LIST_FILES_IN_DIR = "obsidian_list_files_in_dir"

@mcp.tool(
    name=TOOL_LIST_FILES_IN_VAULT,
    description="Lists all files and directories in the root directory of your Obsidian vault. Returns a structured object with separate lists for files and directories.",
)
def obsidian_list_files_in_vault() -> Annotated[Dict[str, List[str]], Field(description="Object with 'files' and 'directories' arrays")]:
    api = _get_client()
    raw_list = api.list_files_in_vault()

    # Separate files and directories
    files = [item for item in raw_list if not item.endswith('/')]
    directories = [item.rstrip('/') for item in raw_list if item.endswith('/')]

    return {
        "files": files,
        "directories": directories
    }

@mcp.tool(
    name=TOOL_LIST_FILES_IN_DIR,
    description="Lists all files and directories that exist in a specific Obsidian directory. Returns a structured object with separate lists for files and directories.",
)
def obsidian_list_files_in_dir(
    dirpath: Annotated[str, Field(description="Directory path relative to the vault root (trailing slashes are automatically handled)")]
) -> Annotated[Dict[str, List[str]], Field(description="Object with 'files' and 'directories' arrays")]:
    api = _get_client()
    raw_list = api.list_files_in_dir(dirpath)

    # Separate files and directories
    files = [item for item in raw_list if not item.endswith('/')]
    directories = [item.rstrip('/') for item in raw_list if item.endswith('/')]

    return {
        "files": files,
        "directories": directories
    }

@mcp.tool(
    name="obsidian_get_file_contents",
    description="Return the content of a single file in your vault.",
)
def obsidian_get_file_contents(
    filepath: Annotated[str, Field(description="File path relative to the vault root")]
) -> Annotated[str, Field(description="The content of the file")]:
    api = _get_client()
    return api.get_file_contents(filepath)

@mcp.tool(
    name="obsidian_simple_search",
    description="""Simple search for documents matching a specified text query across all files in the vault.

    Returns a list of search results, each containing:
    - filename: The file path
    - score: Relevance score (negative values, closer to 0 is more relevant)
    - matches: Array of match objects with context and match_position (start/end)

    Use this tool when you want to do a simple text search.""",
)
def obsidian_simple_search(
    query: Annotated[str, Field(description="The search query")],
    context_length: Annotated[int, Field(description="Length of the context to return around each match")] = 100
) -> Annotated[List[Dict[str, Any]], Field(description="List of search results with filename, score, and matches")]:
    api = _get_client()
    results = api.search(query, context_length)
    formatted_results = []
    for result in results:
        formatted_matches = []
        for match in result.get('matches', []):
            context = match.get('context', '')
            match_pos = match.get('match', {})
            start = match_pos.get('start', 0)
            end = match_pos.get('end', 0)
            formatted_matches.append({
                'context': context,
                'match_position': {'start': start, 'end': end}
            })
        formatted_results.append({
            'filename': result.get('filename', ''),
            'score': result.get('score', 0),
            'matches': formatted_matches
        })
    return formatted_results

@mcp.tool(
    name="obsidian_append_content",
    description="Append content to the end of an existing file, or create a new file if it doesn't exist. Automatically creates parent directories if needed.",
)
def obsidian_append_content(
    filepath: Annotated[str, Field(description="File path relative to the vault root")],
    content: Annotated[str, Field(description="The content to append")]
) -> Annotated[None, Field(description="The content was successfully appended")]:
    api = _get_client()
    api.append_content(filepath, content)

@mcp.tool(
    name="obsidian_patch_content",
    description="""Insert content into an existing note relative to a heading, block reference, or frontmatter field.

    Valid operations: 'append', 'prepend', 'replace'
    Valid target_types: 'heading', 'block', 'frontmatter'

    Example: To append content after a heading named "Tasks", use operation='append', target_type='heading', target='Tasks'.""",
)
def obsidian_patch_content(
    filepath: Annotated[str, Field(description="File path relative to the vault root")],
    operation: Annotated[str, Field(description="The patch operation: 'append', 'prepend', or 'replace'")],
    target_type: Annotated[str, Field(description="The target type: 'heading', 'block', or 'frontmatter'")],
    target: Annotated[str, Field(description="The target identifier (e.g., heading text, block ID, or frontmatter key)")],
    content: Annotated[str, Field(description="The content to insert")]
) -> Annotated[None, Field(description="The content was successfully patched")]:
    api = _get_client()
    api.patch_content(filepath, operation, target_type, target, content)

@mcp.tool(
    name="obsidian_put_content",
    description="Create a new file or update an existing file in your vault. Automatically creates parent directories if they don't exist.",
)
def obsidian_put_content(
    filepath: Annotated[str, Field(description="File path relative to the vault root")],
    content: Annotated[str, Field(description="The content to write")]
) -> Annotated[None, Field(description="The content was successfully written")]:
    api = _get_client()
    api.put_content(filepath, content)

@mcp.tool(
    name="obsidian_delete_file",
    description="Delete a file or directory from the vault.",
)
def obsidian_delete_file(
    filepath: Annotated[str, Field(description="Path to the file to delete (relative to vault root)")],
    confirm: Annotated[bool, Field(description="Must be set to true to delete a file")] = False
) -> Annotated[None, Field(description="The file was successfully deleted")]:
    if not confirm:
        raise RuntimeError("confirm must be set to true to delete a file")
    api = _get_client()
    api.delete_file(filepath)

@mcp.tool(
    name="obsidian_complex_search",
    description="""Complex search for documents using a JsonLogic query.
           Supports standard JsonLogic operators plus 'glob' and 'regexp' for pattern matching. Results must be non-falsy.

           Use this tool when you want to do a complex search, e.g. for all documents with certain tags etc.
           ALWAYS follow query syntax in examples.

           Examples
             1. Match all markdown files
             {"glob": ["*.md", {"var": "path"}]}

             2. Match all markdown files with 1221 substring inside them
             {
               "and": [
                 { "glob": ["*.md", {"var": "path"}] },
                 { "regexp": [".*1221.*", {"var": "content"}] }
               ]
             }

             3. Match all markdown files in Work folder containing name Keaton
             {
               "and": [
                 { "glob": ["*.md", {"var": "path"}] },
                 { "regexp": [".*Work.*", {"var": "path"}] },
                 { "regexp": ["Keaton", {"var": "content"}] }
               ]
             }
           """,
)
def obsidian_complex_search(
    query: Annotated[dict, Field(description="The JsonLogic query to execute")]
) -> Annotated[
    List[Dict[str, Any]], Field(description="A list of files matching the search query with path and metadata")
]:
    api = _get_client()
    raw_results = api.search_json(query)

    # Transform results to ensure they're proper dictionaries
    # The API may return objects that need conversion
    results = []
    for item in raw_results:
        if isinstance(item, dict):
            results.append(item)
        elif hasattr(item, '__dict__'):
            # Convert object to dict
            results.append(vars(item))
        elif hasattr(item, 'model_dump'):
            # Pydantic model
            results.append(item.model_dump())
        else:
            # Fallback: convert to string representation
            results.append({"path": str(item)})

    return results

@mcp.tool(
    name="obsidian_batch_get_file_contents",
    description="Return the contents of multiple files in your vault as a structured array. Each element contains the file path, content, and success status.",
)
def obsidian_batch_get_file_contents(
    filepaths: Annotated[list[str], Field(description="List of file paths to read")]
) -> Annotated[
    List[Dict[str, Any]],
    Field(description="Array of objects with 'path', 'content', and 'success' fields")
]:
    api = _get_client()
    results = []

    for filepath in filepaths:
        try:
            content = api.get_file_contents(filepath)
            results.append({
                "path": filepath,
                "content": content,
                "success": True
            })
        except Exception as e:
            results.append({
                "path": filepath,
                "error": str(e),
                "success": False
            })

    return results

@mcp.tool(
    name="obsidian_get_periodic_note",
    description="Get current periodic note for the specified period. REQUIRES the Periodic Notes plugin with the requested period type enabled in Obsidian.",
)
def obsidian_get_periodic_note(
    period: Annotated[str, Field(description="The period type (daily, weekly, monthly, quarterly, yearly)")],
    type: Annotated[str, Field(description="Type of the data to get ('content' or 'metadata')")] = "content"
) -> Annotated[
    Any, Field(description="The content or metadata of the periodic note")
]:
    valid_periods = ["daily", "weekly", "monthly", "quarterly", "yearly"]
    if period not in valid_periods:
        raise RuntimeError(f"Invalid period: {period}. Must be one of: {', '.join(valid_periods)}")
    valid_types = ["content", "metadata"]
    if type not in valid_types:
        raise RuntimeError(f"Invalid type: {type}. Must be one of: {', '.join(valid_types)}")

    api = _get_client()
    return api.get_periodic_note(period, type)

@mcp.tool(
    name="obsidian_get_recent_periodic_notes",
    description="Get most recent periodic notes for the specified period type. REQUIRES the Periodic Notes plugin with the requested period type enabled in Obsidian.",
)
def obsidian_get_recent_periodic_notes(
    period: Annotated[str, Field(description="The period type (daily, weekly, monthly, quarterly, yearly)")],
    limit: Annotated[int, Field(description="Maximum number of notes to return")] = 5,
    include_content: Annotated[bool, Field(description="Whether to include note content")] = False
) -> Annotated[
    List[Dict[str, Any]],
    Field(description="A list of recent periodic notes, with or without content"),
]:
    valid_periods = ["daily", "weekly", "monthly", "quarterly", "yearly"]
    if period not in valid_periods:
        raise RuntimeError(f"Invalid period: {period}. Must be one of: {', '.join(valid_periods)}")
    if not isinstance(limit, int) or limit < 1:
        raise RuntimeError(f"Invalid limit: {limit}. Must be a positive integer")
    if not isinstance(include_content, bool):
        raise RuntimeError(f"Invalid include_content: {include_content}. Must be a boolean")

    api = _get_client()
    return api.get_recent_periodic_notes(period, limit, include_content)

@mcp.tool(
    name="obsidian_get_recent_changes",
    description="Get recently modified files in the vault. REQUIRES the Dataview plugin to be installed and enabled in Obsidian.",
)
def obsidian_get_recent_changes(
    limit: Annotated[int, Field(description="Maximum number of files to return")] = 10,
    days: Annotated[int, Field(description="Only include files modified within this many days")] = 90
) -> Annotated[
    List[Dict[str, Any]],
    Field(description="A list of recently modified files, with their modification times"),
]:
    if not isinstance(limit, int) or limit < 1:
        raise RuntimeError(f"Invalid limit: {limit}. Must be a positive integer")
    if not isinstance(days, int) or days < 1:
        raise RuntimeError(f"Invalid days: {days}. Must be a positive integer")

    api = _get_client()
    return api.get_recent_changes(limit, days)

# ==============================================================================
# MCP Resources (Read-Only Metadata Access)
# ==============================================================================

@mcp.resource("obsidian://vault/{filepath}/metadata")
def get_file_metadata_resource(filepath: Annotated[str, Field(description="File path relative to vault root")]) -> Annotated[
    Dict[str, Any],
    Field(description="Complete file metadata including content, frontmatter, tags, and stats")
]:
    """Get complete metadata for a file: content, frontmatter, tags, and file statistics.

    This resource provides read-only access to all metadata associated with a file,
    including YAML frontmatter, extracted tags, and filesystem statistics.
    """
    api = _get_client()
    return api.get_file_metadata(filepath)

@mcp.resource("obsidian://vault/{filepath}/frontmatter")
def get_file_frontmatter(filepath: Annotated[str, Field(description="File path relative to vault root")]) -> Annotated[
    Dict[str, Any],
    Field(description="YAML frontmatter fields as a dictionary")
]:
    """Get only the YAML frontmatter from a file.

    Returns an empty dictionary if the file has no frontmatter.
    """
    api = _get_client()
    metadata = api.get_file_metadata(filepath)
    return metadata.get('frontmatter', {})

@mcp.resource("obsidian://vault/{filepath}/tags")
def get_file_tags(filepath: Annotated[str, Field(description="File path relative to vault root")]) -> Annotated[
    List[str],
    Field(description="Array of tags found in the file")
]:
    """Get all tags from a file.

    Returns an empty array if the file has no tags.
    """
    api = _get_client()
    metadata = api.get_file_metadata(filepath)
    return metadata.get('tags', [])

@mcp.resource("obsidian://vault/{filepath}/stats")
def get_file_stats(filepath: Annotated[str, Field(description="File path relative to vault root")]) -> Annotated[
    Dict[str, Any],
    Field(description="File statistics with ctime, mtime, and size")
]:
    """Get file statistics (creation time, modification time, size).

    Returns:
        Dictionary with:
        - ctime: Creation time (timestamp)
        - mtime: Modification time (timestamp)
        - size: File size in bytes
    """
    api = _get_client()
    metadata = api.get_file_metadata(filepath)
    return metadata.get('stat', {})

# ==============================================================================
# Search Tools (Tag and Frontmatter Queries)
# ==============================================================================

@mcp.tool(
    name="obsidian_search_by_tags",
    description="""Search for files containing specified tags.

    Use this tool to find all files that have specific tags. Supports both AND and OR logic:
    - AND logic (match_all=True): Files must have ALL specified tags
    - OR logic (match_all=False): Files with ANY of the specified tags will match

    Tags should be provided without the # prefix.""",
)
def obsidian_search_by_tags(
    tags: Annotated[List[str], Field(description="List of tags to search for (without # prefix)")],
    match_all: Annotated[bool, Field(description="If True, files must have ALL tags (AND). If False, files with ANY tag match (OR).")] = False
) -> Annotated[
    List[Dict[str, Any]],
    Field(description="List of files matching the tag criteria")
]:
    api = _get_client()
    return api.search_by_tags(tags, match_all)

@mcp.tool(
    name="obsidian_search_by_frontmatter",
    description="""Search files by frontmatter field values.

    This tool allows you to search for files based on their YAML frontmatter fields.

    Operators:
    - "equals": Find files where field exactly matches the value
    - "contains": Find files where field contains the value (works for strings and arrays)
    - "exists": Find files that have the specified field (value parameter not needed)

    Example uses:
    - Find files with status="done": field="status", value="done", operator="equals"
    - Find files with any status field: field="status", operator="exists"
    - Find files tagged with "project": field="tags", value="project", operator="contains"
    """,
)
def obsidian_search_by_frontmatter(
    field: Annotated[str, Field(description="Frontmatter field name to search")],
    value: Annotated[Any, Field(description="Value to match (optional if operator is 'exists')")] = None,
    operator: Annotated[str, Field(description="Comparison operator: 'equals', 'contains', or 'exists'")] = "equals"
) -> Annotated[
    List[Dict[str, Any]],
    Field(description="List of files where frontmatter matches the criteria")
]:
    api = _get_client()
    return api.search_by_frontmatter(field, value, operator)

@mcp.tool(
    name="obsidian_list_all_tags",
    description="""Get all unique tags in the vault with usage counts.

    Returns a dictionary mapping each tag to the number of files using it.
    This is useful for getting an overview of all tags in your vault and
    understanding tag popularity.

    Note: This operation scans all markdown files in the vault and may take
    some time for large vaults.""",
)
def obsidian_list_all_tags() -> Annotated[
    Dict[str, int],
    Field(description="Dictionary mapping tag names to the number of files using them")
]:
    api = _get_client()
    return api.list_all_tags()