"""Constants for mcp-obsidian.

This module contains all configuration constants and magic numbers
used throughout the application. Following the guideline to avoid
magic numbers by using descriptive, named constants.
"""

# ==============================================================================
# Obsidian REST API Configuration
# ==============================================================================

DEFAULT_OBSIDIAN_HOST = "127.0.0.1"
DEFAULT_OBSIDIAN_PORT = 27124
DEFAULT_OBSIDIAN_PROTOCOL = "https"

# Connection timeouts in seconds
CONNECTION_TIMEOUT_SECONDS = 3
READ_TIMEOUT_SECONDS = 6
DEFAULT_TIMEOUT = (CONNECTION_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS)

# SSL verification disabled for self-signed certificates
OBSIDIAN_SSL_VERIFY = False

# ==============================================================================
# Omnisearch Plugin Configuration
# ==============================================================================

DEFAULT_OMNISEARCH_HOST = "127.0.0.1"
DEFAULT_OMNISEARCH_PORT = 51361
DEFAULT_OMNISEARCH_PROTOCOL = "http"

# ==============================================================================
# MCP Server Configuration
# ==============================================================================

DEFAULT_MCP_SERVER_PORT = 37123

# ==============================================================================
# Search Configuration
# ==============================================================================

# Default context length for simple search results
SEARCH_DEFAULT_CONTEXT_LENGTH = 100

# ==============================================================================
# Periodic Notes Configuration
# ==============================================================================

# Valid period types for periodic notes
VALID_PERIOD_TYPES = ["daily", "weekly", "monthly", "quarterly", "yearly"]

# Valid data types for periodic notes
VALID_PERIODIC_NOTE_TYPES = ["content", "metadata"]

# Default number of periodic notes to retrieve
PERIODIC_NOTES_DEFAULT_LIMIT = 5

# ==============================================================================
# Recent Changes Configuration
# ==============================================================================

# Default number of recent changes to return
RECENT_CHANGES_DEFAULT_LIMIT = 10

# Default time window for recent changes (in days)
RECENT_CHANGES_DEFAULT_DAYS = 90

# ==============================================================================
# Frontmatter Search Configuration
# ==============================================================================

# Valid operators for frontmatter search
VALID_FRONTMATTER_OPERATORS = ["equals", "contains", "exists"]

# ==============================================================================
# Tool Names (for consistent reference)
# ==============================================================================
# Note: FastMCP defaults tool names to function names, so explicit name
# constants are only needed when the tool name differs from the function name.
