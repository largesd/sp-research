"""Data models for the research system."""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class ResearchRound(Enum):
    """Research round enumeration."""
    ROUND_1 = 1
    ROUND_2 = 2


@dataclass
class SubAgentConfig:
    """Configuration for a sub-agent."""
    name: str
    expertise: str
    description: str


@dataclass
class ResearcherConfig:
    """Configuration for a researcher."""
    alias: str
    model: str
    language: str
    description: str
    sub_agent_count: int = 5


@dataclass
class ResearchConfig:
    """Overall research configuration parsed from OBJECTIVE.md."""
    topic: str
    researchers: List[ResearcherConfig] = field(default_factory=list)
    research_rounds: int = 2
    sub_agent_default_count: int = 5
    research_areas: List[str] = field(default_factory=list)


@dataclass
class ResearchNote:
    """A single research note/findings."""
    title: str
    content: str
    sources: List[str] = field(default_factory=list)
    round_num: int = 1
    sub_agent_name: str = ""
    timestamp: str = ""


@dataclass
class ResearchSummary:
    """Final summary for a researcher."""
    executive_summary: str
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
