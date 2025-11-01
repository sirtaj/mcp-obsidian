import argparse
import logging
from typing import Literal, cast
from .tools import mcp
from . import constants

# Type alias for transport modes
Transport = Literal["stdio", "http", "sse"]


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description="Run the MCP Obsidian server.")
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "http", "sse"],
        help="The transport method for the MCP server (stdio, sse or http).",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=constants.DEFAULT_OBSIDIAN_HOST,
        help="The host address for the MCP HTTP server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=constants.DEFAULT_MCP_SERVER_PORT,
        help="The port for the MCP HTTP server.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging output.",
    )
    args = parser.parse_args()

    # Configure logging based on debug flag
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.debug:
        logging.info("Debug logging enabled")
        logging.debug(f"Starting MCP server with transport={args.transport}")
        if args.transport != "stdio":
            logging.debug(f"Server will listen on {args.host}:{args.port}")

    # Cast transport to proper type for type checker
    transport = cast(Transport, args.transport)

    run_args: dict = {
        "transport": transport,
    }
    if transport != "stdio":
        run_args["host"] = args.host
        run_args["port"] = args.port

    mcp.run(**run_args)


# Optionally expose other important items at package level
__all__ = ["main"]

if __name__ == "__main__":
    main()
