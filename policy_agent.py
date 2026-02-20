"""Policy Agent implementation for synthesizing research into policy proposals."""

import json
from pathlib import Path
from typing import List, Optional

from openai import OpenAI

from models import PolicyConfig, PolicyProposal
from utils import get_timestamp, sanitize_filename


class PolicyAgent:
    """A policy agent that synthesizes research materials into actionable policy proposals."""

    def __init__(
        self,
        config: PolicyConfig,
        topic: str,
        client: OpenAI,
        base_output_path: Path = Path("researchers")
    ):
        """Initialize a Policy agent.

        Args:
            config: Policy agent configuration
            topic: Research topic
            client: OpenAI client instance
            base_output_path: Base path for reading researcher outputs
        """
        self.config = config
        self.topic = topic
        self.client = client
        self.base_output_path = Path(base_output_path)

        # Create policy output folder
        self.output_folder = self.base_output_path / sanitize_filename(config.alias)
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def collect_research_materials(self) -> dict[str, str]:
        """Collect all research materials from researcher SUMMARY.md files.

        Returns:
            Dictionary mapping researcher alias to their summary content
        """
        materials = {}

        # Look for all researcher folders
        for researcher_folder in self.base_output_path.iterdir():
            if researcher_folder.is_dir() and researcher_folder.name != sanitize_filename(self.config.alias):
                summary_path = researcher_folder / "SUMMARY.md"
                if summary_path.exists():
                    try:
                        content = summary_path.read_text(encoding="utf-8")
                        materials[researcher_folder.name] = content
                    except Exception as e:
                        print(f"    Warning: Could not read {summary_path}: {e}")

                # Also collect individual research notes from memory folders
                memory_folder = researcher_folder / "memory"
                if memory_folder.exists():
                    memory_content = []
                    for md_file in sorted(memory_folder.glob("*.md")):
                        try:
                            file_content = md_file.read_text(encoding="utf-8")
                            memory_content.append(f"\n### From: {md_file.name}\n\n{file_content}")
                        except Exception as e:
                            memory_content.append(f"\n### From: {md_file.name}\n\n(Error reading file: {e})")

                    if memory_content:
                        materials[f"{researcher_folder.name}_memory"] = "\n".join(memory_content)

        return materials

    def get_system_prompt(self) -> str:
        """Generate system prompt for the Policy agent.

        Returns:
            System prompt string
        """
        return f"""You are a Policy Analyst specializing in evidence-based policy development.

Your task is to synthesize research materials into a comprehensive, objective policy proposal for {self.config.target_location}.

Core Principles:
1. OBJECTIVITY: You must remain completely neutral and objective. Do not inject personal opinions or preferences.
2. EVIDENCE-BASED: All recommendations must be derived from the research materials provided.
3. CONTEXT-AWARE: Consider the specific economic, social, and political context of {self.config.target_location}.
4. PRACTICAL: Propose actionable policies that can realistically be implemented.
5. COMPREHENSIVE: Cover short-term (1-2 years), mid-term (3-5 years), and long-term (5+ years) strategies.

Target Location: {self.config.target_location}

Research Topic: {self.topic}

Your proposal should be within {self.config.max_proposal_words} words and include:
- Executive Summary
- Analysis of Research Findings
- Short-term Policies (1-2 years)
- Mid-term Policies (3-5 years)
- Long-term Policies (5+ years)
- Implementation Considerations
- References to research sources

Always cite the specific research materials when making recommendations."""

    def generate_proposal(self) -> Path:
        """Generate the policy proposal by synthesizing all research materials.

        Returns:
            Path to generated PROPOSAL.md
        """
        print(f"\n{'─' * 70}")
        print(f"Policy Agent: {self.config.alias}")
        print(f"{'─' * 70}")

        # Collect all research materials
        print("  Collecting research materials...")
        materials = self.collect_research_materials()

        if not materials:
            print("  Warning: No research materials found. Creating placeholder proposal.")
            return self._create_placeholder_proposal()

        print(f"  Found materials from {len([k for k in materials.keys() if not k.endswith('_memory')])} researchers")

        # Build the research content
        research_content = "\n\n".join([
            f"## Research from {alias.upper()}\n\n{content[:8000]}"
            for alias, content in materials.items()
            if not alias.endswith('_memory')
        ])

        # Create user prompt
        user_prompt = f"""Please synthesize the following research materials into a comprehensive policy proposal for {self.config.target_location}.

Research Topic: {self.topic}

Target Location: {self.config.target_location}

Location Context:
- High cost of living and housing
- Service-oriented economy with strong finance sector
- Aging population
- Limited social safety net traditions
- Close integration with mainland China's economy
- Strong emphasis on education and professional qualifications

{research_content}

---

Generate a comprehensive PROPOSAL.md with:

1. **Executive Summary** - Brief overview of the problem and proposed solutions

2. **Analysis of Research Findings** - Synthesis of key findings from all researchers:
   - Common themes and agreements
   - Divergent viewpoints and debates
   - Evidence gaps that need further investigation

3. **Short-term Policies (1-2 years)** - Immediate actions that can be implemented quickly:
   - Policy measures
   - Expected outcomes
   - Resource requirements

4. **Mid-term Policies (3-5 years)** - Medium-term strategies requiring more planning:
   - Policy measures
   - Expected outcomes
   - Resource requirements

5. **Long-term Policies (5+ years)** - Long-term structural changes:
   - Policy measures
   - Expected outcomes
   - Resource requirements

6. **Implementation Considerations** - Practical factors for {self.config.target_location}:
   - Political feasibility
   - Budget implications
   - Stakeholder impacts
   - Risk mitigation

7. **References** - All research sources cited

Requirements:
- Maximum {self.config.max_proposal_words} words
- Objective and evidence-based (no personal opinions)
- Specific to {self.config.target_location}'s context
- Cite specific researchers when referencing their findings
- Use clear, professional language

Format the output in clear markdown with proper headers."""

        try:
            print("  Generating policy proposal...")
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,  # Lower temperature for more objective output
                max_tokens=6000
            )

            proposal_content = response.choices[0].message.content

            # Add header with metadata
            final_content = f"""# Policy Proposal: {self.topic}

**Policy Agent:** {self.config.alias}
**Target Location:** {self.config.target_location}
**Model:** {self.config.model}
**Language:** {self.config.language}
**Max Words:** {self.config.max_proposal_words}
**Generated:** {get_timestamp()}

---

{proposal_content}

---

*Generated by Multi-Agent Research System - Policy Agent*

## Research Sources

This proposal is based on research conducted by:

"""

            # Add list of researchers
            for alias in materials.keys():
                if not alias.endswith('_memory'):
                    final_content += f"- {alias.upper()}\n"

            final_content += """
---

*Note: This proposal is generated based solely on the research materials provided and aims to be objective and evidence-based.*
"""

        except Exception as e:
            print(f"  Error generating proposal: {e}")
            final_content = self._create_error_proposal(str(e))

        # Write PROPOSAL.md
        proposal_path = self.output_folder / "PROPOSAL.md"
        proposal_path.write_text(final_content, encoding="utf-8")

        print(f"  Proposal saved to: {proposal_path}")
        return proposal_path

    def _create_placeholder_proposal(self) -> Path:
        """Create a placeholder proposal when no research materials are found.

        Returns:
            Path to placeholder PROPOSAL.md
        """
        content = f"""# Policy Proposal: {self.topic}

**Policy Agent:** {self.config.alias}
**Target Location:** {self.config.target_location}
**Generated:** {get_timestamp()}

---

## Notice

No research materials were found. Please ensure that researchers have completed their work before running the Policy agent.

## Expected Research Sources

The Policy agent expects to find SUMMARY.md files from the following researchers in the `{self.base_output_path}` folder:
- Paul (Economic policy expert)
- Mary (Social welfare specialist)
- Ming (Technology and society researcher)

---

*Generated by Multi-Agent Research System - Policy Agent*
"""

        proposal_path = self.output_folder / "PROPOSAL.md"
        proposal_path.write_text(content, encoding="utf-8")
        return proposal_path

    def _create_error_proposal(self, error_message: str) -> str:
        """Create an error proposal content.

        Args:
            error_message: The error message to include

        Returns:
            Error proposal content string
        """
        return f"""# Policy Proposal: {self.topic}

**Policy Agent:** {self.config.alias}
**Target Location:** {self.config.target_location}
**Generated:** {get_timestamp()}

---

## Error

Failed to generate proposal: {error_message}

Please check the API connection and try again.

---

*Generated by Multi-Agent Research System - Policy Agent*
"""
