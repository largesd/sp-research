"""Utility functions for the research system."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def load_env_variables() -> tuple[str, str]:
    """Load API configuration from .env file.
    
    Returns:
        Tuple of (api_key, api_url)
        
    Raises:
        ValueError: If required environment variables are missing
    """
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
    
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not found in .env file. "
            "Please create a .env file with your OpenRouter API key."
        )
    
    return api_key, api_url


def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        The directory path
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_timestamp() -> str:
    """Get current timestamp string.
    
    Returns:
        ISO format timestamp
    """
    return datetime.now().isoformat()


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as filename.
    
    Args:
        name: Original name
        
    Returns:
        Sanitized filename
    """
    # Replace spaces and special characters
    sanitized = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    # Remove any non-alphanumeric characters except underscore and hyphen
    sanitized = ''.join(c for c in sanitized if c.isalnum() or c in '_-')
    return sanitized.lower()


def create_researcher_folders(base_path: Path | str, alias: str) -> tuple[Path, Path]:
    """Create folder structure for a researcher.
    
    Args:
        base_path: Base path for all researchers
        alias: Researcher alias
        
    Returns:
        Tuple of (researcher_folder, memory_folder)
    """
    base_path = Path(base_path) if isinstance(base_path, str) else base_path
    researcher_folder = base_path / sanitize_filename(alias)
    memory_folder = researcher_folder / "memory"
    
    ensure_directory(researcher_folder)
    ensure_directory(memory_folder)
    
    return researcher_folder, memory_folder


def format_sources(sources: list[str]) -> str:
    """Format a list of sources for markdown.
    
    Args:
        sources: List of source strings
        
    Returns:
        Formatted markdown string
    """
    if not sources:
        return "*No sources provided*"
    
    return '\n'.join(f'- {source}' for source in sources)


def read_previous_research(memory_folder: Path, round_num: int) -> str:
    """Read research materials from previous rounds.
    
    Args:
        memory_folder: Path to memory folder
        round_num: Current round number (reads all rounds < current)
        
    Returns:
        Concatenated content of previous research materials
    """
    if round_num <= 1:
        return ""
    
    content_parts = []
    
    # Read all markdown files in memory folder
    for md_file in sorted(memory_folder.glob("*.md")):
        try:
            file_content = md_file.read_text(encoding="utf-8")
            content_parts.append(f"\n## From: {md_file.name}\n\n{file_content}")
        except Exception as e:
            content_parts.append(f"\n## From: {md_file.name}\n\n(Error reading file: {e})")
    
    return '\n'.join(content_parts)
