# MCP Obsidian Server Test Suite

Comprehensive test suite for all 14 MCP tools provided by the Obsidian server.

## Test Environment Configuration

Tests automatically use a **dedicated test vault** to avoid interfering with your production vault:

- **Production vault**: Port 27123 (configured in `.env`)
- **Test vault**: Port 37123 (configured in `.env.test`)

When you run pytest, the tests will automatically connect to port 37123 (test vault). Your production vault on port 27123 remains untouched.

### Environment Files

- **`.env`** - Production configuration (port 27123)
- **`.env.test`** - Test configuration (port 37123) - automatically loaded by pytest
- **`.env.production`** - Backup of production configuration

## Test Coverage

### File Operations (6 tools)
- `test_list_files_in_vault` - List vault root contents
- `test_list_files_in_dir` - List directory contents
- `test_get_file_contents` - Read single file
- `test_batch_get_file_contents` - Read multiple files
- Plus error handling tests for non-existent paths

### Write Operations
- `test_put_content_create_new_file` - Create new files
- `test_put_content_overwrite_file` - Overwrite existing files
- `test_append_content` - Append to files

### Search Operations (2 tools)
- `test_simple_search` - Text search with parameterized queries
- `test_complex_search_glob` - JsonLogic glob patterns
- `test_complex_search_and_operator` - Complex queries with AND logic

### Periodic Notes (2 tools)
- `test_get_periodic_note_content` - Get current periodic notes (all periods)
- `test_get_periodic_note_metadata` - Get note metadata
- `test_get_recent_periodic_notes` - Get recent periodic notes

### Recent Changes (1 tool)
- `test_get_recent_changes` - Get recently modified files

### Delete Operations (1 tool)
- `test_delete_without_confirmation` - Safety check
- `test_delete_test_file` - Cleanup test files

### Integration Tests
- `test_create_search_delete_workflow` - End-to-end workflow

### Advanced File Operations (`test_file_operations.py`)

**Folder Operations (3 tests)**
- `test_create_file_in_nested_folder` - Create files in nested folder structures (auto-creates parent directories)
- `test_create_multiple_files_in_folder` - Create multiple files in the same folder
- `test_create_folder_hierarchy` - Create complex folder hierarchies with files at different levels

**File Edit Workflows (3 tests)**
- `test_create_edit_append_workflow` - Complete workflow: create → overwrite → append
- `test_incremental_content_building` - Build file content incrementally with multiple appends
- `test_patch_content_workflow` - SKIPPED (complex heading syntax requirements)

**File Move Workflows (3 tests)**
- `test_move_file_simulation` - Simulate file move via copy + delete
- `test_rename_file_simulation` - Simulate file rename in same directory
- `test_reorganize_multiple_files` - Move multiple files to new folder structure

**Cleanup (1 test)**
- `test_cleanup_test_folders` - Delete all test folders created during testing

## Running Tests

### Install Dependencies

```bash
# Add test dependencies
uv add --dev pytest pytest-asyncio
```

### Run All Tests

```bash
# Run full test suite (uses test vault on port 37123)
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_obsidian_tools.py
uv run pytest tests/test_file_operations.py

# Run specific test class
uv run pytest tests/test_obsidian_tools.py::TestFileOperations
uv run pytest tests/test_file_operations.py::TestFolderOperations

# Run specific test
uv run pytest tests/test_obsidian_tools.py::TestFileOperations::test_list_files_in_vault
uv run pytest tests/test_file_operations.py::TestFolderOperations::test_create_file_in_nested_folder
```

### Run Tests by Category

```bash
# Run only search tests
uv run pytest tests/test_obsidian_tools.py::TestSearchOperations

# Run integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"
```

### Debugging Tests

```bash
# Stop on first failure
uv run pytest -x

# Show local variables on failure
uv run pytest -l

# Show print statements
uv run pytest -s

# Run with Python debugger
uv run pytest --pdb
```

## Test Requirements

### Test Vault Setup

1. **Create a separate Obsidian vault** for testing
2. **Enable Local REST API plugin** in the test vault
3. **Configure the plugin** to listen on port **37123** (HTTP)
4. **Use the same API key** as your production vault (or update `.env.test`)

### Environment Variables

The test configuration (`.env.test`) should contain:
- `OBSIDIAN_API_KEY` - Your API key
- `OBSIDIAN_HOST` - Default: 172.17.0.1
- `OBSIDIAN_PORT` - **37123** (test vault port)
- `OBSIDIAN_PROTOCOL` - Default: http

### Verifying Test Environment

Before running tests, verify the test vault is accessible:

```bash
# Test connection to test vault
curl -H "Authorization: Bearer YOUR_API_KEY" http://172.17.0.1:37123/vault/

# Should return a list of files in your test vault
```

## Test Strategy

Tests use **in-memory testing** via FastMCP Client, which:
- Runs directly against the server code (no subprocess management)
- Uses real STDIO transport internally for maximum fidelity
- Provides fast test execution
- Requires no external MCP Inspector

## Fixtures

### `obsidian_client`
Async fixture providing a connected FastMCP Client for all tests.

### `vault_files`
Helper fixture that returns list of files in vault root, useful for tests that need to operate on existing files.

## Notes

- Tests create temporary files (`test-mcp-file.md`, `integration-test-file.md`) in the **test vault only**
- Advanced file operation tests create a `test-folders/` directory hierarchy with multiple test files
- Delete tests run last to clean up test files and folders
- The cleanup test (`test_cleanup_test_folders`) removes all test artifacts
- Some tests may skip if required resources don't exist in your test vault
- 404 errors from Obsidian API are handled gracefully in periodic note tests
- **Your production vault on port 27123 is never touched by tests**

## Switching Between Environments

### For Testing
Tests automatically use `.env.test` (port 37123)

### For Production Use
Regular server runs use `.env` (port 27123):
```bash
uv run mcp-obsidian
```

### Manual Environment Override
```bash
# Force use of test environment
cp .env.test .env
uv run mcp-obsidian

# Restore production environment
cp .env.production .env
uv run mcp-obsidian
```
