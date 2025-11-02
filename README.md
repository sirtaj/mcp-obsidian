# MCP Server for Obsidian

Access your Obsidian vault programmatically via Claude with support for search, batch operations, and content manipulation.

> **Fork**: This is a fork of [mcp-obsidian](https://github.com/MarkusPfundstein/mcp-obsidian) using [FastMCP 2.0+](https://github.com/jlowin/fastmcp). See installation instructions below to use this version.

## Quick Start

### 1. Install Obsidian Plugin

Install the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) community plugin:
- Obsidian → Settings → Community Plugins → Browse
- Search "Local REST API" → Install → Enable
- Copy your API key from the plugin settings

### 2. Configure Claude Desktop

Edit your Claude Desktop configuration file:

- **MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Add this configuration to install from this fork:

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
        "OBSIDIAN_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

> **Note**: This installs from the GitHub repository. If you want to use the original version instead, use `"args": ["mcp-obsidian"]`.
>
> **Tip**: If Claude can't find `uvx`, use the full path from `which uvx` (Linux/MacOS) or `where.exe uvx` (Windows).

### 3. Start Using It

Restart Claude Desktop and try:
- "List all files in my Obsidian vault"
- "Search for notes about machine learning"
- "Create a new note with today's meeting agenda"

## Key Features

### Batch Operations
Read or modify multiple files in one request with automatic error handling.

### Content Patching
Insert content relative to headings, blocks, or frontmatter without replacing entire files.

### Search Options
Multiple search methods available:
- Text search with relevance scores
- JsonLogic queries with regex and glob patterns
- Tag-based filtering with AND/OR logic
- Frontmatter field queries
- Folder search by name
- Omnisearch integration (optional): Fuzzy matching, PDF/image OCR support

### File Organization
Move, rename, or bulk-reorganize files with confirmation safeguards.

### Periodic Notes Support
Access daily, weekly, monthly, quarterly, and yearly notes (requires Periodic Notes plugin).

### Resources
Two MCP resources for efficient data access:
- `obsidian://vault/{filepath}/content` - File content only
- `obsidian://vault/{filepath}/metadata` - Complete metadata including frontmatter, tags, and file stats

## Common Use Cases

### Knowledge Extraction
```
"Find all notes mentioning 'API design' and summarize key patterns"
"Search my weekly reviews from the last month and identify recurring themes"
"Show me all notes tagged 'python' AND 'tutorial' with examples"
```

### Content Organization
```
"Create a new project note with frontmatter template"
"Append today's learnings to my daily note"
"Update the status field to 'completed' in project-x.md"
```

### Research & Analysis
```
"Search my vault for 'neural networks', rank by relevance"
"Find all PDFs about machine learning using Omnisearch"
"Show me notes modified in the last week that mention 'deadline'"
```

### Batch Processing
```
"Read all files in the 'Archive' folder and generate an index"
"Add a 'reviewed: true' field to all notes tagged 'needs-review'"
"Create summaries for each file in my weekly notes folder"
```

## Available Tools

### File Operations
- `obsidian_list_files_in_vault` - List vault root directory (supports recursive depth)
- `obsidian_list_files_in_dir` - List specific directory
- `obsidian_get_file_contents` - Read single file
- `obsidian_batch_get_file_contents` - Read multiple files
- `obsidian_append_content` - Append to file
- `obsidian_put_content` - Create or overwrite file
- `obsidian_delete_file` - Delete file or directory (requires confirmation)

### File Organization
- `obsidian_move_file` - Move or rename a file (requires confirmation)
- `obsidian_bulk_move_files` - Move or rename multiple files in one operation

### Content Analysis
- `obsidian_list_headings` - Extract headings from a file (filterable by level)

### Content Manipulation
- `obsidian_patch_content` - Insert content relative to headings, blocks, or frontmatter

### Search
- `obsidian_simple_search` - Text search with context and relevance scores
- `obsidian_complex_search` - JsonLogic queries with regex and glob support
- `obsidian_search_by_tags` - Filter by tags (AND/OR logic)
- `obsidian_search_by_frontmatter` - Query by metadata fields
- `obsidian_list_all_tags` - List all tags with usage counts
- `obsidian_search_folders` - Find folders by name
- `obsidian_omnisearch_search` - Fuzzy search with BM25 ranking (optional, requires Omnisearch plugin)

### Periodic Notes
- `obsidian_get_periodic_note` - Get current daily/weekly/monthly/quarterly/yearly note
- `obsidian_get_recent_periodic_notes` - Get recent periodic notes
- Requires the Periodic Notes plugin

### Recent Changes
- `obsidian_get_recent_changes` - Track recently modified files (requires Dataview plugin)

## Omnisearch Integration (Optional)

The [Omnisearch plugin](https://github.com/scambier/obsidian-omnisearch) provides additional search capabilities:

**Features:**
- Fuzzy matching (handles typos)
- BM25 relevance ranking
- PDF and image search with OCR
- Recency-based ranking
- Automatic fallback to standard search if unavailable

**Setup:**
1. Install Omnisearch plugin in Obsidian
2. Enable "HTTP Server" in plugin settings (default port: 51361)
3. Add to your config:
```json
"env": {
  "OBSIDIAN_API_KEY": "your_key",
  "OMNISEARCH_ENABLED": "true"
}
```

**Advanced Syntax:**
```
path:"Work/Projects" deadline          # Search specific folder
"machine learning" -basics             # Exact phrase, exclude word
ext:pdf neural networks                # Search PDFs only
path:"Archive" ext:md todo -done       # Complex filters
```

**Use Cases:**
- Omnisearch: Typo-tolerant search, PDFs, fuzzy matching
- Simple Search: Exact text matching
- Complex Search: JsonLogic queries, regex patterns
- Tag/Frontmatter Search: Metadata filtering

## Configuration Reference

### Required
- `OBSIDIAN_API_KEY` - From Local REST API plugin settings

### Optional
| Variable | Default | Description |
|----------|---------|-------------|
| `OBSIDIAN_HOST` | `127.0.0.1` | Obsidian server host |
| `OBSIDIAN_PORT` | `27124` | Obsidian server port |
| `OBSIDIAN_PROTOCOL` | `https` | `http` or `https` |
| `OMNISEARCH_ENABLED` | `false` | Enable Omnisearch integration |
| `OMNISEARCH_HOST` | Same as `OBSIDIAN_HOST` | Omnisearch server (can be different) |
| `OMNISEARCH_PORT` | `51361` | Omnisearch HTTP server port |
| `OMNISEARCH_PROTOCOL` | `http` | Usually `http` |

### Configuration Methods

**Method 1: MCP Config** (Recommended)
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
        "OBSIDIAN_API_KEY": "your_key",
        "OBSIDIAN_PORT": "27124",
        "OMNISEARCH_ENABLED": "true"
      }
    }
  }
}
```

**Method 2: .env File**
```bash
OBSIDIAN_API_KEY=your_key
OBSIDIAN_HOST=127.0.0.1
OMNISEARCH_ENABLED=true
```

## Example Prompts

### Basic Operations
```
"List all files in my vault"
"Show me the contents of my daily note"
"Create a new note called 'ideas.md' with a bullet list"
```

### Search
```
"Search for 'API design patterns' and show relevance scores"
"Find notes tagged 'project' AND 'urgent'"
"Show all notes with status='in-progress' in frontmatter"
"Which notes were modified in the last 3 days?"
```

### Content Operations
```
"Read my last 3 weekly notes and create a monthly summary"
"Add a new task under '## TODO' in my project note"
"Append today's learnings to my daily note"
"Find all meeting notes and extract action items"
```

### Batch Operations
```
"Use Omnisearch to find 'quantum computing' with fuzzy matching"
"Search PDFs for 'neural networks' using Omnisearch"
"Batch read all files in 'Projects' and create an index"
"Find folders named 'archive' only in my Notes directory"
```

## For Developers

### Installation from Source

```bash
# Clone the repository
git clone https://github.com/sirtaj/mcp-obsidian.git
cd mcp-obsidian

# Install dependencies
uv sync
```

### Running Locally

```bash
# Run with stdio (for Claude Desktop)
uv run mcp-obsidian

# Run with HTTP for debugging
uv run mcp-obsidian --transport http --port 8080

# Run with SSE
uv run mcp-obsidian --transport sse --port 8080
```

### Claude Desktop Config for Local Development

Edit your Claude Desktop config file (see paths above) and use:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-obsidian",
        "run",
        "mcp-obsidian"
      ],
      "env": {
        "OBSIDIAN_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Testing

Uses a separate test vault (port 37123) to avoid interfering with production:

```bash
# Configure test vault in .env.test
OBSIDIAN_API_KEY=your_test_key
OBSIDIAN_PORT=37123

# Run tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific tests
uv run pytest tests/test_obsidian_tools.py::TestSearchOperations
```

See [tests/README.md](tests/README.md) for detailed test documentation.

### Debugging

Use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) for debugging:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-obsidian run mcp-obsidian
```

Or watch server logs:

```bash
# MacOS
tail -n 20 -f ~/Library/Logs/Claude/mcp-server-obsidian.log

# Linux
tail -n 20 -f ~/.config/Claude/logs/mcp-server-obsidian.log

# Windows (PowerShell)
Get-Content -Path "$env:APPDATA\Claude\logs\mcp-server-obsidian.log" -Tail 20 -Wait
```

### Architecture

See [AGENTS.md](AGENTS.md) for:
- Detailed architecture documentation
- Code organization and patterns
- Contribution guidelines
- Adding new tools and features

## Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Obsidian Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api)
- [Omnisearch Plugin](https://github.com/scambier/obsidian-omnisearch)

## License

MIT License - see [LICENSE](LICENSE) file for details.
