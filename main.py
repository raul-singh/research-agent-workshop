import os
from pathlib import Path

import click
from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient
from datapizza.tools import tool
from dotenv import load_dotenv

from search_in_docs import search_in_documents

load_dotenv()


@tool
def search(
    query: str,
    document: str | None = None,
    surrounding: int = 100,
    after_only: bool = False,
    fuzzy: bool = False,
) -> str:
    """Search the D&D 5e SRD knowledge base for information.

    Use this tool to find specific rules, spells, monsters, items, or any other
    D&D 5e content. The search supports regex patterns and returns matching text
    with surrounding context. If the text gets truncated because of the surrounding value,
    it is indicated by an ellipsis.

    Args:
        query: The search string (supports regex). Be specific with your search terms.
        document: Optional specific document filename to search (e.g., "DND5eSRD_104-120.md").
                  If None, searches all documents.
        surrounding: Number of characters of context to include around matches (default: 100).
        after_only: If True, only include characters after the match, not before.
        fuzzy: If True, find similar text when exact matches fail.

    Returns:
        Formatted search results with source document and matching content.
    """
    results = search_in_documents(
        query=query,
        document=document,
        surrounding=surrounding,
        after_only=after_only,
        fuzzy=fuzzy,
    )

    if not results:
        return "No matches found for the given query."

    output_parts = [f"Found {len(results)} match(es):\n"]

    for i, result in enumerate(results, start=1):
        output_parts.append(f"[{i}] Source: {result['source']}")
        output_parts.append(f"    Match: {result['match']}")
        if result.get("title_path"):
            output_parts.append(f"    Title Path: {result['title_path']}")
        output_parts.append(f"    Context: {result['content']}")
        output_parts.append("")

    return "\n".join(output_parts)


def load_structure() -> str:
    """Load the knowledge base structure file."""
    structure_path = Path("knowledge_base/structure.txt")
    return structure_path.read_text(encoding="utf-8")


def create_agent() -> Agent:
    """Create and configure the D&D knowledge base agent."""
    structure = load_structure()

    system_prompt = f"""You are a helpful D&D 5e rules assistant with access to the complete Systems Reference Document (SRD).

Your role is to answer questions about D&D 5e rules, spells, monsters, items, classes, and other game content by searching the knowledge base.

## Knowledge Base Structure

The following shows the organization of the SRD documents you can search. Use this to understand where different content is located and to target your searches effectively:

{structure}

## How to Answer Questions

1. **Analyze the question** to identify key terms and topics
2. **Plan your search** by breaking down the question into smaller parts. Use the `write_plan` tool to write a plan for the search.
3. **Use grep_documents** to search for relevant information. Tips:
   - Search for specific terms (spell names, monster names, rule keywords)
   - Use the `document` parameter to target specific files when you know where content is, using the structure provided above. Prefer this over searching all documents.
   - For broad topics, search without specifying a document
   - You may need multiple searches to gather complete information
   - Set `fuzzy=True` when you need approximate matches (typos, paraphrasing, uncertain spelling)
   - To look for a title, prepend "# " to the query, for example: "# Fireball". You can pair this with `after_only=True` to look for the content after the title since usually content before the title is not relevant.
   - Stop searching when you have enough information to answer the question.
4. **Synthesize the results** into a clear, accurate answer
5. **Cite your sources** by mentioning which document(s) the information came from
6. **If information is not found**, say so clearly rather than guessing

## Important Guidelines

- Use the `grep_documents` tool in parallel to search for multiple queries at once.
- Prefer generic queries over specific queries that may fail.
- If you are doing very wide queries, use a small surrounding value.
- If yu don't find the answer because of the small surrounding value, increase the surrounding value.
- Combine `fuzzy=True` with smaller `surrounding` windows to keep the context concise.
- Do not use your own knowledge to answer the question. Always search the knowledge base for the answer.
- Always search before answering - don't rely on assumptions
- Quote relevant rules text when applicable
- If a question is ambiguous, search for the most likely interpretation
- For complex topics, break them down and search for each component
- Be concise but thorough in your answers"""

    client = OpenAIClient(
        model="gpt-5.1",
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    agent = Agent(
        name="dnd_kb_agent",
        client=client,
        system_prompt=system_prompt,
        tools=[search],
        gen_args={"reasoning_effort": "minimal"},
    )

    return agent


@click.command()
@click.option(
    "--query",
    "-q",
    prompt="Ask about D&D 5e",
    help="Your question about D&D 5e rules, spells, monsters, etc.",
)
def main(query: str) -> None:
    """D&D 5e SRD Knowledge Base Agent.

    Ask questions about D&D 5e rules, spells, monsters, items, classes, and more.
    The agent will search the SRD documents to find accurate answers.
    """
    agent = create_agent()

    click.echo(click.style("\n🎲 Searching the D&D 5e SRD...\n", fg="cyan", bold=True))

    response = agent.run(query)

    click.echo(click.style("📜 Answer:", fg="green", bold=True))
    click.echo(response.text)


if __name__ == "__main__":
    main()
    main()
