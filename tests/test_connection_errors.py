"""
Tests for MCP server connection error handling.

This test suite covers various connection failure scenarios:
- Connection refused (wrong port/host)
- Invalid API key (401 Unauthorized)
- Timeout scenarios
- Network errors

These tests verify that the MCP server returns clear, actionable error messages
to clients when the Obsidian REST API is unavailable or misconfigured.
"""

import pytest
import os
from fastmcp import FastMCP
from mcp_obsidian.tools import mcp


class TestConnectionErrors:
    """Test error handling when MCP server cannot connect to Obsidian."""

    def test_connection_refused_wrong_port(self):
        """Test error message when Obsidian is not running on the specified port."""
        from mcp_obsidian.obsidian import Obsidian

        # Try to call a tool - should fail with connection error
        with pytest.raises(Exception) as exc_info:
            client = Obsidian(
                api_key="test-key",
                protocol="http",
                host="127.0.0.1",
                port=99999  # Port where nothing is listening
            )
            client.list_files_in_vault()

        error_msg = str(exc_info.value)
        # Should mention connection failure
        assert "Request failed" in error_msg or "Connection" in error_msg or "refused" in error_msg.lower()

    def test_connection_refused_wrong_host(self):
        """Test error message when Obsidian host is unreachable."""
        from mcp_obsidian.obsidian import Obsidian

        # Use a non-routable IP address (TEST-NET-1)
        with pytest.raises(Exception) as exc_info:
            client = Obsidian(
                api_key="test-key",
                protocol="http",
                host="192.0.2.1",  # Non-routable test IP
                port=27124
            )
            client.list_files_in_vault()

        error_msg = str(exc_info.value)
        assert "Request failed" in error_msg

    def test_invalid_api_key(self):
        """Test error message when API key is invalid."""
        from mcp_obsidian.obsidian import Obsidian

        # Use correct host/port but wrong API key
        with pytest.raises(Exception) as exc_info:
            client = Obsidian(
                api_key="invalid-api-key-12345",
                protocol="http",
                host="127.0.0.1",
                port=37123  # Test vault port
            )
            client.list_files_in_vault()

        error_msg = str(exc_info.value)
        # Should mention authentication/authorization error
        assert "Error" in error_msg
        # Common auth error codes: 401, 403, 40100-40199
        assert "401" in error_msg or "403" in error_msg or "40100" in error_msg or "Unauthorized" in error_msg

    def test_obsidian_not_running(self):
        """Test clear error message when Obsidian is not running at all."""
        from mcp_obsidian.obsidian import Obsidian

        # Use a port that's definitely not in use
        with pytest.raises(Exception) as exc_info:
            client = Obsidian(
                api_key="test-key",
                protocol="http",
                host="127.0.0.1",
                port=54321
            )
            client.list_files_in_vault()

        error_msg = str(exc_info.value)
        # Should indicate connection problem
        assert "Request failed" in error_msg
        assert len(error_msg) > 10  # Should have a descriptive message


class TestConnectionErrorMessages:
    """Test that error messages are clear and actionable."""

    def test_error_contains_connection_details(self):
        """Verify error messages help users diagnose the problem."""
        from mcp_obsidian.obsidian import Obsidian

        with pytest.raises(Exception) as exc_info:
            client = Obsidian(
                api_key="test-key",
                protocol="http",
                host="127.0.0.1",
                port=99999
            )
            client.list_files_in_vault()

        error_msg = str(exc_info.value)

        # Error should be informative
        assert len(error_msg) > 20
        # Should mention it's a request/connection issue
        assert "Request failed" in error_msg or "Connection" in error_msg

    def test_http_error_codes_preserved(self):
        """Verify HTTP error codes are preserved in error messages."""
        from mcp_obsidian.obsidian import Obsidian

        # Use correct connection but wrong API key to get HTTP 401
        with pytest.raises(Exception) as exc_info:
            client = Obsidian(
                api_key="wrong-key",
                protocol="http",
                host="127.0.0.1",
                port=37123
            )
            client.list_files_in_vault()

        error_msg = str(exc_info.value)
        # Should contain error code from Obsidian API
        assert "Error" in error_msg
        # Error code should be numeric
        assert any(char.isdigit() for char in error_msg)


class TestConnectionTimeout:
    """Test timeout handling."""

    def test_timeout_produces_clear_error(self):
        """Test that connection timeouts produce clear error messages."""
        from mcp_obsidian.obsidian import Obsidian

        # Use an IP that will timeout (black hole)
        with pytest.raises(Exception) as exc_info:
            client = Obsidian(
                api_key="test-key",
                protocol="http",
                host="192.0.2.1",  # TEST-NET-1, should timeout
                port=27124
            )
            client.list_files_in_vault()

        error_msg = str(exc_info.value)
        # Should mention request failure
        assert "Request failed" in error_msg
