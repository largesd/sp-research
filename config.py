"""Configuration loader for OBJECTIVE.md."""

import re
from pathlib import Path
from typing import List, Optional

from models import PolicyConfig, ResearchConfig, ResearcherConfig


def parse_objective_md(filepath: str = "OBJECTIVE.md") -> ResearchConfig:
    """Parse OBJECTIVE.md and extract research configuration.

    Args:
        filepath: Path to OBJECTIVE.md

    Returns:
        ResearchConfig object with all settings
    """
    content = Path(filepath).read_text(encoding="utf-8")

    # Extract topic
    topic_match = re.search(r'## Research Topic\s*\n\s*([^\n]+)', content)
    topic = topic_match.group(1).strip() if topic_match else "Unknown Topic"

    # Extract target location
    location_match = re.search(r'\*\*Target Location:\*\*\s*([^\n]+)', content)
    target_location = location_match.group(1).strip() if location_match else ""

    # Extract sub-agent default count
    sub_agent_match = re.search(r'\*\*Default count per researcher\*\*:\s*(\d+)', content)
    sub_agent_count = int(sub_agent_match.group(1)) if sub_agent_match else 5

    # Extract research rounds
    rounds_match = re.search(r'\*\*Research rounds\*\*:\s*(\d+)', content)
    research_rounds = int(rounds_match.group(1)) if rounds_match else 2

    # Parse researchers table
    researchers = parse_researchers_table(content)

    # Parse research areas
    research_areas = parse_research_areas(content)

    # Parse Policy agent configuration
    policy_agent = parse_policy_config(content)

    return ResearchConfig(
        topic=topic,
        researchers=researchers,
        research_rounds=research_rounds,
        sub_agent_default_count=sub_agent_count,
        research_areas=research_areas,
        target_location=target_location,
        policy_agent=policy_agent
    )


def parse_researchers_table(content: str) -> List[ResearcherConfig]:
    """Parse the researchers table from markdown content.

    Args:
        content: Full markdown content

    Returns:
        List of ResearcherConfig objects
    """
    researchers = []

    # Find researchers section - look specifically for "### Researchers" header
    # Then match the table that follows with 4 columns (Alias, Model, Language, Description)
    researchers_section = re.search(
        r'### Researchers[^\n]*\n\n\|([^\n]+)\|\n\|[-:\|\s]+\|\n((?:\|[^\n]+\n)+)',
        content,
        re.DOTALL
    )

    if researchers_section:
        # Extract rows (skip header and separator)
        rows_text = researchers_section.group(2)
        rows = [r.strip() for r in rows_text.strip().split('\n') if r.strip()]

        for row in rows:
            # Parse table row: | Alias | Model | Language | Description |
            cells = [c.strip() for c in row.split('|') if c.strip()]
            if len(cells) >= 4:
                researchers.append(ResearcherConfig(
                    alias=cells[0],
                    model=cells[1],
                    language=cells[2],
                    description=cells[3]
                ))

    return researchers


def parse_policy_config(content: str) -> Optional[PolicyConfig]:
    """Parse the Policy agent configuration from markdown content.

    Args:
        content: Full markdown content

    Returns:
        PolicyConfig object or None if not found
    """
    # Check if Policy Agent section exists
    if "### Policy Agent" not in content and "## Policy Agent" not in content:
        return None

    policy = PolicyConfig()

    # Find Policy Agent section
    policy_section = re.search(
        r'### Policy Agent.*?(## |\Z)',
        content,
        re.DOTALL
    )

    if not policy_section:
        policy_section = re.search(
            r'## Policy Agent.*?(## |\Z)',
            content,
            re.DOTALL
        )

    if policy_section:
        section_text = policy_section.group(0)

        # Parse model
        model_match = re.search(r'LLM Model\s*\|\s*([^|]+)', section_text)
        if model_match:
            policy.model = model_match.group(1).strip()

        # Parse language
        language_match = re.search(r'Language\s*\|\s*([^|]+)', section_text)
        if language_match:
            policy.language = language_match.group(1).strip()

        # Parse max proposal words
        words_match = re.search(r'Max Proposal Words\s*\|\s*(\d+)', section_text)
        if words_match:
            policy.max_proposal_words = int(words_match.group(1))

        # Parse target location
        location_match = re.search(r'Target Location\s*\|\s*([^|]+)', section_text)
        if location_match:
            policy.target_location = location_match.group(1).strip()

        # Parse proposal terms
        terms_match = re.search(r'Proposal Terms\s*\|\s*([^|]+)', section_text)
        if terms_match:
            terms_text = terms_match.group(1).strip()
            # Split by comma and clean up
            policy.proposal_terms = [t.strip() for t in terms_text.split(',')]

    return policy


def parse_research_areas(content: str) -> List[str]:
    """Parse research areas list from markdown content.

    Args:
        content: Full markdown content

    Returns:
        List of research area strings
    """
    areas = []

    # Find research areas section (numbered list)
    areas_match = re.search(
        r'## Research Areas.*?\n(1\..*?)(?=---|\Z)',
        content,
        re.DOTALL
    )

    if areas_match:
        areas_text = areas_match.group(1)
        # Extract numbered items
        for line in areas_text.split('\n'):
            match = re.match(r'\d+\.\s*(.+)', line.strip())
            if match:
                areas.append(match.group(1).strip())

    return areas


def get_researcher_system_prompt(researcher: ResearcherConfig, topic: str, language: str) -> str:
    """Generate system prompt for a researcher.

    Args:
        researcher: Researcher configuration
        topic: Research topic
        language: Language to use

    Returns:
        System prompt string
    """
    return f"""You are {researcher.alias}, an expert researcher specializing in {researcher.description}.

Your task is to conduct comprehensive research on the following topic:
"{topic}"

Language: {language}

You will lead a team of {researcher.sub_agent_count} sub-agents, each with specialized expertise in different areas.
Your research process involves multiple rounds:
- Round 1: Foundation research across all areas
- Round 2: Deep dive analysis building on Round 1 findings

Guidelines:
1. Always provide well-structured, human-readable research outputs
2. Include proper citations with sources and references
3. Synthesize findings from your sub-agents into coherent insights
4. Store all research materials in your designated memory folder
5. Produce a final SUMMARY.md synthesizing all research rounds

You have access to sub-agents who can research specific aspects. Use them strategically."""
