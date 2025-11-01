"""Configuration management for mcp-obsidian.

This module centralizes environment variable loading and configuration
management, following the single responsibility principle.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv
from . import constants

# Load environment variables from .env file once at module level
load_dotenv()


@dataclass(frozen=True)
class ObsidianConfig:
    """Configuration for Obsidian REST API connection."""

    api_key: str
    host: str
    port: int
    protocol: str


@dataclass(frozen=True)
class OmnisearchConfig:
    """Configuration for Omnisearch plugin connection."""

    enabled: bool
    host: str
    port: int
    protocol: str


def get_obsidian_config() -> ObsidianConfig:
    """Load and validate Obsidian REST API configuration from environment.

    Returns:
        ObsidianConfig instance with validated configuration

    Raises:
        ValueError: If OBSIDIAN_API_KEY is not set
    """
    api_key = os.getenv("OBSIDIAN_API_KEY", "")
    if not api_key:
        raise ValueError(
            f"OBSIDIAN_API_KEY environment variable required. "
            f"Working directory: {os.getcwd()}"
        )

    host = os.getenv("OBSIDIAN_HOST", constants.DEFAULT_OBSIDIAN_HOST)
    port = int(os.getenv("OBSIDIAN_PORT", str(constants.DEFAULT_OBSIDIAN_PORT)))
    protocol = os.getenv("OBSIDIAN_PROTOCOL", constants.DEFAULT_OBSIDIAN_PROTOCOL)

    return ObsidianConfig(api_key=api_key, host=host, port=port, protocol=protocol)


def get_omnisearch_config(obsidian_host: str) -> OmnisearchConfig:
    """Load Omnisearch plugin configuration from environment.

    Args:
        obsidian_host: Host from Obsidian config to use as default

    Returns:
        OmnisearchConfig instance with configuration
    """
    enabled = os.getenv("OMNISEARCH_ENABLED", "false").lower() == "true"
    host = os.getenv("OMNISEARCH_HOST", obsidian_host)
    port = int(os.getenv("OMNISEARCH_PORT", str(constants.DEFAULT_OMNISEARCH_PORT)))
    protocol = os.getenv("OMNISEARCH_PROTOCOL", constants.DEFAULT_OMNISEARCH_PROTOCOL)

    return OmnisearchConfig(enabled=enabled, host=host, port=port, protocol=protocol)
