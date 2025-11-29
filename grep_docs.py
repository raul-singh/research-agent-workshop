#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["click"]
# ///
"""Grep documents with surrounding context."""

import re
from pathlib import Path

import click


def grep_documents(
    query: str,
    document: str | None = None,
    surrounding: int = 100,
    after_only: bool = False,
) -> list[dict[str, str]]:
    """Search for query in documents and return matches with surrounding context.

    Args:
        query: The search string (supports regex).
        document: Optional specific document filename to search. If None, searches all .md files in folder.
        surrounding: Number of characters before and after the match to include (default: 100).
        after_only: If True, only include characters after the match, not before (default: False).

    Returns:
        A list of dicts, each containing:
            - "source": The document filename
            - "content": The matched text with surrounding context
            - "match": The exact matched text
    """

    folder = Path("knowledge_base/docs")
    results = []

    # Determine which files to search
    if document:
        files = [folder / document]
        if not files[0].exists():
            # Try with .md extension
            files = [folder / f"{document}.md"]
    else:
        files = sorted(folder.glob("*.md"))

    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error:
        # If query is not valid regex, escape it
        pattern = re.compile(re.escape(query), re.IGNORECASE)

    for file_path in files:
        if not file_path.exists():
            continue

        content = file_path.read_text(encoding="utf-8")

        for match in pattern.finditer(content):
            if after_only:
                start = match.start()
            else:
                start = max(0, match.start() - surrounding)
            end = min(len(content), match.end() + surrounding)

            # Extract context
            context = content[start:end]

            # Add ellipsis if we truncated
            if start > 0 and not after_only:
                context = "..." + context
            if end < len(content):
                context = context + "..."

            results.append(
                {
                    "source": file_path.name,
                    "content": context,
                    "match": match.group(),
                }
            )

    return results


@click.command()
@click.argument("query")
@click.option(
    "--document",
    "-d",
    help="Specific document to search (searches all if not provided)",
)
@click.option(
    "--folder",
    "-f",
    default="output",
    type=click.Path(exists=True, path_type=Path),
    help="Folder containing documents",
)
@click.option(
    "--surrounding",
    "-s",
    default=100,
    type=int,
    help="Characters of context before/after match",
)
@click.option(
    "--case-sensitive", "-c", is_flag=True, help="Enable case-sensitive search"
)
@click.option(
    "--after-only",
    "-a",
    is_flag=True,
    help="Only include characters after the match, not before",
)
def main(
    query: str,
    document: str | None,
    folder: Path,
    surrounding: int,
    case_sensitive: bool,
    after_only: bool,
) -> None:
    """Search for QUERY in markdown documents."""
    results = grep_documents(
        query=query,
        document=document,
        folder=folder,
        surrounding=surrounding,
        case_insensitive=not case_sensitive,
        after_only=after_only,
    )

    if not results:
        click.echo("No matches found.")
        return

    click.echo(f"Found {len(results)} match(es):\n")

    for i, result in enumerate(results, start=1):
        click.echo(click.style(f"[{i}] {result['source']}", fg="cyan", bold=True))
        click.echo(f"    Match: {click.style(result['match'], fg='yellow')}")
        click.echo(f"    Context: {result['content']}")
        click.echo()


if __name__ == "__main__":
    main()
