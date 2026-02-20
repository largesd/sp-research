#!/usr/bin/env python3
"""
Multi-Agent Research Orchestrator

This script orchestrates multiple LLM-based researchers to conduct comprehensive
research on a given topic, with each researcher managing sub-agents for
specialized research areas across multiple rounds.
"""

import sys
from pathlib import Path
from typing import Optional

from config import parse_objective_md
from models import ResearchConfig
from policy_agent import PolicyAgent
from researcher import Researcher
from utils import ensure_directory, load_env_variables


def create_openrouter_client(api_key: str, api_url: str):
    """Create OpenAI client configured for OpenRouter.

    Args:
        api_key: OpenRouter API key
        api_url: OpenRouter API base URL

    Returns:
        OpenAI client instance
    """
    from openai import OpenAI

    return OpenAI(
        base_url=api_url,
        api_key=api_key,
    )


def validate_config(config: ResearchConfig) -> bool:
    """Validate the research configuration.

    Args:
        config: Research configuration

    Returns:
        True if valid, False otherwise
    """
    if not config.topic:
        print("❌ Error: No research topic defined in OBJECTIVE.md")
        return False

    if not config.researchers:
        print("❌ Error: No researchers defined in OBJECTIVE.md")
        return False

    print(f"✅ Configuration validated:")
    print(f"   Topic: {config.topic}")
    print(f"   Researchers: {len(config.researchers)}")
    print(f"   Rounds: {config.research_rounds}")
    print(f"   Sub-agents per researcher: {config.sub_agent_default_count}")

    if config.target_location:
        print(f"   Target Location: {config.target_location}")

    if config.policy_agent:
        print(f"   Policy Agent: Enabled ({config.policy_agent.model})")
        print(f"   Max Proposal Words: {config.policy_agent.max_proposal_words}")

    return True


def run_policy_agent(
    config: ResearchConfig,
    client,
    base_output_path: Path
) -> Optional[Path]:
    """Run the Policy agent to generate policy proposal.

    Args:
        config: Research configuration
        client: OpenAI client instance
        base_output_path: Base path for researcher outputs

    Returns:
        Path to generated PROPOSAL.md or None if disabled
    """
    if not config.policy_agent:
        print("\n⚠️  Policy Agent not configured, skipping proposal generation.")
        return None

    print("\n" + "=" * 70)
    print("📋 Phase 3: Policy Proposal Generation")
    print("=" * 70)

    policy_agent = PolicyAgent(
        config=config.policy_agent,
        topic=config.topic,
        client=client,
        base_output_path=base_output_path
    )

    try:
        proposal_path = policy_agent.generate_proposal()
        return proposal_path
    except Exception as e:
        print(f"\n❌ Error during policy proposal generation: {e}")
        return None


def main():
    """Main entry point for the research orchestrator."""
    print("=" * 70)
    print("🔬 Multi-Agent Research Orchestrator")
    print("=" * 70)

    # Load environment variables
    try:
        api_key, api_url = load_env_variables()
        print(f"\n✅ Loaded environment variables")
        print(f"   API URL: {api_url}")
    except ValueError as e:
        print(f"\n❌ {e}")
        print("\nPlease create a .env file with:")
        print("  OPENROUTER_API_KEY=your_api_key_here")
        print("  OPENROUTER_API_URL=https://openrouter.ai/api/v1")
        sys.exit(1)

    # Parse OBJECTIVE.md
    print("\n📄 Parsing OBJECTIVE.md...")
    try:
        config = parse_objective_md("OBJECTIVE.md")
    except FileNotFoundError:
        print("❌ Error: OBJECTIVE.md not found in current directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error parsing OBJECTIVE.md: {e}")
        sys.exit(1)

    # Validate configuration
    if not validate_config(config):
        sys.exit(1)

    # Create base output directory
    researchers_base = Path("researchers")
    ensure_directory(researchers_base)

    # Create OpenRouter client
    client = create_openrouter_client(api_key, api_url)

    # Initialize and run researchers
    print("\n" + "=" * 70)
    print("🚀 Phase 1 & 2: Starting Research Process")
    print("=" * 70)

    summaries = []

    for i, researcher_config in enumerate(config.researchers, 1):
        print(f"\n{'─' * 70}")
        print(f"Researcher {i}/{len(config.researchers)}")
        print(f"{'─' * 70}")

        # Create researcher
        researcher = Researcher(
            config=researcher_config,
            research_config=config,
            client=client,
            base_output_path=researchers_base
        )

        # Run full research
        try:
            summary_path = researcher.run_full_research()
            summaries.append((researcher_config.alias, summary_path))
        except Exception as e:
            print(f"\n❌ Error during research for {researcher_config.alias}: {e}")
            continue

    # Run Policy Agent if configured
    proposal_path = None
    if config.policy_agent:
        proposal_path = run_policy_agent(config, client, researchers_base)

    # Print final summary
    print("\n" + "=" * 70)
    print("✅ Research Complete!")
    print("=" * 70)
    print(f"\n📁 Research outputs saved in: {researchers_base.absolute()}")

    print("\n📄 Summary files generated:")
    for alias, path in summaries:
        print(f"   - {alias}: {path}")

    if proposal_path:
        print(f"\n📋 Policy Proposal:")
        print(f"   - {config.policy_agent.alias}: {proposal_path}")

    print("\n🎉 All researchers have completed their work!")
    print("   Review the SUMMARY.md files in each researcher folder for results.")
    if proposal_path:
        print(f"   Review the PROPOSAL.md in the {config.policy_agent.alias} folder for the policy proposal.")
    print("=" * 70)


if __name__ == "__main__":
    main()
