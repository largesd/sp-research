# Multi-Agent Research System

A Python-based multi-agent research orchestrator that uses multiple LLM models via OpenRouter to conduct comprehensive research on complex topics.

## Features

- **Multiple Researchers**: Deploy multiple LLM models as researchers, each with their own expertise and language
- **Sub-Agent Orchestration**: Each researcher can spawn specialized sub-agents for different research areas
- **Multi-Round Research**: Research proceeds in rounds, with later rounds building on previous findings
- **Structured Output**: All research materials are stored in human-readable markdown with proper citations
- **Memory Management**: Each researcher maintains their own reference folder for research continuity

## Setup

### 1. Create Conda Environment

```bash
conda create -n sp-research python=3.12 -y
conda activate sp-research
```

### 2. Install Dependencies

```bash
pip install openai python-dotenv pyyaml
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=<API_KEY>
OPENROUTER_API_URL=https://openrouter.ai/api/v1
```

Get your API key from [OpenRouter](https://openrouter.ai/keys)

### 4. Customize Research Objective

Edit `OBJECTIVE.md` to define:
- Research topic
- Number of researchers and their configurations
- Sub-agent settings
- Research rounds and areas

### 5. Run the Research

```bash
python main.py
```

## Project Structure

```
.
├── OBJECTIVE.md         # Research configuration and topic definition
├── README.md            # This file
├── .env                 # API keys (ignored by git)
├── .gitignore           # Git ignore rules
├── main.py              # Main orchestrator entry point
├── config.py            # Configuration loader
├── researcher.py        # Researcher agent class
├── sub_agent.py         # Sub-agent class for specialized tasks
├── models.py            # Data models and types
├── utils.py             # Utility functions
└── researchers/         # Output folder (created automatically)
    ├── Paul/            # Researcher folder
    │   ├── memory/      # Research materials and references
    │   └── SUMMARY.md   # Final synthesis
    ├── Mary/
    │   ├── memory/
    │   └── SUMMARY.md
    └── Ming/
        ├── memory/
        └── SUMMARY.md
```

## How It Works

1. **Orchestrator** reads `OBJECTIVE.md` to understand the research configuration
2. **Researchers** are initialized based on the configuration (model, language, alias)
3. **Round 1**: Each researcher spawns sub-agents to gather foundational research
4. **Round 2**: Sub-agents analyze previous findings and conduct deeper research
5. **Summary**: Each researcher synthesizes all findings into `SUMMARY.md`

## Customization

### Adding More Researchers

Edit `OBJECTIVE.md` and add entries to the Researchers table:

```markdown
| Alice  | google/gemini-pro | English | Futurist analyst |
```

### Changing Research Topic

Simply edit the "Research Topic" section in `OBJECTIVE.md`.

### Adjusting Sub-Agent Count

Modify the "Default count per researcher" in `OBJECTIVE.md`.
