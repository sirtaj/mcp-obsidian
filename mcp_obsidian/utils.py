"""Utility functions for mcp-obsidian.

This module contains shared helper functions used across multiple tools,
following the DRY (Don't Repeat Yourself) principle.
"""

from typing import Any, Dict, List
from . import constants


def separate_files_and_directories(items: List[str]) -> Dict[str, List[str]]:
    """Separate a list of items into files and directories.

    Args:
        items: List of file and directory paths (directories end with '/')

    Returns:
        Dictionary with 'files' and 'directories' keys
    """
    files = [item for item in items if not item.endswith("/")]
    directories = [item.rstrip("/") for item in items if item.endswith("/")]

    return {"files": files, "directories": directories}


def format_search_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format search results from Obsidian API to standardized structure.

    Args:
        results: Raw search results from Obsidian API

    Returns:
        Formatted search results with consistent structure
    """
    formatted_results = []

    for result in results:
        formatted_matches = []
        for match in result.get("matches", []):
            context = match.get("context", "")
            match_pos = match.get("match", {})
            start = match_pos.get("start", 0)
            end = match_pos.get("end", 0)
            formatted_matches.append(
                {"context": context, "match_position": {"start": start, "end": end}}
            )

        formatted_results.append(
            {
                "filename": result.get("filename", ""),
                "score": result.get("score", 0),
                "matches": formatted_matches,
            }
        )

    return formatted_results


def add_fallback_indicator(
    results: List[Dict[str, Any]],
    message: str = "Used Obsidian simple_search (Omnisearch unavailable)",
) -> List[Dict[str, Any]]:
    """Add fallback indicator to search results.

    Args:
        results: Search results to annotate
        message: Fallback message to add

    Returns:
        Results with '_fallback' field added to each item
    """
    for result in results:
        result["_fallback"] = message
    return results


def validate_period_type(period: str) -> None:
    """Validate period type for periodic notes.

    Args:
        period: Period type to validate

    Raises:
        RuntimeError: If period type is invalid
    """
    if period not in constants.VALID_PERIOD_TYPES:
        raise RuntimeError(
            f"Invalid period: {period}. "
            f"Must be one of: {', '.join(constants.VALID_PERIOD_TYPES)}"
        )


def validate_note_type(note_type: str) -> None:
    """Validate note type for periodic notes.

    Args:
        note_type: Note type to validate

    Raises:
        RuntimeError: If note type is invalid
    """
    if note_type not in constants.VALID_PERIODIC_NOTE_TYPES:
        raise RuntimeError(
            f"Invalid type: {note_type}. "
            f"Must be one of: {', '.join(constants.VALID_PERIODIC_NOTE_TYPES)}"
        )


def validate_positive_integer(value: Any, name: str) -> None:
    """Validate that a value is a positive integer.

    Args:
        value: Value to validate
        name: Name of the parameter (for error messages)

    Raises:
        RuntimeError: If value is not a positive integer
    """
    if not isinstance(value, int) or value < 1:
        raise RuntimeError(f"Invalid {name}: {value}. Must be a positive integer")


def validate_boolean(value: Any, name: str) -> None:
    """Validate that a value is a boolean.

    Args:
        value: Value to validate
        name: Name of the parameter (for error messages)

    Raises:
        RuntimeError: If value is not a boolean
    """
    if not isinstance(value, bool):
        raise RuntimeError(f"Invalid {name}: {value}. Must be a boolean")
