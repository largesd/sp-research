"""Sub-agent implementation for specialized research tasks."""

import json
from pathlib import Path
from typing import Optional

from openai import OpenAI

from models import ResearchNote
from utils import get_timestamp


class SubAgent:
    """A specialized sub-agent for conducting research in a specific area."""
    
    def __init__(
        self,
        name: str,
        expertise: str,
        client: OpenAI,
        model: str,
        language: str,
        researcher_alias: str
    ):
        """Initialize a sub-agent.
        
        Args:
            name: Sub-agent name/identifier
            expertise: Area of expertise
            client: OpenAI client instance
            model: LLM model name
            language: Language to use for research
            researcher_alias: Parent researcher alias
        """
        self.name = name
        self.expertise = expertise
        self.client = client
        self.model = model
        self.language = language
        self.researcher_alias = researcher_alias
    
    def get_system_prompt(self, topic: str) -> str:
        """Generate system prompt for this sub-agent.
        
        Args:
            topic: Research topic
            
        Returns:
            System prompt string
        """
        return f"""You are a specialized research assistant named "{self.name}" working under {self.researcher_alias}.

Your Expertise: {self.expertise}
Research Topic: {topic}
Language: {self.language}

Your role is to conduct focused, in-depth research in your area of expertise.
You will be given a specific research task and should provide:
1. Comprehensive findings with clear structure
2. Proper citations and sources for all information
3. Analysis and insights relevant to the main topic
4. References to origin of information (URLs, papers, reports, etc.)

Always format your response as valid JSON with this structure:
{{
    "title": "Research Title",
    "content": "Detailed research findings in markdown format",
    "sources": ["Source 1", "Source 2", "..."],
    "key_insights": ["Insight 1", "Insight 2", "..."]
}}

Be thorough but concise. Focus on factual, well-sourced information."""
    
    def research(
        self,
        topic: str,
        round_num: int,
        previous_context: str = "",
        specific_task: Optional[str] = None
    ) -> ResearchNote:
        """Conduct research on the given topic.
        
        Args:
            topic: Research topic
            round_num: Current research round
            previous_context: Context from previous rounds
            specific_task: Optional specific task instructions
            
        Returns:
            ResearchNote with findings
        """
        system_prompt = self.get_system_prompt(topic)
        
        # Build user prompt based on round and context
        if round_num == 1:
            task_desc = specific_task or f"Conduct foundational research on how {self.expertise} relates to the topic."
            user_prompt = f"""Round {round_num} Research Task:

{task_desc}

Research Topic: {topic}

Provide comprehensive findings including:
- Key facts and data points
- Relevant theories or frameworks
- Current state of knowledge
- Important sources and references

Respond in the specified JSON format."""
        else:
            task_desc = specific_task or f"Analyze previous findings and conduct deeper research on {self.expertise}."
            user_prompt = f"""Round {round_num} Research Task:

{task_desc}

Research Topic: {topic}

Previous Research Context:
{previous_context if previous_context else "No previous research available."}

Based on the previous findings, provide:
- Critical analysis of existing information
- New insights and deeper understanding
- Identification of gaps or contradictions
- Actionable recommendations
- Additional sources and references

Respond in the specified JSON format."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                # Clean up markdown code blocks if present
                if content.strip().startswith('```json'):
                    content = content.strip()[7:]
                    if content.endswith('```'):
                        content = content[:-3]
                elif content.strip().startswith('```'):
                    content = content.strip()[3:]
                    if content.endswith('```'):
                        content = content[:-3]
                
                data = json.loads(content.strip())
                
                # Combine content and key_insights
                full_content = data.get("content", "")
                if data.get("key_insights"):
                    full_content += "\n\n### Key Insights\n\n"
                    for insight in data["key_insights"]:
                        full_content += f"- {insight}\n"
                
                return ResearchNote(
                    title=data.get("title", f"Research on {self.expertise}"),
                    content=full_content,
                    sources=data.get("sources", []),
                    round_num=round_num,
                    sub_agent_name=self.name,
                    timestamp=get_timestamp()
                )
                
            except json.JSONDecodeError:
                # Fallback: treat entire response as content
                return ResearchNote(
                    title=f"Research on {self.expertise} - Round {round_num}",
                    content=content,
                    sources=[],
                    round_num=round_num,
                    sub_agent_name=self.name,
                    timestamp=get_timestamp()
                )
                
        except Exception as e:
            return ResearchNote(
                title=f"Error in Research - {self.name}",
                content=f"Error conducting research: {str(e)}",
                sources=[],
                round_num=round_num,
                sub_agent_name=self.name,
                timestamp=get_timestamp()
            )
    
    def save_research_note(self, note: ResearchNote, memory_folder: Path) -> Path:
        """Save a research note to the memory folder.
        
        Args:
            note: ResearchNote to save
            memory_folder: Path to memory folder
            
        Returns:
            Path to saved file
        """
        from utils import sanitize_filename
        
        filename = f"round{note.round_num}_{sanitize_filename(self.name)}_{sanitize_filename(note.title)[:50]}.md"
        filepath = memory_folder / filename
        
        # Format content with metadata
        content = f"""# {note.title}

**Sub-Agent:** {note.sub_agent_name}  
**Researcher:** {self.researcher_alias}  
**Round:** {note.round_num}  
**Timestamp:** {note.timestamp}

---

{note.content}

---

## Sources & References

"""
        if note.sources:
            for source in note.sources:
                content += f"- {source}\n"
        else:
            content += "*No sources provided*\n"
        
        filepath.write_text(content, encoding="utf-8")
        return filepath
