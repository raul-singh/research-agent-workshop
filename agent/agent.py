import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated

from datapizza.clients.openai import OpenAIClient
from datapizza.tools import Tool, tool
from dotenv import load_dotenv

from agent.custom_logs import (
    log_event,
    log_kv,
    log_task_done,
    log_task_failed,
    log_task_spawn,
)
from agent.harness import Agent
from agent.prompt import SEARCH_GUIDANCE, SUBAGENT_PROMPT, SYSTEM_PROMPT
from agent.search_in_docs import search_in_documents

load_dotenv()

MODEL = "gpt-5.4-mini"
MAX_SEARCH_RESULTS = 50


@tool
def search(
    query: str,
    document: str | None = None,
    surrounding: int = 5,
    after_only: bool = False,
    fuzzy: bool = False,
    case_sensitive: bool = False,
) -> str:
    """Search the D&D 5e SRD knowledge base for information.

    Use this tool to find specific rules, spells, monsters, items, or any other
    D&D 5e content. The search supports regex patterns and returns matching text
    with surrounding context. Prefer exact search first for known terms, feature
    names, species names, spell names, and headings. If fuzzy=True, the same
    text-search rules still apply, but with tolerance for typos and small wording
    differences. Fuzzy search is not semantic search and should not be used for
    open-ended questions, hypotheses, long natural-language descriptions, or
    already-exact terms like "Orc". If a heading search like "# Feature Name"
    fails, retry the bare feature name or the parent section heading instead.
    If the text gets truncated because of the surrounding value, it is indicated
    by an ellipsis.

    Args:
        query: The search string (supports regex). Be specific with your search terms.
        document: Optional specific document filename to search (e.g., "DND5eSRD_104-120.md").
                  If None, searches all documents.
        surrounding: Number of lines of context to include around matches (default: 5).
        after_only: If True, only include lines after the match, not before.
        fuzzy: If True, tolerate typos and small wording differences while still
               searching for a short concrete term or phrase. Use only after
               exact search fails due likely spelling/wording mismatch. Not
               semantic search.
        case_sensitive: If True, match case exactly. Defaults to case-insensitive search.

    Returns:
        Formatted search results with source document and matching content.
    """

    results = search_in_documents(
        query=query,
        document=document,
        surrounding=surrounding,
        after_only=after_only,
        fuzzy=fuzzy,
        case_sensitive=case_sensitive,
    )

    if not results:
        return "No matches found for the given query."

    if len(results) > MAX_SEARCH_RESULTS:
        return (
            f"Search returned {len(results)} matches, which is too many to return safely. "
            "Narrow the query before trying again: use a more specific term, set the "
            "document parameter when possible, search a heading/title first, or split the "
            "question into smaller searches."
        )

    output_parts = [f"Found {len(results)} match(es):\n"]

    for i, result in enumerate(results, start=1):
        output_parts.append(f"[{i}] Source: {result['source']}")
        output_parts.append(f"    Match: {result['match']}")
        if result.get("title_path"):
            output_parts.append(f"    Title Path: {result['title_path']}")
        output_parts.append(f"    Context: {result['content']}")
        output_parts.append("")

    return "\n".join(output_parts)


@tool
def delegate_research(
    tasks: Annotated[
        list[str],
        "Concrete, independent research tasks. Each task should ask a subagent to gather evidence and sources, not merely plan the work.",
    ],
    max_parallel: Annotated[
        int,
        "Maximum number of subagents to run at the same time. Use 3-6 for broad comparisons.",
    ] = 4,
) -> str:
    """Delegate independent research tasks to parallel subagents.

    Use this before direct search when a question has three or more independent
    research branches, such as comparing many options or surveying multiple rules
    areas. Each task should be self-contained and ask for concise findings with
    source documents. Subagents can use search but cannot delegate to other agents.

    Args:
        tasks: Independent research tasks to run in parallel.
        max_parallel: Maximum number of subagents to run at the same time.

    Returns:
        Numbered subagent findings, one section per task.
    """

    cleaned_tasks = [task.strip() for task in tasks if task.strip()]
    if not cleaned_tasks:
        return "No research tasks provided."

    subagent_prompt = format_subagent_prompt()
    concurrency = min(max(1, max_parallel), 8)
    log_event(
        "delegate", f"starting {len(cleaned_tasks)} research task(s)", color="magenta"
    )

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(_run_subagent_task, task, index, subagent_prompt)
            for index, task in enumerate(cleaned_tasks, start=1)
        ]
        results = [future.result() for future in futures]

    output_parts = [f"Completed {len(results)} delegated research task(s):"]
    for index, task, answer in sorted(results):
        output_parts.append("")
        output_parts.append(f"[{index}] Task: {task}")
        output_parts.append(answer)

    return "\n".join(output_parts)


def _run_subagent_task(
    task: str,
    index: int,
    system_prompt: str,
) -> tuple[int, str, str]:
    """Run a single delegated research task in an isolated harness Agent."""
    started_at = time.monotonic()
    name = f"S{index}"
    log_task_spawn(name, task, tools=["search"], agent_name=name)

    subagent = Agent(
        client=create_client(),
        system_prompt=system_prompt,
        tools=[Tool(search)],
        compact_logs=True,
        name=name,
    )

    try:
        answer = subagent.run(task)
    except Exception as exc:
        log_task_failed("task", time.monotonic() - started_at, exc, agent_name=name)
        return index, task, f"Subagent failed: {exc}"

    log_task_done("task", time.monotonic() - started_at, agent_name=name)
    return index, task, answer or "No answer returned."


def load_structure() -> str:
    """Load the knowledge base table of contents file."""
    structure_path = Path("knowledge_base/toc.txt")
    return structure_path.read_text(encoding="utf-8")


def format_system_prompt() -> str:
    """Format the main agent system prompt with current KB structure."""
    return SYSTEM_PROMPT.format(
        structure=load_structure(),
        search_guidance=SEARCH_GUIDANCE,
    )


def format_subagent_prompt() -> str:
    """Format the delegated research subagent prompt with current KB structure."""
    return SUBAGENT_PROMPT.format(
        structure=load_structure(),
        search_guidance=SEARCH_GUIDANCE,
    )


def create_client() -> OpenAIClient:
    """Create the OpenAI client used by agents."""
    return OpenAIClient(
        model=MODEL,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def create_agent() -> Agent:
    """Create and configure the D&D knowledge base agent."""
    return Agent(
        client=create_client(),
        system_prompt=format_system_prompt(),
        tools=[search, delegate_research],
    )
