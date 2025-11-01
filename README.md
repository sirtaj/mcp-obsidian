# MCP server for Obsidian

MCP server to interact with Obsidian via the Local REST API community plugin.

## THIS FORK

**NOTE**: This is a fork that uses fastmcp instead of the old mcp library.


### Running

```shell
mcp-obsidian --transport http --host 127.0.0.1 --port 37123
```

Transport options are http, sse and stdio (the default). transport and port
are optional and unused for stdio.

The old README follows for historical purposes.

## Components

### Tools

The server implements 18 tools by default (19 with optional Omnisearch integration) organized into 6 categories:

#### File Operations (6 tools)

- **obsidian_list_files_in_vault**: Lists all files and directories in the root directory of your vault. Returns a structured object with separate `files` and `directories` arrays.
- **obsidian_list_files_in_dir**: Lists all files and directories in a specific directory. Returns a structured object with separate `files` and `directories` arrays.
- **obsidian_get_file_contents**: Returns the content of a single file in your vault.
- **obsidian_batch_get_file_contents**: Returns the contents of multiple files as a structured array with path, content, and success status for each file.
- **obsidian_append_content**: Appends content to the end of an existing file, or creates a new file if it doesn't exist. Automatically creates parent directories if needed.
- **obsidian_put_content**: Creates a new file or overwrites an existing file with specified content. Automatically creates parent directories if needed.

#### Content Patching (1 tool)

- **obsidian_patch_content**: Inserts content into an existing note relative to a heading, block reference, or frontmatter field. Supports `append`, `prepend`, and `replace` operations.

#### File Deletion (1 tool)

- **obsidian_delete_file**: Deletes a file or directory from your vault. Requires explicit confirmation (`confirm=True`) to prevent accidental deletions.

#### Search Operations (6-7 tools)

- **obsidian_simple_search**: Simple text search across all files in the vault. Returns structured results with filename, relevance score, and match context with positions.
- **obsidian_complex_search**: Advanced search using JsonLogic queries. Supports glob patterns, regex, and complex AND/OR logic.
- **obsidian_search_by_tags**: Searches for files containing specified tags. Supports both AND logic (files must have ALL tags) and OR logic (files with ANY tag match).
- **obsidian_search_by_frontmatter**: Searches files by YAML frontmatter field values. Supports `equals`, `contains`, and `exists` operators.
- **obsidian_list_all_tags**: Returns all unique tags in the vault with usage counts (number of files using each tag).
- **obsidian_search_folders**: Recursively searches for folders by name using case-insensitive substring matching. Optionally specify a root path to limit search scope.
- **obsidian_omnisearch_search** (optional): Advanced full-text search using Omnisearch plugin with fuzzy matching, BM25 relevance scoring, OCR support, PDF indexing, and recency boosting. Requires Omnisearch plugin with HTTP server enabled.

#### Periodic Notes (2 tools)

- **obsidian_get_periodic_note**: Gets the current periodic note for a specified period (daily, weekly, monthly, quarterly, yearly). Returns either content or metadata. Requires the Periodic Notes plugin.
- **obsidian_get_recent_periodic_notes**: Gets the most recent periodic notes for a specified period type. Optionally includes note content. Requires the Periodic Notes plugin.

#### Recent Changes (1 tool)

- **obsidian_get_recent_changes**: Gets recently modified files in the vault with their modification times. Requires the Dataview plugin.

### Resources

The server provides 2 MCP resources for read-only data access:

- **obsidian://vault/{filepath}/metadata**: Complete file metadata including content, frontmatter, tags, and file statistics (ctime, mtime, size). Returns a JSON object with all metadata fields.
- **obsidian://vault/{filepath}/content**: File content only as plain text. More efficient than `/metadata` when you don't need frontmatter, tags, or statistics.

**When to use each:**
- Use `/content` when you only need the file text
- Use `/metadata` when you need any metadata (frontmatter, tags, stats) or multiple fields
- Extract specific fields client-side: `metadata['frontmatter']`, `metadata['tags']`, `metadata['stat']`

### Example Prompts

It's good to first instruct Claude to use Obsidian, then it will always call the tool.

#### Basic Operations
- "Get the contents of the last architecture call note and summarize them"
- "Create a new note called 'meeting-notes.md' with today's agenda"
- "List all files in the 'Projects' directory"

#### Search & Discovery
- "Search for all files where Azure CosmosDb is mentioned and quickly explain to me the context"
- "Find all notes tagged with 'project' and 'urgent'"
- "Show me all notes that have a 'status' field set to 'in-progress' in their frontmatter"
- "List all tags in my vault and show me the most popular ones"
- "Find all folders with 'project' in their name"
- "Search for folders named 'archive' only in my Notes directory"

#### Advanced Workflows
- "Summarize the last meeting notes and put them into a new note 'summary-meeting.md'. Add an introduction so I can send it via email"
- "Find all files with the 'weekly-review' tag, read their content, and create a summary in a new note"
- "Show me all notes modified in the last 7 days"
- "Get my current daily note and append a new task to it"

#### Metadata & Organization
- "Find all notes that mention 'API' and have a 'priority' field in their frontmatter"
- "Show me the frontmatter of my project notes to understand what fields I'm using"
- "List all files tagged with both 'python' AND 'tutorial'"

## Omnisearch Integration (Optional)

The server supports optional integration with the [Omnisearch plugin](https://github.com/scambier/obsidian-omnisearch), providing advanced search capabilities beyond the standard Obsidian Local REST API search.

### Features

When enabled, the `obsidian_omnisearch_search` tool provides:

- **Fuzzy Matching**: Typo-tolerant searches that find content even with spelling variations
- **BM25 Relevance Scoring**: Industry-standard ranking algorithm for better result ordering
- **OCR Support**: Search text within images (if OCR enabled in Omnisearch)
- **PDF Indexing**: Search within PDF files stored in your vault
- **Recency Boosting**: Recently modified files ranked higher in results
- **Intelligent Tokenization**: Better handling of compound words and technical terms
- **Automatic Fallback**: If Omnisearch is unavailable, automatically falls back to `obsidian_simple_search`

### Graceful Degradation

The Omnisearch integration is designed to fail gracefully. If the Omnisearch HTTP server is unavailable or unreachable, the tool will automatically fall back to the standard `obsidian_simple_search` functionality. When fallback occurs:

- Search results will still be returned using the regular Obsidian search
- A `_fallback` field will be added to each result indicating fallback was used
- The server continues to function normally without errors

This allows you to configure Omnisearch on a separate host or disable it temporarily without breaking your workflow.

### Setup

1. **Install Omnisearch Plugin**
   - In Obsidian: Settings > Community Plugins > Browse
   - Search for "Omnisearch" and install
   - Enable the plugin

2. **Enable HTTP Server**
   - In Obsidian: Settings > Omnisearch
   - Enable "HTTP Server" option
   - Note the port (default: 51361)

3. **Configure Environment Variables**
   ```bash
   # In your .env file or MCP client config
   OMNISEARCH_ENABLED=true
   OMNISEARCH_PORT=51361      # Use your Omnisearch port
   OMNISEARCH_PROTOCOL=http
   ```

4. **Restart MCP Server**
   - The Omnisearch tool will be automatically registered when enabled

### When to Use Omnisearch vs. Simple Search

| Use Case | Recommended Tool |
|----------|------------------|
| Exact text matching | `obsidian_simple_search` |
| Searching with typos/variations | `obsidian_omnisearch_search` |
| Complex JsonLogic queries | `obsidian_complex_search` |
| Tag-based filtering | `obsidian_search_by_tags` |
| Frontmatter queries | `obsidian_search_by_frontmatter` |
| Searching PDFs/images | `obsidian_omnisearch_search` |
| Best relevance ranking | `obsidian_omnisearch_search` |

### Search Syntax & Tips

Omnisearch supports advanced query syntax for precise searches:

**Operators:**
- `path:"folder/path"` - Restrict results to specific directory
- `ext:"md pdf"` or `ext:md` or `.md` - Filter by file type(s)
- `"exact phrase"` - Match precise multi-word expressions
- `-excluded` - Exclude notes containing specific words

**Query Best Practices:**
- Best queries use spontaneous words that come to mind
- Use words from filenames, titles, or unique terminology
- Titles and headings are weighted more than body text
- Omnisearch automatically handles typos and variations

**Example Queries:**
```
meeting notes 2024                      # Simple search
path:"Work/Projects" deadline           # Search in specific folder
"machine learning" -basics              # Exact phrase, exclude basics
ext:pdf neural networks                 # Search only PDFs
path:"Archive" ext:md todo -done        # Complex filter
```

### Example Prompts with Omnisearch

- "Use Omnisearch to find notes about 'machne learning' (even with typo)"
- "Search for 'quantum computing' and rank by relevance using Omnisearch"
- "Find all references to 'API' in my PDFs using Omnisearch"
- "Search path:'Projects' for deadline with Omnisearch"
- "Use Omnisearch to find 'neural networks' excluding 'basics'"

## Configuration

### Environment Variables

The server supports configuration via environment variables. There are two ways to configure them:

#### Method 1: Server Config (Preferred)

Add environment variables to your MCP client configuration:

```json
{
  "mcp-obsidian": {
    "command": "uvx",
    "args": [
      "mcp-obsidian"
    ],
    "env": {
      "OBSIDIAN_API_KEY": "<your_api_key_here>",
      "OBSIDIAN_HOST": "127.0.0.1",
      "OBSIDIAN_PORT": "27124",
      "OBSIDIAN_PROTOCOL": "https"
    }
  }
}
```

**Note**: Sometimes Claude has issues detecting the location of `uv`/`uvx`. You can use `which uvx` to find and paste the full path in the above config.

#### Method 2: .env File

Create a `.env` file in the working directory:

```bash
OBSIDIAN_API_KEY=your_api_key_here
OBSIDIAN_HOST=127.0.0.1
OBSIDIAN_PORT=27124
OBSIDIAN_PROTOCOL=https
```

The server uses `python-dotenv` to automatically load environment variables from `.env` files.

### Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OBSIDIAN_API_KEY` | **Yes** | - | Bearer token from the Obsidian Local REST API plugin. Find this in the plugin settings. |
| `OBSIDIAN_HOST` | No | `127.0.0.1` | Host where Obsidian Local REST API is running. |
| `OBSIDIAN_PORT` | No | `27124` | Port where Obsidian Local REST API is listening. |
| `OBSIDIAN_PROTOCOL` | No | `https` | Protocol to use (`http` or `https`). The plugin uses self-signed certs for HTTPS. |
| `OMNISEARCH_ENABLED` | No | `false` | Set to `true` to enable Omnisearch integration. Requires Omnisearch plugin with HTTP server. |
| `OMNISEARCH_HOST` | No | Same as `OBSIDIAN_HOST` | Host where Omnisearch HTTP server is running. Can be different from `OBSIDIAN_HOST` if running on a separate machine. |
| `OMNISEARCH_PORT` | No | `51361` | Port where Omnisearch HTTP server is listening. |
| `OMNISEARCH_PROTOCOL` | No | `http` | Protocol for Omnisearch HTTP server (typically `http`). |

## Quickstart

### Install

#### Obsidian REST API

You need the Obsidian REST API community plugin running: https://github.com/coddingtonbear/obsidian-local-rest-api

Install and enable it in the settings and copy the api key.

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  
```json
{
  "mcpServers": {
    "mcp-obsidian": {
      "command": "uv",
      "args": [
        "--directory",
        "<dir_to>/mcp-obsidian",
        "run",
        "mcp-obsidian"
      ],
      "env": {
        "OBSIDIAN_API_KEY": "<your_api_key_here>",
        "OBSIDIAN_HOST": "<your_obsidian_host>",
        "OBSIDIAN_PORT": "<your_obsidian_port>"
      }
    }
  }
}
```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  
```json
{
  "mcpServers": {
    "mcp-obsidian": {
      "command": "uvx",
      "args": [
        "mcp-obsidian"
      ],
      "env": {
        "OBSIDIAN_API_KEY": "<YOUR_OBSIDIAN_API_KEY>",
        "OBSIDIAN_HOST": "<your_obsidian_host>",
        "OBSIDIAN_PORT": "<your_obsidian_port>"
      }
    }
  }
}
```
</details>

## Testing

This project includes a comprehensive test suite covering all 18 tools and 2 resources.

### Test Environment Setup

Tests use a **dedicated test vault** to avoid interfering with your production vault:

- **Production vault**: Port 27124 (default, configured in `.env`)
- **Test vault**: Port 37123 (configured in `.env.test`)

To set up testing:

1. Create a separate Obsidian vault for testing
2. Enable the Local REST API plugin in the test vault
3. Configure the plugin to listen on port **37123**
4. Create a `.env.test` file with your test configuration:

```bash
OBSIDIAN_API_KEY=your_api_key_here
OBSIDIAN_HOST=127.0.0.1
OBSIDIAN_PORT=37123
OBSIDIAN_PROTOCOL=http
```

### Running Tests

```bash
# Install test dependencies
uv add --dev pytest pytest-asyncio

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_obsidian_tools.py
uv run pytest tests/test_metadata_search.py

# Run specific test category
uv run pytest tests/test_obsidian_tools.py::TestSearchOperations
```

### Test Coverage

The test suite includes:
- **File operations tests**: List, read, write, append, batch operations
- **Search operation tests**: Simple search, complex queries, tag search, frontmatter search, folder search
- **Resource tests**: Both MCP resources (metadata and content)
- **Periodic notes tests**: Current and recent periodic notes
- **Advanced file operations**: Nested folders, file workflows, simulated move/rename
- **Folder search tests**: Case-insensitive search, substring matching, scoped search
- **Integration tests**: Complete workflows combining multiple tools

See [tests/README.md](tests/README.md) for detailed test documentation.

## Development

### Building

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-obsidian run mcp-obsidian
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

You can also watch the server logs with this command:

```bash
tail -n 20 -f ~/Library/Logs/Claude/mcp-server-mcp-obsidian.log
```
