"""
Quick validation script to inspect actual tool response formats.
Run this to see exactly what data structure each tool returns.
"""

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport


async def test_list_files_format(obsidian_client: Client[FastMCPTransport]):
    """Validate list_files_in_vault returns correct format."""
    result = await obsidian_client.call_tool(
        name="obsidian_list_files_in_vault",
        arguments={}
    )

    print("\n=== list_files_in_vault ===")
    print(f"Type: {type(result.data)}")
    print(f"Keys: {result.data.keys()}")
    print(f"Files (first 3): {result.data['files'][:3]}")
    print(f"Directories (first 3): {result.data['directories'][:3]}")

    assert isinstance(result.data, dict)
    assert "files" in result.data
    assert "directories" in result.data
    assert isinstance(result.data["files"], list)
    assert isinstance(result.data["directories"], list)
    assert all(isinstance(item, str) for item in result.data["files"])
    assert all(isinstance(item, str) for item in result.data["directories"])
    print("✅ PASS: Returns dict with 'files' and 'directories' arrays")


async def test_get_file_format(obsidian_client: Client[FastMCPTransport], vault_files):
    """Validate get_file_contents returns correct format."""
    md_files = [f for f in vault_files if f.endswith('.md')]
    if not md_files:
        pytest.skip("No markdown files")

    result = await obsidian_client.call_tool(
        name="obsidian_get_file_contents",
        arguments={"filepath": md_files[0]}
    )

    print("\n=== get_file_contents ===")
    print(f"Type: {type(result.data)}")
    print(f"Data length: {len(result.data)} chars")
    print(f"First 100 chars: {result.data[:100]}")

    assert isinstance(result.data, str)
    print("✅ PASS: Returns string")


async def test_simple_search_format(obsidian_client: Client[FastMCPTransport]):
    """Validate simple_search returns correct format and show how to access data."""
    result = await obsidian_client.call_tool(
        name="obsidian_simple_search",
        arguments={"query": "test", "context_length": 100}
    )

    print("\n=== simple_search ===")
    print(f"result.data type: {type(result.data)}")
    print(f"result.data: {result.data}")

    # Check structured_content which has the parsed data
    if hasattr(result, 'structured_content') and result.structured_content:
        print(f"\nstructured_content type: {type(result.structured_content)}")
        print(f"structured_content keys: {result.structured_content.keys()}")

        if 'result' in result.structured_content:
            actual_results = result.structured_content['result']
            print(f"\nActual results type: {type(actual_results)}")
            print(f"Number of results: {len(actual_results)}")

            if len(actual_results) > 0:
                print("\nFirst result structure:")
                print(f"  Keys: {actual_results[0].keys()}")
                print(f"  Filename: {actual_results[0].get('filename')}")
                print(f"  Score: {actual_results[0].get('score')}")
                print(f"  Matches: {len(actual_results[0].get('matches', []))}")

            print("✅ PASS: Search returns list of dicts in structured_content['result']")
        else:
            print("⚠️ No 'result' key in structured_content")
    else:
        print("⚠️ No structured_content")


async def test_complex_search_format(obsidian_client: Client[FastMCPTransport]):
    """Validate complex_search returns correct format."""
    query = {"glob": ["*.md", {"var": "path"}]}

    result = await obsidian_client.call_tool(
        name="obsidian_complex_search",
        arguments={"query": query}
    )

    print("\n=== complex_search ===")
    print(f"Type: {type(result.data)}")
    print(f"Number of results: {len(result.data)}")

    if len(result.data) > 0:
        print(f"First result: {result.data[0]}")

    assert isinstance(result.data, list)
    print("✅ PASS: Returns list")


async def test_recent_changes_format(obsidian_client: Client[FastMCPTransport]):
    """Validate get_recent_changes returns correct format."""
    try:
        result = await obsidian_client.call_tool(
            name="obsidian_get_recent_changes",
            arguments={"limit": 5, "days": 30}
        )

        print("\n=== get_recent_changes ===")
        print(f"Type: {type(result.data)}")
        print(f"Number of results: {len(result.data)}")

        if len(result.data) > 0:
            print(f"First result keys: {result.data[0].keys() if isinstance(result.data[0], dict) else 'not a dict'}")
            print(f"First result: {result.data[0]}")

        assert isinstance(result.data, list)
        print("✅ PASS: Returns list")
    except Exception as e:
        # 40070 indicates Dataview plugin not installed
        if "40070" not in str(e):
            raise
        pytest.skip("Recent changes format test skipped: Dataview plugin not installed in test vault")


@pytest.fixture
async def vault_files(obsidian_client: Client[FastMCPTransport]) -> list[str]:
    """Helper fixture to get vault files."""
    result = await obsidian_client.call_tool(
        name="obsidian_list_files_in_vault",
        arguments={}
    )
    return result.data["files"]
