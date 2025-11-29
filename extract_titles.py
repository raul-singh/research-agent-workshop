#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["click"]
# ///
"""Extract all markdown titles from markdown files in a folder."""

from pathlib import Path

import click


def extract_titles(file_path: Path) -> list[tuple[int, str]]:
    """Extract first and second level headers from a markdown file.
    
    Returns a list of (line_number, title) tuples.
    """
    titles = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            stripped = line.strip()
            # Match "# " or "## " but not "### " or deeper
            if stripped.startswith("# ") or stripped.startswith("## "):
                titles.append((line_num, stripped))
    return titles


@click.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--include-line-numbers", "-n", is_flag=True, help="Include line numbers in output")
def main(folder: Path, include_line_numbers: bool) -> None:
    """Extract all markdown titles from .md files in FOLDER."""
    md_files = sorted(folder.glob("*.md"))
    
    if not md_files:
        click.echo(f"No markdown files found in {folder}")
        return
    
    for md_file in md_files:
        titles = extract_titles(md_file)
        if titles:
            click.echo(click.style(f"\n{md_file.name}", fg="cyan", bold=True))
            click.echo("-" * len(md_file.name))
            for line_num, title in titles:
                if include_line_numbers:
                    click.echo(f"  L{line_num}: {title}")
                else:
                    click.echo(f"  {title}")


if __name__ == "__main__":
    main()

