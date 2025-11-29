#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["click"]
# ///
"""Merge markdown files and split by first-level headers."""

import re
from pathlib import Path

import click


def slugify(text: str) -> str:
    """Convert a title to a filename-safe slug."""
    # Remove the leading # and strip
    text = text.lstrip("#").strip()
    # Convert to lowercase and replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
    # Remove leading/trailing hyphens
    return slug.strip("-")


def merge_files(folder: Path) -> str:
    """Merge all markdown files in folder into a single string."""
    md_files = sorted(folder.glob("*.md"))
    contents = []
    for md_file in md_files:
        contents.append(md_file.read_text(encoding="utf-8"))
    return "\n\n".join(contents)


def split_by_h1(content: str) -> list[tuple[str, str]]:
    """Split content by first-level headers.
    
    Returns list of (title, content) tuples.
    """
    # Split on lines that start with "# " (first-level header)
    sections = re.split(r"(?=^# )", content, flags=re.MULTILINE)
    
    result = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # Extract the title from the first line
        lines = section.split("\n", 1)
        title = lines[0].strip()
        
        # If this section starts with a first-level header, use it
        if title.startswith("# "):
            result.append((title, section))
        else:
            # Content before the first header (preamble)
            result.append(("# _preamble", section))
    
    return result


@click.command()
@click.argument("input_folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("output_folder", type=click.Path(path_type=Path))
@click.option("--merged-file", "-m", type=click.Path(path_type=Path), help="Also save the merged file to this path")
def main(input_folder: Path, output_folder: Path, merged_file: Path | None) -> None:
    """Merge markdown files from INPUT_FOLDER and split by H1 headers into OUTPUT_FOLDER."""
    # Merge all files
    click.echo(f"Merging files from {input_folder}...")
    merged_content = merge_files(input_folder)
    
    # Optionally save merged file
    if merged_file:
        merged_file.write_text(merged_content, encoding="utf-8")
        click.echo(f"Saved merged file to {merged_file}")
    
    # Split by first-level headers
    sections = split_by_h1(merged_content)
    click.echo(f"Found {len(sections)} sections")
    
    # Create output folder
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Write each section to a file
    for i, (title, content) in enumerate(sections, start=1):
        slug = slugify(title)
        filename = f"{i:03d}-{slug}.md"
        output_path = output_folder / filename
        output_path.write_text(content, encoding="utf-8")
        click.echo(f"  {filename}: {title}")
    
    click.echo(f"\nDone! Created {len(sections)} files in {output_folder}")


if __name__ == "__main__":
    main()

