# AGENTS.md - MCP Obsidian Server Maintenance Guide

This file provides guidance for AI assistants and developers working on this codebase.

## Project Overview

**Name:** mcp-obsidian
**Type:** Model Context Protocol (MCP) server for Obsidian vault access
**Framework:** FastMCP 2.0+
**Language:** Python 3.11+
**Purpose:** Provides programmatic access to Obsidian vaults via the Local REST API plugin
**Repository:** https://github.com/sirtaj/mcp-obsidian

This is a fork of [MarkusPfundstein/mcp-obsidian](https://github.com/MarkusPfundstein/mcp-obsidian) that migrated from the legacy `mcp` library to `fastmcp 2.0+`.

## Architecture

### Four-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CLI Layer (server.py)                                      │
│  - Argument parsing                                         │
│  - Transport mode selection                                 │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│  Tools Layer (tools.py)                                     │
│  - FastMCP server initialization                            │
│  - Tool registrations (conditional Omnisearch)              │
│  - Resource registrations                                   │
└──────────────┬──────────────────────────────────────────────┘
               │
        ┌──────┴───────┬────────────────┐
        │              │                │
┌───────▼─────┐  ┌─────▼──────────┐  ┌─▼──────────┐
│ obsidian.py │  │ omnisearch.py  │  │ config.py  │
│             │  │ (optional)     │  │ constants  │
│ - REST API  │  │ - HTTP search  │  │ utils.py   │
│ - 14 methods│  │ - 1 method     │  └────────────┘
└─────────────┘  └────────────────┘
```

### Core Files

| File | Purpose | Lines | Key Responsibilities |
|------|---------|-------|---------------------|
| `mcp_obsidian/server.py` | Entry point | ~71 | CLI argument parsing, transport mode handling |
| `mcp_obsidian/tools.py` | Tool registry | ~1036 | MCP tool definitions, resources, FastMCP server config |
| `mcp_obsidian/obsidian.py` | Obsidian API client | ~663 | HTTP communication with Obsidian Local REST API |
| `mcp_obsidian/omnisearch.py` | Omnisearch client | ~92 | HTTP communication with Omnisearch plugin (optional) |
| `mcp_obsidian/config.py` | Configuration mgmt | ~73 | Environment variable loading, config dataclasses |
| `mcp_obsidian/constants.py` | Constants | ~83 | Named constants (follows user guideline) |
| `mcp_obsidian/utils.py` | Utilities | ~134 | Shared helper functions, validators, formatters |

### Tool Categories

The server provides tools organized into these categories:

1. **File Operations**
   - List vault/directory contents (with recursive depth control)
   - Read single/batch files
   - Append/overwrite content
   - Delete files/directories (with safety confirmation)

2. **File Organization**
   - Move/rename single file (with safety confirmation)
   - Bulk move/rename multiple files

3. **Content Analysis**
   - List headings in a file

4. **Content Patching**
   - Insert content relative to headings/blocks/frontmatter

5. **Search Operations**
   - Simple text search
   - Complex JsonLogic queries
   - Search by tags/frontmatter
   - Folder search
   - List all tags
   - **Omnisearch integration (optional)**: Advanced fuzzy search with BM25 scoring

6. **Periodic Notes**
   - Get current/recent periodic notes (requires Periodic Notes plugin)

7. **Recent Changes**
   - Track recent file modifications (requires Dataview plugin)

## Recent Additions (Since AGENTS.md Creation)

The codebase has been significantly enhanced with:

### New Tools
- **obsidian_list_headings** - Extract all headings from a file (supports filtering by level)
- **obsidian_move_file** - Move or rename a single file (requires confirmation)
- **obsidian_bulk_move_files** - Batch move/rename multiple files efficiently

### New Modules
- **config.py** - Centralized configuration management with dataclasses
- **constants.py** - All magic numbers extracted to named constants
- **utils.py** - Shared helper functions (validators, formatters, separators)

### Enhanced Features
- **Recursive directory listing** - `max_depth` parameter for controlled recursion
- **Improved error handling** - Dedicated validation functions in utils.py
- **Better separation of concerns** - Configuration, constants, and utilities isolated
- **MCP Resources** - Two read-only resources for efficient data access

## Key Design Patterns

### 1. Stateless Tool Execution

Each tool creates a fresh `Obsidian()` client instance. No shared state between calls.

```python
@mcp.tool()
def obsidian_list_files_in_vault() -> list[str]:
    obs = Obsidian(...)  # Fresh instance per call
    return obs.list_files_in_vault()
```

### 2. Error Handling Pattern

The `Obsidian._safe_call()` wrapper handles all API errors gracefully:

```python
def _safe_call(self, fn: Callable[..., T]) -> T:
    try:
        return fn()
    except requests.HTTPError as e:
        # Parse JSON error response
    except requests.exceptions.RequestException as e:
        # Generic request failures
```

**Important:** Batch operations continue on individual failures (resilient design).

### 3. Type Annotations with Documentation

All tools use `Annotated` types with Pydantic `Field` for inline documentation:

```python
def obsidian_get_file_contents(
    filepath: Annotated[str, Field(description="The path to the file...")]
) -> str:
```

This provides rich type hints AND user-facing documentation.

### 4. Environment-Based Configuration

Configuration loaded via `python-dotenv` and managed through `config.py`:

```python
# In config.py
@dataclass(frozen=True)
class ObsidianConfig:
    api_key: str
    host: str
    port: int
    protocol: str

# In tools.py
obsidian_config = config.get_obsidian_config()
client = Obsidian(
    api_key=obsidian_config.api_key,
    host=obsidian_config.host,
    port=obsidian_config.port,
    protocol=obsidian_config.protocol
)
```

Benefits:
- Type safety with frozen dataclasses
- Centralized validation
- Single source of truth for defaults
- No config files needed beyond `.env`

### 5. Optional Feature Pattern: Omnisearch Integration

The Omnisearch integration demonstrates the pattern for optional features with separate client modules:

```python
# In tools.py:
from . import obsidian, omnisearch  # Separate client modules

# Environment-based feature flag
omnisearch_enabled = os.getenv("OMNISEARCH_ENABLED", "false").lower() == "true"

def _get_omnisearch_client() -> omnisearch.OmnisearchClient:
    """Separate client factory for optional feature."""
    return omnisearch.OmnisearchClient(
        host=omnisearch_host,
        port=omnisearch_port,
        protocol=omnisearch_protocol
    )

# Conditional tool registration
if omnisearch_enabled:
    @mcp.tool(name=OMNISEARCH_TOOL_NAME)
    def obsidian_omnisearch_search(query: str) -> list[dict]:
        client = _get_omnisearch_client()

        try:
            return client.search(query)
        except Exception as e:
            # Automatic fallback to obsidian_simple_search if Omnisearch unavailable
            if "Connection refused" in str(e) or "request failed" in str(e).lower():
                api = _get_client()
                results = api.search(query, context_length=100)
                # Add fallback indicator to results
                for result in results:
                    result['_fallback'] = 'Used Obsidian simple_search (Omnisearch unavailable)'
                return results
            else:
                raise
```

**Key aspects:**
- **Separate module**: `omnisearch.py` keeps Omnisearch code isolated from `obsidian.py`
- **Multi-level graceful degradation**:
  1. Server starts successfully even if `OMNISEARCH_ENABLED=false`
  2. Tool automatically falls back to `obsidian_simple_search` if Omnisearch unreachable
- Tool only registered when enabled via environment variable
- Dedicated client factory function `_get_omnisearch_client()`
- **Independent host configuration**: `OMNISEARCH_HOST` can differ from `OBSIDIAN_HOST`

**Configuration:**
```bash
OMNISEARCH_ENABLED=true        # Enable feature
OMNISEARCH_HOST=127.0.0.1      # Can be different from OBSIDIAN_HOST
OMNISEARCH_PORT=51361          # Default port
OMNISEARCH_PROTOCOL=http       # Typically HTTP
```

**When to use this pattern:**
- Optional plugin integrations (like Omnisearch, Periodic Notes, Dataview)
- Features requiring external services
- Experimental/beta features

## Common Maintenance Tasks

### Adding a New Tool

1. **Add API method to `obsidian.py`:**
   ```python
   def new_api_method(self, param: str) -> dict:
       return self._safe_call(lambda: ...)
   ```

2. **Register tool in `tools.py`:**
   ```python
   @mcp.tool()
   def obsidian_new_tool(
       param: Annotated[str, Field(description="...")]
   ) -> dict:
       obs = Obsidian(api_key, host, port, protocol)
       return obs.new_api_method(param)
   ```

3. **Update README.md** with usage examples

4. **Test with Claude Desktop** or `mcp dev`

### Adding a New Optional Client Module

Follow the Omnisearch pattern for plugin integrations or external services:

1. **Create new client module** (e.g., `newplugin.py`):
   ```python
   import requests
   from typing import Any

   DEFAULT_PLUGIN_PORT = 12345

   class PluginClient:
       def __init__(self, host: str, port: int, protocol: str = "http"):
           self.host = host
           self.port = port
           self.protocol = protocol

       def _safe_call(self, f) -> Any:
           # Standard error handling pattern
           ...

       def search(self, query: str) -> list[dict]:
           # API implementation
           ...
   ```

2. **Add environment variables in `tools.py`:**
   ```python
   from . import obsidian, omnisearch, newplugin

   plugin_enabled = os.getenv("PLUGIN_ENABLED", "false").lower() == "true"
   plugin_host = os.getenv("PLUGIN_HOST", obsidian_host)
   plugin_port = int(os.getenv("PLUGIN_PORT", str(newplugin.DEFAULT_PLUGIN_PORT)))
   ```

3. **Create client factory function:**
   ```python
   def _get_plugin_client() -> newplugin.PluginClient:
       return newplugin.PluginClient(
           host=plugin_host,
           port=plugin_port
       )
   ```

4. **Conditionally register tool:**
   ```python
   if plugin_enabled:
       @mcp.tool(name="obsidian_plugin_search")
       def obsidian_plugin_search(query: str) -> list[dict]:
           client = _get_plugin_client()
           return client.search(query)
   ```

5. **Update documentation** (README.md, AGENTS.md, .env.example)

**Why separate modules:**
- Clear separation of concerns
- Easier to maintain and test
- Optional features don't bloat core client
- Independent error handling and dependencies

### Updating Dependencies

```bash
# Add new dependency
uv add package-name

# Update fastmcp (important for MCP spec updates)
uv add fastmcp@latest

# Regenerate lockfile
uv lock
```

### Modifying the API Client

When changing `obsidian.py`:

1. **Consult `openapi.yaml`** for correct endpoint specs
2. **Maintain the `_safe_call()` wrapper** for all HTTP operations
3. **Use appropriate HTTP methods:**
   - GET: Reading data
   - POST: Creating/searching
   - PUT: Overwriting
   - PATCH: Partial updates
   - DELETE: Removing

4. **Keep SSL verification disabled** (Obsidian uses self-signed certs):
   ```python
   response = requests.get(..., verify=False)
   ```

### Magic Numbers Refactoring (Completed)

**Status**: ✅ Complete - All magic numbers have been extracted to `constants.py` following user guidelines.

The codebase now uses a dedicated `constants.py` module with descriptive, named constants:

**Obsidian Configuration:**
- `DEFAULT_OBSIDIAN_PORT = 27124`
- `CONNECTION_TIMEOUT_SECONDS = 3`
- `READ_TIMEOUT_SECONDS = 6`
- `DELETE_TIMEOUT_SECONDS = 30`
- `OBSIDIAN_SSL_VERIFY = False`

**Search Configuration:**
- `SEARCH_DEFAULT_CONTEXT_LENGTH = 100`

**Periodic Notes:**
- `PERIODIC_NOTES_DEFAULT_LIMIT = 5`
- `VALID_PERIOD_TYPES = ["daily", "weekly", "monthly", "quarterly", "yearly"]`
- `VALID_PERIODIC_NOTE_TYPES = ["content", "metadata"]`

**Recent Changes:**
- `RECENT_CHANGES_DEFAULT_LIMIT = 10`
- `RECENT_CHANGES_DEFAULT_DAYS = 90`

**Other:**
- `DEFAULT_MCP_SERVER_PORT = 37123`
- `VALID_FRONTMATTER_OPERATORS = ["equals", "contains", "exists"]`

All code now imports from `constants` module instead of using inline literals.

## Testing Strategy

### Manual Testing with Claude Desktop

1. **Add to Claude Desktop config:**

**Config file locations:**
- **MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**For production use (GitHub install):**
   ```json
   {
     "mcpServers": {
       "obsidian": {
         "command": "uvx",
         "args": [
           "--from",
           "git+https://github.com/sirtaj/mcp-obsidian.git",
           "mcp-obsidian"
         ],
         "env": {
           "OBSIDIAN_API_KEY": "your_key_here"
         }
       }
     }
   }
   ```

**For local development:**
   ```json
   {
     "mcpServers": {
       "obsidian": {
         "command": "uv",
         "args": ["--directory", "/path/to/mcp-obsidian", "run", "mcp-obsidian"],
         "env": {
           "OBSIDIAN_API_KEY": "your_key_here"
         }
       }
     }
   }
   ```

2. **Test each tool category:**
   - File operations: List, read, write, append
   - Search: Simple and complex queries
   - Periodic notes: Daily/weekly/monthly access
   - Delete: Verify confirmation requirement

3. **Check error handling:**
   - Invalid file paths (should fail gracefully)
   - Missing API key (should error clearly)
   - Network issues (should handle timeouts)

### Development Testing

```bash
# Run with stdio (default)
uv run mcp-obsidian

# Run with HTTP for debugging
uv run mcp-obsidian --transport http --port 8080

# Type checking
uv run pyright mcp_obsidian/
```

## Important Gotchas

### 1. SSL Verification Disabled

The Obsidian Local REST API uses self-signed certificates. **Do not enable SSL verification** or requests will fail:

```python
# Correct
response = requests.get(url, verify=False)

# Wrong - will fail with SSL errors
response = requests.get(url, verify=True)
```

### 2. Delete Tool Safety

`obsidian_delete_file()` requires explicit confirmation to prevent accidents:

```python
# Won't work
delete_file("important.md")  # Raises RuntimeError

# Correct
delete_file("important.md", confirm=True)
```

This is intentional - deletes are destructive and irreversible.

### 3. Period Type Validation

Periodic note tools only accept specific period types:

```python
VALID_PERIODS = ["daily", "weekly", "monthly", "quarterly", "yearly"]
```

Any other value will raise `ValueError`.

### 4. Batch Operations Continue on Errors

`obsidian_batch_get_file_contents()` doesn't fail if one file errors:

```python
# If file2.md doesn't exist, you still get file1.md and file3.md
results = batch_get(["file1.md", "file2.md", "file3.md"])
```

Check the returned content for individual error messages.

### 5. File Paths are Vault-Relative

All file paths are relative to the vault root, not absolute system paths:

```python
# Correct
get_file_contents("Notes/Meeting.md")

# Wrong
get_file_contents("/Users/me/Vault/Notes/Meeting.md")
```

### 6. FastMCP 2.0+ Required

This fork **does not work** with the legacy `mcp` library. Always use `fastmcp >= 2.11.2`:

```toml
# Correct
dependencies = ["fastmcp>=2.11.2", ...]

# Won't work
dependencies = ["mcp", ...]  # Old library
```

### 7. Omnisearch Troubleshooting (Optional Feature)

If Omnisearch tool isn't available when expected:

**Check 1: Environment variable**
```bash
OMNISEARCH_ENABLED=true  # Must be lowercase "true"
```

**Check 2: HTTP server enabled in Omnisearch plugin**
- Obsidian > Settings > Omnisearch > Enable "HTTP Server"
- Verify port matches `OMNISEARCH_PORT` (default: 51361)

**Check 3: Server logs**
If enabled but connection fails, server will start successfully but tool won't be registered.
No error is raised - this is intentional graceful degradation.

**Check 4: Protocol**
Omnisearch typically uses HTTP, not HTTPS:
```bash
OMNISEARCH_PROTOCOL=http  # Usually HTTP, not HTTPS
```

**Expected behavior:**
- `OMNISEARCH_ENABLED=false`: Tool not registered (default)
- `OMNISEARCH_ENABLED=true` + working connection: Tool available
- `OMNISEARCH_ENABLED=true` + connection fails: Server starts, tool not registered

## API Reference

### Obsidian REST API Plugin Endpoints

The `obsidian.py` client wraps these endpoints:

| Method | Endpoint | Purpose | Tool(s) |
|--------|----------|---------|---------|
| GET | `/vault/` | List vault root | `list_files_in_vault` |
| GET | `/vault/{dirpath}/` | List directory | `list_files_in_dir` |
| GET | `/vault/{filepath}` | Read file | `get_file_contents`, `batch_get_file_contents` |
| GET | `/vault/{filepath}` | Get headings | `list_headings` |
| POST | `/vault/{filepath}` | Append content | `append_content` |
| PUT | `/vault/{filepath}` | Overwrite file | `put_content` |
| PATCH | `/vault/{filepath}` | Patch content | `patch_content` |
| PATCH | `/vault/{filepath}` | Move/rename file | `move_file`, `bulk_move_files` |
| DELETE | `/vault/{filepath}` | Delete file/dir | `delete_file` |
| POST | `/search/simple/` | Text search | `simple_search` |
| POST | `/search/` | JsonLogic/DQL search | `complex_search`, `get_recent_changes` |
| POST | `/search/` | Tag search | `search_by_tags` |
| POST | `/search/` | Frontmatter search | `search_by_frontmatter` |
| POST | `/search/` | Folder search | `search_folders` |
| GET | `/tags/` | List all tags | `list_all_tags` |
| GET | `/periodic/{period}/` | Current periodic note | `get_periodic_note` |
| GET | `/periodic/{period}/recent` | Recent periodic notes | `get_recent_periodic_notes` |

Full API spec available in `openapi.yaml`.

### Omnisearch Plugin HTTP API (Optional)

When enabled, the client also connects to Omnisearch's HTTP server:

| Method | Endpoint | Purpose | Tool |
|--------|----------|---------|------|
| GET | `/search?q={query}` | Advanced fuzzy search | `obsidian_omnisearch_search` |

**Base URL:** `http://{OMNISEARCH_HOST}:{OMNISEARCH_PORT}` (typically `http://127.0.0.1:51361`)

**Note:** Omnisearch API does not require authentication headers.

### Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `OBSIDIAN_API_KEY` | Yes | - | Bearer token from Local REST API plugin |
| `OBSIDIAN_HOST` | No | `127.0.0.1` | Obsidian server host |
| `OBSIDIAN_PORT` | No | `27124` | Obsidian server port |
| `OBSIDIAN_PROTOCOL` | No | `https` | HTTP or HTTPS |
| `OMNISEARCH_ENABLED` | No | `false` | Enable Omnisearch integration |
| `OMNISEARCH_HOST` | No | Same as `OBSIDIAN_HOST` | Omnisearch server host |
| `OMNISEARCH_PORT` | No | `51361` | Omnisearch server port |
| `OMNISEARCH_PROTOCOL` | No | `http` | HTTP or HTTPS (typically HTTP) |

## Code Quality Guidelines

### 1. Type Hints

Always provide complete type hints:

```python
# Good
def process_files(paths: list[str]) -> dict[str, Any]:
    ...

# Bad
def process_files(paths):
    ...
```

### 2. Docstrings in Tool Descriptions

Use `Field(description=...)` for user-facing documentation:

```python
@mcp.tool()
def my_tool(
    param: Annotated[str, Field(description="Clear explanation of what this parameter does")]
) -> str:
    """Optional internal docstring for developers."""
```

### 3. Error Messages

Provide clear, actionable error messages:

```python
# Good
raise ValueError(f"Invalid period type '{period}'. Must be one of: {VALID_PERIODS}")

# Bad
raise ValueError("Invalid period")
```

### 4. Consistent Naming

- Tools: `obsidian_verb_noun` (e.g., `obsidian_get_file_contents`)
- API methods: `verb_noun` (e.g., `get_file_contents`)
- Constants: `SCREAMING_SNAKE_CASE` (e.g., `DEFAULT_PORT`)
- Variables: `snake_case` (e.g., `api_key`)

### 5. Avoid Magic Numbers

Extract numeric literals to named constants (per user global instructions):

```python
# Good
DEFAULT_LIMIT = 10
results = search(limit=DEFAULT_LIMIT)

# Bad
results = search(limit=10)
```

## Extending the System

### Adding Support for New Obsidian API Features

1. **Check `openapi.yaml`** for new endpoints
2. **Add method to `Obsidian` class** in `obsidian.py`
3. **Wrap with `_safe_call()`** for error handling
4. **Register as MCP tool** in `tools.py`
5. **Test with actual Obsidian vault**
6. **Update README.md** with examples

### Adding New Transport Modes

FastMCP supports custom transports. To add one:

1. **Update `server.py` argument parser:**
   ```python
   parser.add_argument("--transport", choices=["stdio", "http", "sse", "new_mode"])
   ```

2. **Add to transport mapping:**
   ```python
   transport_map = {
       "stdio": mcp.settings.stdio_transport(),
       "http": mcp.settings.http_transport(host, port),
       "sse": mcp.settings.sse_transport(host, port),
       "new_mode": custom_transport_config(),
   }
   ```

3. **Test with MCP client**

### Supporting Multiple Vaults

Currently, the server connects to one vault per instance. To support multiple:

1. **Add vault selection parameter** to each tool
2. **Pass vault-specific config** to `Obsidian()` constructor
3. **Update environment config** to support multiple API keys/hosts
4. **Consider vault naming/aliasing** for user clarity

## File Manifest

```
/home/sirtaj/proj/mcp-obsidian/
├── mcp_obsidian/
│   ├── __init__.py           # Empty package marker
│   ├── server.py             # CLI entry point (~71 lines)
│   ├── tools.py              # 20-21 MCP tools, 2 resources (~1036 lines)
│   ├── obsidian.py           # Obsidian REST API client (~663 lines)
│   ├── omnisearch.py         # Omnisearch HTTP client (~92 lines, optional)
│   ├── config.py             # Configuration management (~73 lines)
│   ├── constants.py          # All constants/magic numbers (~83 lines)
│   └── utils.py              # Shared utilities (~134 lines)
├── tests/                    # Test suite (pytest)
│   ├── test_obsidian_tools.py
│   ├── test_metadata_search.py
│   └── README.md
├── pyproject.toml            # Project metadata, dependencies
├── uv.lock                   # Locked dependencies
├── openapi.yaml              # Obsidian API specification
├── README.md                 # User documentation
├── LICENSE                   # MIT License
├── .gitignore                # Python ignore patterns
├── .env.example              # Environment variable template
└── AGENTS.md                 # This file
```

## Resources

- **FastMCP Documentation:** https://github.com/jlowin/fastmcp
- **MCP Specification:** https://modelcontextprotocol.io/
- **Obsidian Local REST API Plugin:** https://github.com/coddingtonbear/obsidian-local-rest-api
- **openapi.yaml:** Complete API specification in this repo

## Quick Command Reference

```bash
# Clone repository
git clone https://github.com/sirtaj/mcp-obsidian.git
cd mcp-obsidian

# Installation
uv sync

# Run server (stdio mode for Claude Desktop)
uv run mcp-obsidian

# Run with HTTP for debugging
uv run mcp-obsidian --transport http --port 8080

# Type checking
uv run pyright mcp_obsidian/

# Run tests
uv run pytest

# Add dependency
uv add package-name

# Update dependencies
uv lock --upgrade
```

## Version History Notes

- **v0.2.1** (current): Modern fastmcp 2.0+ implementation
- **v0.1.x**: Legacy mcp library (deprecated)

This fork represents a complete modernization to fastmcp 2.0+. Do not attempt to use old mcp library patterns.

---

**Last Updated:** 2025-11-02
**Codebase Version:** 0.2.1
**FastMCP Version:** 2.11.2+
