"""Pytest configuration and fixtures for MCP Obsidian Server tests."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load test environment configuration BEFORE importing mcp_obsidian modules
# This ensures tests use the test vault (port 37123) instead of production vault
test_env_path = Path(__file__).parent.parent / '.env.test'
if test_env_path.exists():
    load_dotenv(test_env_path, override=True)
    print(f"✓ Loaded test environment from {test_env_path}")
    print(f"  OBSIDIAN_PORT: {os.getenv('OBSIDIAN_PORT')}")
    print(f"  OBSIDIAN_HOST: {os.getenv('OBSIDIAN_HOST')}")
else:
    print(f"⚠ Test environment file not found: {test_env_path}")
    print("  Tests will use production environment from .env")

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport
from mcp_obsidian.tools import mcp


@pytest.fixture
async def obsidian_client():
    """
    Create an in-memory test client for the Obsidian MCP server.

    This fixture provides a FastMCP Client that connects directly to the server
    in-memory using the stdio transport, allowing fast and reliable testing
    without external dependencies.

    Yields:
        Client: A connected MCP client for testing tools
    """
    async with Client(transport=mcp) as client:
        yield client


@pytest.fixture
async def vault_files(obsidian_client: Client[FastMCPTransport]) -> list[str]:
    """
    Get the list of files in the vault root for use in other tests.

    This is a helper fixture that can be used by tests that need to operate
    on existing files in the vault.

    Args:
        obsidian_client: The MCP client fixture

    Returns:
        List of file/directory names in vault root
    """
    result = await obsidian_client.call_tool(
        name="obsidian_list_files_in_vault",
        arguments={}
    )
    return result.data
