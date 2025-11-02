__all__ = ["mcp"]

from typing import Any, Annotated, List, Dict
from . import obsidian, omnisearch, constants, config, utils
from fastmcp import FastMCP
from pydantic import Field

# Load configuration
obsidian_config = config.get_obsidian_config()
omnisearch_config = config.get_omnisearch_config(obsidian_config.host)

mcp = FastMCP(
    name="ObsidianServer",
    instructions=f"""
Obsidian Vault Access via Local REST API

TOOLS:
- File Operations: list, read, write, append, batch read, delete, move/rename, bulk move/rename
- Content Analysis: list headings
- Search: simple text search, complex JsonLogic queries, search by tags/frontmatter, folder search{", Omnisearch (fuzzy matching, BM25 scoring)" if omnisearch_config.enabled else ""}
- Content Patching: insert content relative to headings/blocks/frontmatter
- Periodic Notes: access daily/weekly/monthly/quarterly/yearly notes (requires Periodic Notes plugin)
- Recent Changes: track file modifications (requires Dataview plugin)

RESOURCES:
- obsidian://vault/{{filepath}}/metadata - Complete file metadata (content, frontmatter, tags, stats)
- obsidian://vault/{{filepath}}/content - File content only (plain text)

PATH CONVENTIONS:
- All file paths are relative to vault root (e.g., "Notes/meeting.md", not "/full/path/to/vault/Notes/meeting.md")
- Directories end with "/" when listing (strip when using as paths)
- Parent directories are created automatically when writing files

IMPORTANT:
- Delete and move operations require confirm=True parameter
- Use /content resource for text-only access
- Use /metadata resource when you need frontmatter, tags, or stats
- Extract specific fields client-side: metadata['frontmatter'], metadata['tags'], metadata['stat']
            """,
)


def _get_client() -> obsidian.Obsidian:
    """Get configured Obsidian API client.

    Returns:
        Configured Obsidian client instance
    """
    return obsidian.Obsidian(
        api_key=obsidian_config.api_key,
        protocol=obsidian_config.protocol,
        host=obsidian_config.host,
        port=obsidian_config.port,
    )


def _get_omnisearch_client() -> omnisearch.OmnisearchClient:
    """Get configured Omnisearch client.

    Returns:
        Configured Omnisearch client instance
    """
    return omnisearch.OmnisearchClient(
        host=omnisearch_config.host,
        port=omnisearch_config.port,
        protocol=omnisearch_config.protocol,
    )


@mcp.tool(
    description="""Lists all files and directories in the root directory of your Obsidian vault.

    Supports recursive listing with configurable depth. Returns a structured object with separate lists for files and directories.

    Examples:
    - max_depth=0: Only list files in the vault root (no subdirectories scanned)
    - max_depth=1: List vault root + one level of subdirectories
    - max_depth=2: List vault root + two levels deep
    - max_depth=-1: Recursively list entire vault structure (all subdirectories)""",
)
def obsidian_list_files_in_vault(
    max_depth: Annotated[
        int,
        Field(
            description="Controls recursive directory scanning. 0=no recursion (current directory only), 1=one level of subdirectories, 2=two levels deep, -1=unlimited recursion (entire vault). Default: 0"
        ),
    ] = 0,
    folders_only: Annotated[
        bool,
        Field(
            description="If True, only return directories, not files (default: False)"
        ),
    ] = False,
) -> Annotated[
    Dict[str, List[str]],
    Field(description="Object with 'files' and 'directories' arrays"),
]:
    api = _get_client()
    raw_list = api.list_files_in_vault(max_depth=max_depth)
    result = utils.separate_files_and_directories(raw_list)

    if folders_only:
        result["files"] = []

    return result


@mcp.tool(
    description="""Lists all files and directories that exist in a specific Obsidian directory.

    Supports recursive listing with configurable depth. Returns a structured object with separate lists for files and directories.

    Examples:
    - dirpath="Notes", max_depth=0: Only list files directly in Notes/ (no subdirectories scanned)
    - dirpath="Projects", max_depth=1: List Projects/ + one level of subdirectories
    - dirpath="Archive", max_depth=2: List Archive/ + two levels deep
    - dirpath="Work", max_depth=-1: Recursively list entire Work/ folder structure""",
)
def obsidian_list_files_in_dir(
    dirpath: Annotated[
        str,
        Field(
            description="Directory path relative to the vault root (trailing slashes are automatically handled)"
        ),
    ],
    max_depth: Annotated[
        int,
        Field(
            description="Controls recursive directory scanning. 0=no recursion (current directory only), 1=one level of subdirectories, 2=two levels deep, -1=unlimited recursion (entire folder tree). Default: 0"
        ),
    ] = 0,
    folders_only: Annotated[
        bool,
        Field(
            description="If True, only return directories, not files (default: False)"
        ),
    ] = False,
) -> Annotated[
    Dict[str, List[str]],
    Field(description="Object with 'files' and 'directories' arrays"),
]:
    api = _get_client()
    raw_list = api.list_files_in_dir(dirpath, max_depth=max_depth)
    result = utils.separate_files_and_directories(raw_list)

    if folders_only:
        result["files"] = []

    return result


@mcp.tool(
    description="Return the content of a single file in your vault.",
)
def obsidian_get_file_contents(
    filepath: Annotated[str, Field(description="File path relative to the vault root")],
) -> Annotated[str, Field(description="The content of the file")]:
    api = _get_client()
    return api.get_file_contents(filepath)


@mcp.tool(
    description="""Simple text content search across all files in the vault.

    USE THIS TOOL WHEN:
    - Searching for specific words or phrases in note content
    - You need to see context around each match
    - You want a simple, straightforward text search
    - You don't know which files contain the information

    DO NOT USE THIS TOOL WHEN:
    - You need to filter by file path/location → Use obsidian_complex_search
    - You need to search by tags → Use obsidian_search_by_tags
    - You need to search by frontmatter fields → Use obsidian_search_by_frontmatter
    - You want fuzzy/typo-tolerant search → Use obsidian_omnisearch_search (if available)

    Performs case-insensitive text search across all vault files. Returns matches with surrounding context.

    Examples:
    - query="machine learning": Find all mentions of "machine learning"
    - query="TODO", context_length=50: Find TODO items with 50 chars of context
    - query="John Smith": Find all references to a person
    - query="function calculate": Find function definitions or calls

    Returns a list of search results, each containing:
    - filename: The file path
    - score: Relevance score (negative values, closer to 0 is more relevant)
    - matches: Array of match objects with context and match_position (start/end)

    The context_length parameter controls how much text is shown around each match (default: 100 characters).""",
)
def obsidian_simple_search(
    query: Annotated[str, Field(description="The text to search for (case-insensitive)")],
    context_length: Annotated[
        int, Field(description="Number of characters to include around each match for context (default: 100)")
    ] = constants.SEARCH_DEFAULT_CONTEXT_LENGTH,
) -> Annotated[
    List[Dict[str, Any]],
    Field(description="List of search results with filename, score, and matches with context"),
]:
    api = _get_client()
    results = api.search(query, context_length)
    return utils.format_search_results(results)


@mcp.tool(
    description="Append content to the end of an existing file, or create a new file if it doesn't exist. Automatically creates parent directories if needed.",
)
def obsidian_append_content(
    filepath: Annotated[str, Field(description="File path relative to the vault root")],
    content: Annotated[str, Field(description="The content to append")],
) -> Annotated[None, Field(description="The content was successfully appended")]:
    api = _get_client()
    api.append_content(filepath, content)


@mcp.tool(
    description="""List all headings in a markdown file with their full hierarchical paths.

    This tool helps you discover the correct heading paths to use with obsidian_patch_content.

    Returns a list of headings with:
    - level: Heading level (1-6)
    - text: The heading text
    - path: Full hierarchical path for use in patch operations (e.g., "Main::Tasks::Urgent")
    - line: Line number where heading appears

    IMPORTANT: Always use the 'path' value from this tool when calling obsidian_patch_content for nested headings.""",
)
def obsidian_list_headings(
    filepath: Annotated[str, Field(description="File path relative to the vault root")],
    delimiter: Annotated[
        str,
        Field(
            description="Delimiter for building paths (default: '::'). Should match the delimiter you plan to use in patch operations."
        ),
    ] = "::",
) -> Annotated[
    list[dict[str, Any]],
    Field(
        description="List of heading dictionaries with level, text, path, and line number"
    ),
]:
    api = _get_client()
    return api.list_headings(filepath, delimiter)


@mcp.tool(
    description="""Insert content into an existing note relative to a heading, block reference, or frontmatter field.

    ⚠️  IMPORTANT FOR NESTED HEADINGS ⚠️
    For headings at level 2 or deeper (##, ###, etc.), you MUST use the full hierarchical path from the root.
    Use obsidian_list_headings FIRST to discover the correct paths.

    STEP-BY-STEP GUIDE:
    1. Top-level headings (# Heading):
       ✅ Use just the heading text: target="Heading"

    2. Nested headings (##, ###, etc.):
       ✅ Use FULL path with :: delimiter: target="Parent::Child::Grandchild"
       ❌ DO NOT use just the heading text: target="Grandchild" will fail!

    3. Not sure? Call obsidian_list_headings first to see all valid paths.

    EXAMPLES:
    For this file structure:
      # Meeting Notes
      ## Action Items
      ### Urgent

    ❌ WRONG: target="Urgent" (will fail - heading is nested)
    ❌ WRONG: target="Action Items::Urgent" (will fail - missing root)
    ✅ CORRECT: target="Meeting Notes::Action Items::Urgent"

    Valid operations: 'append', 'prepend', 'replace'
    Valid target_types: 'heading', 'block', 'frontmatter'

    The trim_whitespace parameter (default: True) makes matching more forgiving by ignoring leading/trailing spaces.""",
)
def obsidian_patch_content(
    filepath: Annotated[str, Field(description="File path relative to the vault root")],
    operation: Annotated[
        str, Field(description="The patch operation: 'append', 'prepend', or 'replace'")
    ],
    target_type: Annotated[
        str, Field(description="The target type: 'heading', 'block', or 'frontmatter'")
    ],
    target: Annotated[
        str,
        Field(
            description="The target identifier (e.g., heading text, block ID, or frontmatter key)"
        ),
    ],
    content: Annotated[str, Field(description="The content to insert")],
    trim_whitespace: Annotated[
        bool,
        Field(
            description="Trim whitespace from target before matching (default: True for more forgiving matching)"
        ),
    ] = True,
    delimiter: Annotated[
        str,
        Field(
            description="Delimiter for nested headings (default: '::'). Change if headings contain '::' in their text."
        ),
    ] = "::",
) -> Annotated[None, Field(description="The content was successfully patched")]:
    api = _get_client()
    api.patch_content(filepath, operation, target_type, target, content, trim_whitespace, delimiter)


@mcp.tool(
    description="Create a new file or update an existing file in your vault. Automatically creates parent directories if they don't exist.",
)
def obsidian_put_content(
    filepath: Annotated[str, Field(description="File path relative to the vault root")],
    content: Annotated[str, Field(description="The content to write")],
) -> Annotated[None, Field(description="The content was successfully written")]:
    api = _get_client()
    api.put_content(filepath, content)


@mcp.tool(
    description="Delete a file or directory from the vault.",
)
def obsidian_delete_file(
    filepath: Annotated[
        str, Field(description="Path to the file to delete (relative to vault root)")
    ],
    confirm: Annotated[
        bool, Field(description="Must be set to true to delete a file")
    ] = False,
) -> Annotated[None, Field(description="The file was successfully deleted")]:
    if not confirm:
        raise RuntimeError("confirm must be set to true to delete a file")
    api = _get_client()
    api.delete_file(filepath)


@mcp.tool(
    description="""Move or rename a file in the vault by copying content to a new location and deleting the original.

    This operation:
    1. Reads the source file content
    2. Creates the destination file (with parent directories if needed)
    3. Deletes the source file only if steps 1 and 2 succeed

    Note: This does not preserve file metadata like creation dates. For simple renames within the same directory,
    change only the filename portion of the path.""",
)
def obsidian_move_file(
    source_path: Annotated[
        str, Field(description="Current file path (relative to vault root)")
    ],
    destination_path: Annotated[
        str, Field(description="New file path (relative to vault root)")
    ],
    confirm: Annotated[
        bool, Field(description="Must be set to true to perform the move operation")
    ] = False,
) -> Annotated[
    Dict[str, Any],
    Field(description="Result with success status and message"),
]:
    if not confirm:
        raise RuntimeError(
            "confirm must be set to true to move a file (this will delete the source file)"
        )

    api = _get_client()

    try:
        # Step 1: Read source file content
        content = api.get_file_contents(source_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read source file '{source_path}': {str(e)}")

    try:
        # Step 2: Write to destination (automatically creates parent directories)
        api.put_content(destination_path, content)
    except Exception as e:
        raise RuntimeError(
            f"Failed to write to destination '{destination_path}': {str(e)}. "
            f"Source file '{source_path}' was not deleted."
        )

    try:
        # Step 3: Delete source file (only after successful write)
        api.delete_file(source_path)
    except Exception as e:
        # Destination file was created but source deletion failed
        # This is a partial failure state - inform the user
        return {
            "success": False,
            "message": f"File was copied to '{destination_path}' but failed to delete source '{source_path}': {str(e)}. "
            f"You may need to manually delete the source file.",
            "source_path": source_path,
            "destination_path": destination_path,
            "partial_success": True,
        }

    return {
        "success": True,
        "message": f"Successfully moved '{source_path}' to '{destination_path}'",
        "source_path": source_path,
        "destination_path": destination_path,
    }


@mcp.tool(
    description="""Move or rename multiple files in the vault in a single operation.

    Processes each file move independently - if some files fail, others will still be processed.
    Each file is moved using the same read → write → delete pattern as the single file move.

    This is useful for:
    - Moving multiple files to a new directory
    - Batch renaming files
    - Reorganizing vault structure

    Returns detailed results for each file operation including successes and failures.""",
)
def obsidian_bulk_move_files(
    moves: Annotated[
        List[Dict[str, str]],
        Field(
            description="List of move operations, each with 'source' and 'destination' keys. "
            "Example: [{'source': 'old/file1.md', 'destination': 'new/file1.md'}, "
            "{'source': 'old/file2.md', 'destination': 'new/file2.md'}]"
        ),
    ],
    confirm: Annotated[
        bool,
        Field(
            description="Must be set to true to perform bulk move operations (this will delete source files)"
        ),
    ] = False,
) -> Annotated[
    Dict[str, Any],
    Field(description="Results with success/failure details for each file"),
]:
    if not confirm:
        raise RuntimeError(
            "confirm must be set to true to move files in bulk (this will delete source files)"
        )

    if not moves:
        raise ValueError("moves list cannot be empty")

    # Validate all move operations have required keys
    for i, move_op in enumerate(moves):
        if not isinstance(move_op, dict):
            raise ValueError(f"Move operation at index {i} must be a dictionary")
        if "source" not in move_op:
            raise ValueError(f"Move operation at index {i} missing 'source' key")
        if "destination" not in move_op:
            raise ValueError(f"Move operation at index {i} missing 'destination' key")

    api = _get_client()
    results = []
    success_count = 0
    failure_count = 0

    for i, move_op in enumerate(moves):
        source_path = move_op["source"]
        destination_path = move_op["destination"]

        try:
            # Step 1: Read source file content
            try:
                content = api.get_file_contents(source_path)
            except Exception as e:
                raise RuntimeError(f"Failed to read source file: {str(e)}")

            # Step 2: Write to destination
            try:
                api.put_content(destination_path, content)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to write to destination (source not deleted): {str(e)}"
                )

            # Step 3: Delete source file
            try:
                api.delete_file(source_path)
            except Exception as e:
                # Partial failure - file copied but not deleted
                results.append(
                    {
                        "index": i,
                        "source": source_path,
                        "destination": destination_path,
                        "success": False,
                        "partial_success": True,
                        "error": f"File copied to destination but failed to delete source: {str(e)}",
                    }
                )
                failure_count += 1
                continue

            # Success
            results.append(
                {
                    "index": i,
                    "source": source_path,
                    "destination": destination_path,
                    "success": True,
                }
            )
            success_count += 1

        except Exception as e:
            # Complete failure
            results.append(
                {
                    "index": i,
                    "source": source_path,
                    "destination": destination_path,
                    "success": False,
                    "error": str(e),
                }
            )
            failure_count += 1

    return {
        "total": len(moves),
        "successful": success_count,
        "failed": failure_count,
        "success_rate": round(success_count / len(moves) * 100, 2),
        "results": results,
    }


@mcp.tool(
    description="""Advanced search using JsonLogic queries to combine multiple criteria.

           USE THIS TOOL WHEN:
           - You need to filter by file path/location AND content together
           - You need to combine multiple search criteria with AND/OR logic
           - You want to use glob patterns to match file paths
           - You need regex pattern matching on paths or content
           - Simple text search is too broad and returns too many results

           DO NOT USE THIS TOOL WHEN:
           - You just need simple text search → Use obsidian_simple_search
           - You're searching purely by tags → Use obsidian_search_by_tags (simpler)
           - You're searching purely by frontmatter → Use obsidian_search_by_frontmatter (simpler)
           - You need fuzzy matching → Use obsidian_omnisearch_search (if available)

           Supports standard JsonLogic operators plus 'glob' and 'regexp' for pattern matching.
           Results must be non-falsy. ALWAYS follow query syntax in examples.

           Examples:
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

             4. Match files in specific folders OR with specific extensions
             {
               "or": [
                 { "glob": ["Projects/*", {"var": "path"}] },
                 { "glob": ["*.pdf", {"var": "path"}] }
               ]
             }
           """,
)
def obsidian_complex_search(
    query: Annotated[dict, Field(description="The JsonLogic query to execute")],
) -> Annotated[
    List[Dict[str, Any]],
    Field(
        description="A list of files matching the search query with path and metadata"
    ),
]:
    api = _get_client()
    raw_results = api.search_json(query)

    # Transform results to ensure they're proper dictionaries
    # The API may return objects that need conversion
    results = []
    for item in raw_results:
        if isinstance(item, dict):
            results.append(item)
        elif hasattr(item, "__dict__"):
            # Convert object to dict
            results.append(vars(item))
        elif hasattr(item, "model_dump"):
            # Pydantic model
            results.append(item.model_dump())
        else:
            # Fallback: convert to string representation
            results.append({"path": str(item)})

    return results


@mcp.tool(
    description="Return the contents of multiple files in your vault as a structured array. Each element contains the file path, content, and success status.",
)
def obsidian_batch_get_file_contents(
    filepaths: Annotated[list[str], Field(description="List of file paths to read")],
) -> Annotated[
    List[Dict[str, Any]],
    Field(description="Array of objects with 'path', 'content', and 'success' fields"),
]:
    api = _get_client()
    results = []

    for filepath in filepaths:
        try:
            content = api.get_file_contents(filepath)
            results.append({"path": filepath, "content": content, "success": True})
        except Exception as e:
            results.append({"path": filepath, "error": str(e), "success": False})

    return results


@mcp.tool(
    description="""Get current periodic note for the specified period. REQUIRES the Periodic Notes plugin with the requested period type enabled in Obsidian.

    Returns either the note content or its metadata depending on the 'type' parameter.

    Examples:
    - period="daily", type="content": Returns today's daily note content as a string
    - period="weekly", type="metadata": Returns this week's note metadata (frontmatter, tags, stats)
    - period="monthly", type="content": Returns this month's note content
    - period="yearly", type="content": Returns this year's note content

    The 'metadata' type returns a dict with: content, frontmatter, tags, and file statistics.
    The 'content' type returns just the note text as a string.""",
)
def obsidian_get_periodic_note(
    period: Annotated[
        str,
        Field(
            description="The period type: 'daily', 'weekly', 'monthly', 'quarterly', or 'yearly'"
        ),
    ],
    type: Annotated[
        str, Field(description="Return format: 'content' (text only) or 'metadata' (full metadata dict including content, frontmatter, tags, stats)")
    ] = "content",
) -> Annotated[Any, Field(description="Either a string (if type='content') or a dict with metadata (if type='metadata')")]:
    utils.validate_period_type(period)
    utils.validate_note_type(type)

    api = _get_client()
    return api.get_periodic_note(period, type)


@mcp.tool(
    description="""Get most recent periodic notes for the specified period type. REQUIRES the Periodic Notes plugin with the requested period type enabled in Obsidian.

    Returns a list of recent notes with metadata, optionally including full content.

    Examples:
    - period="daily", limit=7: Get last 7 daily notes (metadata only, no content)
    - period="daily", limit=7, include_content=True: Get last 7 daily notes with full content
    - period="weekly", limit=4: Get last 4 weekly notes (metadata only)
    - period="monthly", limit=12, include_content=True: Get last 12 monthly notes with content

    Without include_content: Returns lightweight metadata (filename, date, path, frontmatter)
    With include_content=True: Also includes the full note content in each result""",
)
def obsidian_get_recent_periodic_notes(
    period: Annotated[
        str,
        Field(
            description="The period type: 'daily', 'weekly', 'monthly', 'quarterly', or 'yearly'"
        ),
    ],
    limit: Annotated[
        int, Field(description="Maximum number of notes to return (e.g., 7 for last week of daily notes)")
    ] = constants.PERIODIC_NOTES_DEFAULT_LIMIT,
    include_content: Annotated[
        bool, Field(description="If True, include full note content in results. If False (default), only return metadata (more efficient)")
    ] = False,
) -> Annotated[
    List[Dict[str, Any]],
    Field(description="List of note objects with metadata, optionally including 'content' field if include_content=True"),
]:
    utils.validate_period_type(period)
    utils.validate_positive_integer(limit, "limit")
    utils.validate_boolean(include_content, "include_content")

    api = _get_client()
    return api.get_recent_periodic_notes(period, limit, include_content)


@mcp.tool(
    description="""Get recently modified files in the vault. REQUIRES the Dataview plugin to be installed and enabled in Obsidian.

    Returns files sorted by modification time (newest first), with timestamps and file paths.

    Examples:
    - limit=10, days=7: Get the 10 most recently modified files from the last 7 days
    - limit=20, days=30: Get the 20 most recently modified files from the last month
    - limit=5, days=1: Get the 5 most recently modified files from today

    Useful for:
    - Finding recently edited notes
    - Tracking active work areas
    - Reviewing recent changes before syncing

    Each result includes: path, modification time, and optionally other metadata.""",
)
def obsidian_get_recent_changes(
    limit: Annotated[
        int, Field(description="Maximum number of files to return (sorted by modification time, newest first)")
    ] = constants.RECENT_CHANGES_DEFAULT_LIMIT,
    days: Annotated[
        int, Field(description="Only include files modified within this many days (filters by recency window)")
    ] = constants.RECENT_CHANGES_DEFAULT_DAYS,
) -> Annotated[
    List[Dict[str, Any]],
    Field(
        description="List of file objects with paths and modification timestamps, sorted newest first"
    ),
]:
    utils.validate_positive_integer(limit, "limit")
    utils.validate_positive_integer(days, "days")

    api = _get_client()
    return api.get_recent_changes(limit, days)


# ==============================================================================
# MCP Resources (Read-Only Metadata Access)
# ==============================================================================


@mcp.resource("obsidian://vault/{filepath}/metadata")
def get_file_metadata_resource(
    filepath: Annotated[str, Field(description="File path relative to vault root")],
) -> Annotated[
    Dict[str, Any],
    Field(
        description="Complete file metadata including content, frontmatter, tags, and stats"
    ),
]:
    """Get complete metadata for a file: content, frontmatter, tags, and file statistics.

    This resource provides read-only access to all metadata associated with a file,
    including YAML frontmatter, extracted tags, and filesystem statistics.
    """
    api = _get_client()
    return api.get_file_metadata(filepath)


@mcp.resource("obsidian://vault/{filepath}/content")
def get_file_content_resource(
    filepath: Annotated[str, Field(description="File path relative to vault root")],
) -> Annotated[str, Field(description="The file content as a string")]:
    """Get only the file content (without metadata).

    This resource provides efficient access to just the file content,
    without fetching frontmatter, tags, or stats. More efficient than
    the /metadata resource when you only need the content.
    """
    api = _get_client()
    return api.get_file_contents(filepath)


# ==============================================================================
# Search Tools (Tag and Frontmatter Queries)
# ==============================================================================


@mcp.tool(
    description="""Search for files by tags.

    USE THIS TOOL WHEN:
    - You need to find files with specific tags
    - You want to filter notes by category/topic (using tags)
    - You know the tags and want to find all related notes
    - You need to combine multiple tag criteria (AND/OR logic)

    DO NOT USE THIS TOOL WHEN:
    - You need to search note content → Use obsidian_simple_search
    - You need to search by frontmatter fields → Use obsidian_search_by_frontmatter
    - You need to combine tag search with path filters → Use obsidian_complex_search
    - You don't know what tags exist → Use obsidian_list_all_tags first

    Supports both AND and OR logic. Tags should be provided without the # prefix.

    Examples:
    - tags=["meeting", "urgent"], match_all=False: Files with #meeting OR #urgent (either tag)
    - tags=["project", "2024"], match_all=True: Files with BOTH #project AND #2024
    - tags=["todo"], match_all=False: All files with #todo tag
    - tags=["python", "tutorial", "beginner"], match_all=True: Files with all three tags

    Use match_all=False (default) for broader searches (OR logic)
    Use match_all=True for precise filtering (AND logic - more restrictive)""",
)
def obsidian_search_by_tags(
    tags: Annotated[
        List[str], Field(description="List of tags to search for (without # prefix, e.g., ['meeting', 'work'])")
    ],
    match_all: Annotated[
        bool,
        Field(
            description="If True, files must have ALL tags (AND logic). If False (default), files with ANY tag match (OR logic)."
        ),
    ] = False,
) -> Annotated[
    List[Dict[str, Any]], Field(description="List of files matching the tag criteria, each with path and metadata")
]:
    api = _get_client()
    return api.search_by_tags(tags, match_all)


@mcp.tool(
    description="""Search files by YAML frontmatter metadata fields.

    USE THIS TOOL WHEN:
    - You need to filter by frontmatter fields (status, author, date, custom fields, etc.)
    - You want to find files with specific metadata values
    - You need to check if a frontmatter field exists
    - You're organizing notes with structured metadata

    DO NOT USE THIS TOOL WHEN:
    - You need to search note content → Use obsidian_simple_search
    - You need to search by tags (inline #tags) → Use obsidian_search_by_tags
    - You need to combine with path filters → Use obsidian_complex_search
    - Tags are in frontmatter as YAML arrays → Use this tool with field="tags"

    This tool searches YAML frontmatter at the top of markdown files.

    Operators:
    - "equals": Find files where field exactly matches the value
    - "contains": Find files where field contains the value (works for strings and arrays)
    - "exists": Find files that have the specified field (value parameter not needed)

    Example uses:
    - Find files with status="done": field="status", value="done", operator="equals"
    - Find files with any status field: field="status", operator="exists"
    - Find files with tags array containing "project": field="tags", value="project", operator="contains"
    - Find files by author: field="author", value="John Smith", operator="equals"
    """,
)
def obsidian_search_by_frontmatter(
    field: Annotated[str, Field(description="Frontmatter field name to search")],
    value: Annotated[
        Any, Field(description="Value to match (optional if operator is 'exists')")
    ] = None,
    operator: Annotated[
        str, Field(description="Comparison operator: 'equals', 'contains', or 'exists'")
    ] = "equals",
) -> Annotated[
    List[Dict[str, Any]],
    Field(description="List of files where frontmatter matches the criteria"),
]:
    api = _get_client()
    return api.search_by_frontmatter(field, value, operator)


@mcp.tool(
    description="""List all unique tags in the vault with usage counts.

    USE THIS TOOL WHEN:
    - You need to discover what tags exist in the vault
    - You want to see tag usage statistics
    - You're exploring the vault's tagging system
    - You need to validate a tag name before searching
    - You want to find popular/commonly used tags

    DO NOT USE THIS TOOL WHEN:
    - You already know the tag and want to find files → Use obsidian_search_by_tags
    - You need to search note content → Use obsidian_simple_search
    - You're looking for frontmatter fields → Use obsidian_search_by_frontmatter

    Returns a dictionary mapping each tag to the number of files using it.
    This is useful for getting an overview of all tags in your vault and
    understanding tag popularity.

    Note: This operation scans all markdown files in the vault and may take
    some time for large vaults.""",
)
def obsidian_list_all_tags() -> Annotated[
    Dict[str, int],
    Field(description="Dictionary mapping tag names to the number of files using them"),
]:
    api = _get_client()
    return api.list_all_tags()


@mcp.tool(
    description="""Search for folders/directories by name.

    USE THIS TOOL WHEN:
    - You need to find directories/folders, not files
    - You want to discover folder structure
    - You're looking for a folder but don't know the exact path
    - You need to explore folder organization

    DO NOT USE THIS TOOL WHEN:
    - You're searching for files → Use other search tools
    - You're searching file content → Use obsidian_simple_search
    - You already know the exact folder path → Use obsidian_list_files_in_dir directly

    Searches through the entire vault folder hierarchy (or from a specified root)
    and returns all folders whose names contain the search term (case-insensitive).

    Examples:
    - folder_name="project": Find folders like "Projects", "my-project", "PROJECT-2024"
    - folder_name="archive", root_path="Notes": Find all archive folders under Notes
    - folder_name="2024": Find all folders with year 2024 in their name""",
)
def obsidian_search_folders(
    folder_name: Annotated[
        str,
        Field(description="Substring to search for in folder names (case-insensitive)"),
    ],
    root_path: Annotated[
        str,
        Field(
            description="Optional root directory to start search from (defaults to vault root)"
        ),
    ] = "",
) -> Annotated[
    List[str], Field(description="List of folder paths that match the search criteria")
]:
    api = _get_client()
    return api.search_folders(folder_name, root_path)


# ==============================================================================
# Omnisearch Integration (Optional - Conditional Registration)
# ==============================================================================

if omnisearch_config.enabled:

    @mcp.tool(
        description="""Advanced fuzzy search using Omnisearch plugin.

        USE THIS TOOL WHEN:
        - You want typo-tolerant / fuzzy matching (user might have typos)
        - You need to search across PDFs and images (OCR)
        - You want advanced relevance scoring (BM25 algorithm)
        - Simple search returns nothing due to typos or variations
        - You want recency-boosted results (recent files ranked higher)
        - You're doing exploratory search with uncertain spelling

        DO NOT USE THIS TOOL WHEN:
        - Simple exact text search is sufficient → Use obsidian_simple_search
        - You need to filter by tags → Use obsidian_search_by_tags
        - You need to filter by frontmatter → Use obsidian_search_by_frontmatter
        - You need complex path/content logic → Use obsidian_complex_search
        - Omnisearch plugin is not installed → Falls back to obsidian_simple_search

        FEATURES:
        - Fuzzy matching for typo-tolerant searches
        - BM25 relevance scoring (industry-standard ranking algorithm)
        - OCR support for searching text in images
        - PDF indexing and search
        - Recency boosting for recently modified files
        - Intelligent tokenization
        - Automatic fallback to simple_search if Omnisearch unavailable

        SEARCH SYNTAX & OPERATORS:
        - path:"folder/path" - Restrict results to specific directory
        - ext:"md pdf" or ext:md or .md - Filter by file type(s)
        - "exact phrase" - Match precise multi-word expressions
        - -excluded - Exclude notes containing specific words

        QUERY TIPS:
        - Best queries are spontaneous words that come to mind
        - Use words from filenames, titles, or unique terminology
        - Titles and headings are weighted more than body text
        - Omnisearch handles typos automatically

        EXAMPLES:
        - meeting notes 2024 - Simple fuzzy search
        - path:"Work/Projects" deadline - Search in specific folder
        - "machine learning" -basics - Exact phrase, exclude basics
        - ext:pdf neural networks - Search only PDFs

        NOTE: If Omnisearch HTTP server is unavailable, automatically falls back to
        obsidian_simple_search. Results will include a '_fallback' field when fallback is used.

        REQUIRES: Omnisearch plugin with HTTP server enabled in settings (optional).

        Returns detailed search results with relevance scores and context.""",
    )
    def obsidian_omnisearch_search(
        query: Annotated[
            str, Field(description="Search query string (supports typos, variations)")
        ],
    ) -> Annotated[
        List[Dict[str, Any]],
        Field(
            description="List of search results with relevance scoring from Omnisearch"
        ),
    ]:
        """Search using Omnisearch plugin with automatic fallback to simple search.

        If Omnisearch is unavailable, automatically falls back to obsidian_simple_search.
        """
        client = _get_omnisearch_client()

        try:
            return client.search(query)
        except Exception as e:
            # If Omnisearch is unavailable, fall back to regular Obsidian simple search
            error_msg = str(e)
            if (
                "Connection refused" in error_msg
                or "request failed" in error_msg.lower()
            ):
                # Fall back to regular Obsidian simple search
                api = _get_client()
                results = api.search(
                    query, context_length=constants.SEARCH_DEFAULT_CONTEXT_LENGTH
                )

                # Format results and add fallback indicator
                formatted_results = utils.format_search_results(results)
                return utils.add_fallback_indicator(formatted_results)
            else:
                # Re-raise if it's not a connection error
                raise
