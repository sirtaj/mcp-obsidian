import argparse
from .tools import mcp


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
        default="127.0.0.1",
        help="The host address for the MCP HTTP server.",
    )
    parser.add_argument(
        "--port", type=int, default=37123, help="The port for the MCP HTTP server."
    )
    args = parser.parse_args()

    run_args = {
        "transport": args.transport,
    }
    if args.transport != "stdio":
        run_args["host"] = args.host
        run_args["port"] = args.port

    mcp.run(**run_args)


# Optionally expose other important items at package level
__all__ = ["main"]

if __name__ == "__main__":
    main()
