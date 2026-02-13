"""Researcher agent implementation."""

import json
from pathlib import Path
from typing import List, Optional

from openai import OpenAI

from config import get_researcher_system_prompt
from models import ResearchConfig, ResearcherConfig, ResearchNote, ResearchSummary
from sub_agent import SubAgent
from utils import (
    create_researcher_folders,
    get_timestamp,
    read_previous_research,
    sanitize_filename
)


class Researcher:
    """A researcher agent that orchestrates sub-agents for comprehensive research."""
    
    def __init__(
        self,
        config: ResearcherConfig,
        research_config: ResearchConfig,
        client: OpenAI,
        base_output_path: Path = Path("researchers")
    ):
        """Initialize a researcher.
        
        Args:
            config: Researcher configuration
            research_config: Overall research configuration
            client: OpenAI client instance
            base_output_path: Base path for researcher output folders
        """
        self.config = config
        self.research_config = research_config
        self.client = client
        
        # Create folder structure
        self.folder, self.memory_folder = create_researcher_folders(
            base_output_path,
            config.alias
        )
        
        # Initialize sub-agents
        self.sub_agents: List[SubAgent] = self._create_sub_agents()
        
        # Track research notes
        self.research_notes: List[ResearchNote] = []
    
    def _create_sub_agents(self) -> List[SubAgent]:
        """Create sub-agents based on research areas.
        
        Returns:
            List of SubAgent instances
        """
        sub_agents = []
        areas = self.research_config.research_areas
        
        # If no specific areas defined, use default areas
        if not areas:
            areas = [
                "Economic Analysis",
                "Policy & Governance",
                "Education & Reskilling",
                "Social Safety Nets",
                "Technology & Innovation"
            ]
        
        # Create sub-agents for each area
        for i, area in enumerate(areas[:self.config.sub_agent_count]):
            sub_agent = SubAgent(
                name=f"{self.config.alias}_Assistant_{i+1}",
                expertise=area,
                client=self.client,
                model=self.config.model,
                language=self.config.language,
                researcher_alias=self.config.alias
            )
            sub_agents.append(sub_agent)
        
        return sub_agents
    
    def conduct_research_round(self, round_num: int) -> List[ResearchNote]:
        """Conduct a research round using sub-agents.
        
        Args:
            round_num: Current research round number
            
        Returns:
            List of research notes from this round
        """
        print(f"  [Round {round_num}] {self.config.alias} deploying {len(self.sub_agents)} sub-agents...")
        
        notes = []
        previous_context = ""
        
        # For round 2+, read previous research for context
        if round_num > 1:
            previous_context = read_previous_research(self.memory_folder, round_num)
            print(f"    Loaded previous research: {len(previous_context)} chars")
        
        # Deploy each sub-agent
        for i, sub_agent in enumerate(self.sub_agents):
            print(f"    Sub-agent {i+1}/{len(self.sub_agents)}: {sub_agent.expertise}")
            
            # Define specific task based on round
            if round_num == 1:
                task = f"Conduct foundational research on {sub_agent.expertise} aspects of the topic."
            else:
                task = f"Analyze previous findings on {sub_agent.expertise} and identify deeper insights, gaps, and recommendations."
            
            # Conduct research
            note = sub_agent.research(
                topic=self.research_config.topic,
                round_num=round_num,
                previous_context=previous_context,
                specific_task=task
            )
            
            # Save to memory folder
            filepath = sub_agent.save_research_note(note, self.memory_folder)
            print(f"      Saved to: {filepath.name}")
            
            notes.append(note)
        
        self.research_notes.extend(notes)
        return notes
    
    def generate_summary(self) -> Path:
        """Generate final SUMMARY.md synthesizing all research.
        
        Returns:
            Path to generated SUMMARY.md
        """
        print(f"  Generating summary for {self.config.alias}...")
        
        # Gather all research content
        all_research = read_previous_research(self.memory_folder, 99)
        
        # Create system prompt for summary generation
        system_prompt = f"""You are {self.config.alias}, an expert researcher specializing in {self.config.description}.

Your task is to synthesize all the research conducted by your sub-agents into a comprehensive SUMMARY.md document.

Language: {self.config.language}

The summary should be well-structured, professional, and include:
1. An executive summary
2. Key findings organized by theme
3. Actionable recommendations
4. Complete list of references and sources

Format the output in clear markdown."""

        user_prompt = f"""Please synthesize the following research materials into a comprehensive SUMMARY.md:

Research Topic: {self.research_config.topic}

All Research Materials:
{all_research[:15000]}  # Limit context to avoid token limits

---

Generate a complete SUMMARY.md with:

1. **Executive Summary** - Brief overview of key findings
2. **Key Findings** - Organized by major themes/areas
3. **Recommendations** - Actionable solutions and strategies
4. **References** - All sources cited in the research

Write in {self.config.language} in a professional, academic tone."""

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=6000
            )
            
            summary_content = response.choices[0].message.content
            
            # Add header with metadata
            final_content = f"""# Research Summary

**Researcher:** {self.config.alias}  
**Expertise:** {self.config.description}  
**Model:** {self.config.model}  
**Language:** {self.config.language}  
**Topic:** {self.research_config.topic}  
**Generated:** {get_timestamp()}

---

{summary_content}

---

*Generated by Multi-Agent Research System*
"""
            
        except Exception as e:
            # Fallback summary if API fails
            final_content = f"""# Research Summary

**Researcher:** {self.config.alias}  
**Topic:** {self.research_config.topic}  
**Generated:** {get_timestamp()}

---

## Error

Failed to generate summary: {str(e)}

## Raw Research Notes

{all_research[:5000]}
"""
        
        # Write SUMMARY.md
        summary_path = self.folder / "SUMMARY.md"
        summary_path.write_text(final_content, encoding="utf-8")
        
        print(f"    Summary saved to: {summary_path}")
        return summary_path
    
    def run_full_research(self) -> Path:
        """Run complete research process for all rounds.
        
        Returns:
            Path to SUMMARY.md
        """
        print(f"\n🔬 Starting research for {self.config.alias} ({self.config.model})")
        
        # Conduct each research round
        for round_num in range(1, self.research_config.research_rounds + 1):
            self.conduct_research_round(round_num)
        
        # Generate final summary
        summary_path = self.generate_summary()
        
        print(f"✅ Research complete for {self.config.alias}")
        return summary_path
