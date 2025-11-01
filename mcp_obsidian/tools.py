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

TOOLS ({"21" if omnisearch_config.enabled else "20"} available):
- File Operations: list, read, write, append, batch read, delete, move/rename, bulk move/rename
- Search: simple text search, complex JsonLogic queries, search by tags/frontmatter, folder search{", Omnisearch advanced search (with fuzzy matching, BM25 scoring)" if omnisearch_config.enabled else ""}
- Content Patching: insert content relative to headings/blocks/frontmatter
- Periodic Notes: access daily/weekly/monthly notes (requires Periodic Notes plugin)
- Recent Changes: track file modifications (requires Dataview plugin)

RESOURCES (2 available):
- obsidian://vault/{{filepath}}/metadata - Complete file metadata (content, frontmatter, tags, stats)
- obsidian://vault/{{filepath}}/content - File content only (plain text)

PATH CONVENTIONS:
- All file paths are relative to vault root (e.g., "Notes/meeting.md", not "/full/path/to/vault/Notes/meeting.md")
- Directories end with "/" when listing (strip when using as paths)
- Parent directories are created automatically when writing files

IMPORTANT:
- Delete and move operations require confirm=True parameter
- Use /content resource for text-only access (efficient)
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
    description="Lists all files and directories in the root directory of your Obsidian vault. Returns a structured object with separate lists for files and directories.",
)
def obsidian_list_files_in_vault(
    max_depth: Annotated[
        int,
        Field(
            description="Maximum recursion depth: 0=current directory only, 1=one level deep, -1=unlimited (default: 0)"
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
    description="Lists all files and directories that exist in a specific Obsidian directory. Returns a structured object with separate lists for files and directories.",
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
            description="Maximum recursion depth: 0=current directory only, 1=one level deep, -1=unlimited (default: 0)"
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
    description="""Simple search for documents matching a specified text query across all files in the vault.

    Returns a list of search results, each containing:
    - filename: The file path
    - score: Relevance score (negative values, closer to 0 is more relevant)
    - matches: Array of match objects with context and match_position (start/end)

    Use this tool when you want to do a simple text search.""",
)
def obsidian_simple_search(
    query: Annotated[str, Field(description="The search query")],
    context_length: Annotated[
        int, Field(description="Length of the context to return around each match")
    ] = constants.SEARCH_DEFAULT_CONTEXT_LENGTH,
) -> Annotated[
    List[Dict[str, Any]],
    Field(description="List of search results with filename, score, and matches"),
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
    description="Get current periodic note for the specified period. REQUIRES the Periodic Notes plugin with the requested period type enabled in Obsidian.",
)
def obsidian_get_periodic_note(
    period: Annotated[
        str,
        Field(
            description="The period type (daily, weekly, monthly, quarterly, yearly)"
        ),
    ],
    type: Annotated[
        str, Field(description="Type of the data to get ('content' or 'metadata')")
    ] = "content",
) -> Annotated[Any, Field(description="The content or metadata of the periodic note")]:
    utils.validate_period_type(period)
    utils.validate_note_type(type)

    api = _get_client()
    return api.get_periodic_note(period, type)


@mcp.tool(
    description="Get most recent periodic notes for the specified period type. REQUIRES the Periodic Notes plugin with the requested period type enabled in Obsidian.",
)
def obsidian_get_recent_periodic_notes(
    period: Annotated[
        str,
        Field(
            description="The period type (daily, weekly, monthly, quarterly, yearly)"
        ),
    ],
    limit: Annotated[
        int, Field(description="Maximum number of notes to return")
    ] = constants.PERIODIC_NOTES_DEFAULT_LIMIT,
    include_content: Annotated[
        bool, Field(description="Whether to include note content")
    ] = False,
) -> Annotated[
    List[Dict[str, Any]],
    Field(description="A list of recent periodic notes, with or without content"),
]:
    utils.validate_period_type(period)
    utils.validate_positive_integer(limit, "limit")
    utils.validate_boolean(include_content, "include_content")

    api = _get_client()
    return api.get_recent_periodic_notes(period, limit, include_content)


@mcp.tool(
    description="Get recently modified files in the vault. REQUIRES the Dataview plugin to be installed and enabled in Obsidian.",
)
def obsidian_get_recent_changes(
    limit: Annotated[
        int, Field(description="Maximum number of files to return")
    ] = constants.RECENT_CHANGES_DEFAULT_LIMIT,
    days: Annotated[
        int, Field(description="Only include files modified within this many days")
    ] = constants.RECENT_CHANGES_DEFAULT_DAYS,
) -> Annotated[
    List[Dict[str, Any]],
    Field(
        description="A list of recently modified files, with their modification times"
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
    description="""Search for files containing specified tags.

    Use this tool to find all files that have specific tags. Supports both AND and OR logic:
    - AND logic (match_all=True): Files must have ALL specified tags
    - OR logic (match_all=False): Files with ANY of the specified tags will match

    Tags should be provided without the # prefix.""",
)
def obsidian_search_by_tags(
    tags: Annotated[
        List[str], Field(description="List of tags to search for (without # prefix)")
    ],
    match_all: Annotated[
        bool,
        Field(
            description="If True, files must have ALL tags (AND). If False, files with ANY tag match (OR)."
        ),
    ] = False,
) -> Annotated[
    List[Dict[str, Any]], Field(description="List of files matching the tag criteria")
]:
    api = _get_client()
    return api.search_by_tags(tags, match_all)


@mcp.tool(
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
    description="""Get all unique tags in the vault with usage counts.

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
    description="""Recursively search for folders by name using case-insensitive substring matching.

    This tool searches through the entire vault folder hierarchy (or from a specified root)
    and returns all folders whose names contain the search term (case-insensitive).

    Examples:
    - Search for "project" to find folders like "Projects", "my-project", "PROJECT-2024"
    - Search for "archive" in "Notes" folder to find all archive folders under Notes
    - Search for "2024" to find all folders with year 2024 in their name""",
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
        description="""Search vault using Omnisearch plugin's advanced search engine.

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
        - meeting notes 2024 - Simple search
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
