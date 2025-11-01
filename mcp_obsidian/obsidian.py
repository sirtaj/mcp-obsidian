import requests
import urllib.parse
from typing import Any
from . import constants


class Obsidian:
    def __init__(
        self,
        api_key: str,
        protocol: str = constants.DEFAULT_OBSIDIAN_PROTOCOL,
        host: str = constants.DEFAULT_OBSIDIAN_HOST,
        port: int = constants.DEFAULT_OBSIDIAN_PORT,
        verify_ssl: bool = constants.OBSIDIAN_SSL_VERIFY,
    ):
        self.api_key = api_key

        if protocol == "http":
            self.protocol = "http"
        else:
            self.protocol = (
                "https"  # Default to https for any other value, including 'https'
            )

        self.host = host
        self.port = port
        self.verify_ssl = verify_ssl
        self.timeout = constants.DEFAULT_TIMEOUT

    def get_base_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    def _get_headers(self) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return headers

    def _safe_call(self, f) -> Any:
        try:
            return f()
        except requests.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            code = error_data.get("errorCode", -1)
            message = error_data.get("message", "<unknown>")
            raise Exception(f"Error {code}: {message}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def list_files_in_vault(self, max_depth: int = 0) -> list[str]:
        """List files in the vault root directory.

        Args:
            max_depth: Maximum recursion depth (0 = current directory only, -1 = unlimited)

        Returns:
            List of file and directory paths (directories end with '/')
        """
        url = f"{self.get_base_url()}/vault/"

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.json()["files"]

        items = self._safe_call(call_fn)

        if max_depth == 0:
            return items

        # Recursive mode: traverse subdirectories up to max_depth
        all_items = list(items)  # Copy the initial items
        # Queue items: (directory_path, current_depth)
        dirs_to_process = [(item.rstrip("/"), 1) for item in items if item.endswith("/")]

        while dirs_to_process:
            current_dir, current_depth = dirs_to_process.pop(0)

            # Check if we've reached max depth (unless max_depth is -1 for unlimited)
            if max_depth != -1 and current_depth > max_depth:
                continue

            try:
                subitems = self.list_files_in_dir(current_dir, max_depth=0)
                # Prepend directory path to each item
                for item in subitems:
                    full_path = f"{current_dir}/{item}"
                    all_items.append(full_path)
                    if item.endswith("/"):
                        dirs_to_process.append((full_path.rstrip("/"), current_depth + 1))
            except Exception:
                # Skip directories that can't be accessed
                continue

        return all_items

    def list_files_in_dir(self, dirpath: str, max_depth: int = 0) -> list[str]:
        """List files in a specific directory.

        Args:
            dirpath: Path to the directory (relative to vault root)
            max_depth: Maximum recursion depth (0 = current directory only, -1 = unlimited)

        Returns:
            List of file and directory paths (directories end with '/')
        """
        # Strip trailing slash to avoid double slashes in URL
        dirpath = dirpath.rstrip("/")
        url = f"{self.get_base_url()}/vault/{dirpath}/"

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.json()["files"]

        items = self._safe_call(call_fn)

        if max_depth == 0:
            return items

        # Recursive mode: traverse subdirectories up to max_depth
        all_items = list(items)  # Copy the initial items
        # Queue items: (relative_subdir_path, current_depth)
        dirs_to_process = [(item.rstrip("/"), 1) for item in items if item.endswith("/")]

        while dirs_to_process:
            current_subdir, current_depth = dirs_to_process.pop(0)

            # Check if we've reached max depth (unless max_depth is -1 for unlimited)
            if max_depth != -1 and current_depth > max_depth:
                continue

            try:
                # Build full path from base directory
                full_dir_path = f"{dirpath}/{current_subdir}"
                subitems = self.list_files_in_dir(full_dir_path, max_depth=0)
                # Prepend subdirectory path to each item
                for item in subitems:
                    relative_path = f"{current_subdir}/{item}"
                    all_items.append(relative_path)
                    if item.endswith("/"):
                        dirs_to_process.append((relative_path.rstrip("/"), current_depth + 1))
            except Exception:
                # Skip directories that can't be accessed
                continue

        return all_items

    def get_file_contents(self, filepath: str) -> str:
        url = f"{self.get_base_url()}/vault/{filepath}"

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.text

        return self._safe_call(call_fn)

    def get_batch_file_contents(self, filepaths: list[str]) -> str:
        """Get contents of multiple files and concatenate them with headers.

        Args:
            filepaths: List of file paths to read

        Returns:
            String containing all file contents with headers
        """
        result = []

        for filepath in filepaths:
            try:
                content = self.get_file_contents(filepath)
                result.append(f"# {filepath}\n\n{content}\n\n---\n\n")
            except Exception as e:
                # Add error message but continue processing other files
                result.append(
                    f"# {filepath}\n\nError reading file: {str(e)}\n\n---\n\n"
                )

        return "".join(result)

    def list_headings(
        self, filepath: str, delimiter: str = "::"
    ) -> list[dict[str, Any]]:
        """Extract all headings from a markdown file with their full hierarchical paths.

        Args:
            filepath: Path to the file (relative to vault root)
            delimiter: Delimiter to use for building paths (default: "::")

        Returns:
            List of heading dictionaries with keys:
            - level: Heading level (1-6)
            - text: The heading text without # markers
            - path: Full hierarchical path for use in patch operations
            - line: Line number where heading appears (1-indexed)
        """
        content = self.get_file_contents(filepath)
        headings = []
        hierarchy_stack = []  # Stack to track current path at each level

        for line_num, line in enumerate(content.split("\n"), start=1):
            # Check if line is a heading (starts with one or more #)
            stripped = line.lstrip()
            if not stripped.startswith("#"):
                continue

            # Count heading level and extract text
            level = 0
            for char in stripped:
                if char == "#":
                    level += 1
                else:
                    break

            if level == 0 or level > 6:
                continue

            # Extract heading text (after the # markers and any whitespace)
            heading_text = stripped[level:].lstrip()

            # Build the path by maintaining hierarchy
            # Remove any levels deeper than current level
            hierarchy_stack = hierarchy_stack[: level - 1]

            # Add current heading to hierarchy
            hierarchy_stack.append(heading_text)

            # Build full path with delimiter
            full_path = delimiter.join(hierarchy_stack)

            headings.append(
                {
                    "level": level,
                    "text": heading_text,
                    "path": full_path,
                    "line": line_num,
                }
            )

        return headings

    def search(self, query: str, context_length: int = 100) -> list[dict[str, Any]]:
        url = f"{self.get_base_url()}/search/simple/"
        params = {"query": query, "contextLength": context_length}

        def call_fn():
            response = requests.post(
                url,
                headers=self._get_headers(),
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)

    def append_content(self, filepath: str, content: str) -> None:
        url = f"{self.get_base_url()}/vault/{filepath}"

        def call_fn():
            response = requests.post(
                url,
                headers=self._get_headers() | {"Content-Type": "text/markdown"},
                data=content,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)

    def patch_content(
        self,
        filepath: str,
        operation: str,
        target_type: str,
        target: str,
        content: str,
        trim_whitespace: bool = True,
        delimiter: str = "::",
    ) -> None:
        url = f"{self.get_base_url()}/vault/{filepath}"

        headers = self._get_headers() | {
            "Content-Type": "text/markdown",
            "Operation": operation,
            "Target-Type": target_type,
            "Target": urllib.parse.quote(target),
            "Trim-Target-Whitespace": "true" if trim_whitespace else "false",
            "Target-Delimiter": delimiter,
        }

        def call_fn():
            response = requests.patch(
                url,
                headers=headers,
                data=content,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)

    def put_content(self, filepath: str, content: str) -> None:
        url = f"{self.get_base_url()}/vault/{filepath}"

        def call_fn():
            response = requests.put(
                url,
                headers=self._get_headers() | {"Content-Type": "text/markdown"},
                data=content,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)

    def delete_file(self, filepath: str) -> None:
        """Delete a file or directory from the vault.

        Args:
            filepath: Path to the file to delete (relative to vault root)

        Returns:
            None on success
        """
        url = f"{self.get_base_url()}/vault/{filepath}"

        def call_fn():
            response = requests.delete(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)

    def search_json(self, query: dict) -> list[Any]:
        url = f"{self.get_base_url()}/search/"

        headers = self._get_headers() | {
            "Content-Type": "application/vnd.olrapi.jsonlogic+json"
        }

        def call_fn():
            response = requests.post(
                url,
                headers=headers,
                json=query,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)

    def get_periodic_note(self, period: str, type: str = "content") -> Any:
        """Get current periodic note for the specified period.

        Args:
            period: The period type (daily, weekly, monthly, quarterly, yearly)
            type: Type of the data to get ('content' or 'metadata').
                'content' returns just the content in Markdown format.
                'metadata' includes note metadata (including paths, tags, etc.) and the content..

        Returns:
            Content of the periodic note
        """
        url = f"{self.get_base_url()}/periodic/{period}/"

        def call_fn():
            headers = self._get_headers()
            if type == "metadata":
                headers["Accept"] = "application/vnd.olrapi.note+json"
            response = requests.get(
                url, headers=headers, verify=self.verify_ssl, timeout=self.timeout
            )
            response.raise_for_status()

            if type == "metadata":
                return response.json()
            return response.text

        return self._safe_call(call_fn)

    def get_recent_periodic_notes(
        self, period: str, limit: int = 5, include_content: bool = False
    ) -> list[dict[str, Any]]:
        """Get most recent periodic notes for the specified period type.

        Args:
            period: The period type (daily, weekly, monthly, quarterly, yearly)
            limit: Maximum number of notes to return (default: 5)
            include_content: Whether to include note content (default: False)

        Returns:
            List of recent periodic notes
        """
        url = f"{self.get_base_url()}/periodic/{period}/recent"
        params = {"limit": limit, "includeContent": include_content}

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.json()

        return self._safe_call(call_fn)

    def get_recent_changes(
        self, limit: int = 10, days: int = 90
    ) -> list[dict[str, Any]]:
        """Get recently modified files in the vault.

        Args:
            limit: Maximum number of files to return (default: 10)
            days: Only include files modified within this many days (default: 90)

        Returns:
            List of recently modified files with metadata
        """
        # Build the DQL query
        query_lines = [
            "TABLE file.mtime",
            f"WHERE file.mtime >= date(today) - dur({days} days)",
            "SORT file.mtime DESC",
            f"LIMIT {limit}",
        ]

        # Join with proper DQL line breaks
        dql_query = "\n".join(query_lines)

        # Make the request to search endpoint
        url = f"{self.get_base_url()}/search/"
        headers = self._get_headers() | {
            "Content-Type": "application/vnd.olrapi.dataview.dql+txt"
        }

        def call_fn():
            response = requests.post(
                url,
                headers=headers,
                data=dql_query.encode("utf-8"),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)

    def get_file_metadata(self, filepath: str) -> dict[str, Any]:
        """Get complete file metadata including frontmatter, tags, and stats.

        Args:
            filepath: Path to the file (relative to vault root)

        Returns:
            Dictionary with keys: content, frontmatter, path, tags, stat
        """
        url = f"{self.get_base_url()}/vault/{filepath}"

        def call_fn():
            headers = self._get_headers() | {
                "Accept": "application/vnd.olrapi.note+json"
            }
            response = requests.get(
                url, headers=headers, verify=self.verify_ssl, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)

    def search_by_tags(
        self, tags: list[str], match_all: bool = False
    ) -> list[dict[str, Any]]:
        """Search for files containing specified tags.

        Args:
            tags: List of tags to search for (without # prefix)
            match_all: If True, files must have ALL tags (AND logic).
                      If False, files with ANY tag matches (OR logic).

        Returns:
            List of files matching the tag criteria
        """
        # Build JsonLogic query for tag search
        tag_conditions = [{"in": [tag, {"var": "tags"}]} for tag in tags]

        if match_all:
            # AND logic - all tags must be present
            query = (
                {"and": tag_conditions}
                if len(tag_conditions) > 1
                else tag_conditions[0]
            )
        else:
            # OR logic - any tag matches
            query = (
                {"or": tag_conditions} if len(tag_conditions) > 1 else tag_conditions[0]
            )

        # Use the existing search_json method
        return self.search_json(query)

    def search_by_frontmatter(
        self, field: str, value: Any = None, operator: str = "equals"
    ) -> list[dict[str, Any]]:
        """Search files by frontmatter field values.

        Args:
            field: Frontmatter field name to search
            value: Value to match (optional if operator is "exists")
            operator: Comparison operator ("equals", "contains", "exists")

        Returns:
            List of files where frontmatter matches criteria

        Raises:
            ValueError: If operator is invalid or value is missing when required
        """
        if operator not in constants.VALID_FRONTMATTER_OPERATORS:
            raise ValueError(
                f"Invalid operator: {operator}. "
                f"Must be one of: {', '.join(constants.VALID_FRONTMATTER_OPERATORS)}"
            )

        if operator != "exists" and value is None:
            raise ValueError(f"Value is required for operator '{operator}'")

        # Build JsonLogic query for frontmatter search
        if operator == "exists":
            # Check if field exists in frontmatter
            query = {"in": [field, {"var": "frontmatter"}]}
        elif operator == "equals":
            # Check if field equals specific value
            query = {"==": [{"var": f"frontmatter.{field}"}, value]}
        elif operator == "contains":
            # Check if field contains substring (for strings) or value (for arrays)
            if isinstance(value, str):
                query = {"in": [value, {"var": f"frontmatter.{field}"}]}
            else:
                query = {"in": [value, {"var": f"frontmatter.{field}"}]}
        else:
            # This should never happen due to validation above, but helps type checker
            raise ValueError(f"Unexpected operator: {operator}")

        # Use the existing search_json method
        return self.search_json(query)

    def list_all_tags(self) -> dict[str, int]:
        """Get all unique tags in the vault with usage counts.

        Returns:
            Dictionary mapping tag names to number of files using them
        """
        # Get all files in vault
        all_files = self.list_files_in_vault()

        # Filter to only markdown files
        md_files = [f for f in all_files if f.endswith(".md") and not f.endswith("/")]

        # Aggregate tags from all files
        tag_counts: dict[str, int] = {}

        for filepath in md_files:
            try:
                metadata = self.get_file_metadata(filepath)
                file_tags = metadata.get("tags", [])

                for tag in file_tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            except Exception:
                # Skip files that can't be read or parsed
                continue

        return tag_counts

    def search_folders(self, folder_name: str, root_path: str = "") -> list[str]:
        """Recursively search for folders by name (case-insensitive substring match).

        Args:
            folder_name: Substring to search for in folder names (case-insensitive)
            root_path: Optional root directory to start search from (defaults to vault root)

        Returns:
            List of folder paths that match the search criteria
        """
        matching_folders = []
        folders_to_process = [root_path]

        # Normalize search term to lowercase for case-insensitive comparison
        search_term = folder_name.lower()

        while folders_to_process:
            current_path = folders_to_process.pop(0)

            try:
                # Get all items in current directory
                if current_path == "":
                    items = self.list_files_in_vault()
                else:
                    items = self.list_files_in_dir(current_path)

                # Process directories
                for item in items:
                    if item.endswith("/"):
                        # Remove trailing slash for comparison
                        folder_name_only = item.rstrip("/")

                        # Build full path
                        if current_path == "":
                            full_path = folder_name_only
                        else:
                            full_path = f"{current_path}/{folder_name_only}"

                        # Check if folder name matches (case-insensitive substring)
                        if search_term in folder_name_only.lower():
                            matching_folders.append(full_path)

                        # Add to queue for recursive search
                        folders_to_process.append(full_path)

            except Exception:
                # Skip folders that can't be accessed
                continue

        return matching_folders
