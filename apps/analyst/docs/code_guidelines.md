# Code Organization & Agent Guidelines

This document outlines the strict architectural patterns and code organization guidelines for the VC Investment Analyst Service. Adhering to these guidelines ensures readability, prevents circular dependencies, and maintains modularity.

---

## 1. Project Directory Structure

The canonical source layout for the `vs_analyst` package is shown below. Every new file must be placed in the correct layer — placing code in the wrong layer is a hard failure.

```
apps/analyst/src/vs_analyst/
│
├── agents/           # Pre-configured LLM agent instances bound with tools
│   ├── __init__.py   # AgentRegistry — the single access point for all agents
│   ├── intake.py
│   ├── market.py
│   ├── founder.py     [NEW — to be created]
│   ├── competitor.py  [NEW — to be created]
│   └── ...
│
├── nodes/            # LangGraph node functions — one file per sub-graph
│   ├── __init__.py   # Public exports of all node functions
│   ├── coordinator.py     # Router and join nodes (state transitions only)
│   ├── deck_extraction.py # Intake-phase: parallel deck→state extraction nodes
│   ├── summary.py         # Post-extraction summary node
│   ├── market/        [NEW — to be created]
│   │   ├── __init__.py
│   │   ├── planner.py
│   │   └── synthesizer.py
│   ├── competitor/    [NEW — to be created]
│   ├── founder/       [NEW — to be created]
│   ├── due_diligence/ [NEW — to be created]
│   └── report/        [NEW — to be created]
│
├── services/          [NEW LAYER — to be created]
│   # Pure Python service functions with NO LangChain/LLM dependencies.
│   # The intake extraction logic (file reading, PPTX→PDF conversion,
│   # vision model calls for raw OCR) lives here, not in tools/.
│   ├── __init__.py
│   └── deck_reader.py     [REPLACES tools/file_extractor.py]
│       # Contains: _pdf_extractor(), _pptx_extractor(),
│       #           _convert_pptx_to_pdf_libreoffice(), file_extractor()
│       # Called directly by the intake node, NOT wrapped as a @tool.
│
├── tools/            # Stateless utility functions callable BY agents (not nodes)
│   ├── __init__.py
│   ├── market_tools.py         # Tavily search, web research
│   ├── website_scraper.py      # Stateless scraper tool (returns string)
│   ├── query_pitch_deck.py     # RAG query against extracted deck text
│   └── cognitive_utils.py      [NEW — to be created]
│       # calculate_percentage, parse_numeric_value, years_since, etc.
│
├── orchestrator/     # Graph compilation and public pipeline entrypoint
│   ├── __init__.py
│   ├── pipeline.py        # StateGraph compilation + run_pipeline() entrypoint
│   └── routing_helper.py  # should_continue() and similar routing helpers
│
├── prompts/          # All prompt strings — no inline prompts anywhere else
│   ├── __init__.py   # PromptRegistry enum
│   ├── image.py
│   ├── intak_layer.py
│   └── pitch_deck_prompts.py
│
├── schemas/          # All Pydantic models and TypedDict state definitions
│   ├── __init__.py
│   ├── state.py           # PipelineGraphState, AnalysisState
│   ├── adapters.py        # LLM structured-output extractors (deck→schema)
│   ├── company.py
│   ├── founder.py
│   ├── market.py
│   ├── competitive.py
│   ├── due_diligence.py
│   ├── memo.py
│   ├── shared_enums.py
│   ├── shared_models.py
│   └── user_inputs.py
│
├── utility/          # Cross-cutting infrastructure (logging, LLM client)
│   ├── llm.py             # Singleton LLM instance (llm, query_vision_model, etc.)
│   ├── logs.py            # Structured logger factory (get_logger)
│   └── storage/           # File I/O utilities (e.g., temp dir management)
│
├── managers/         # [DEPRECATED — DO NOT USE OR ADD CODE HERE]
│   # Replaced by the agents/ + nodes/ + services/ separation.
│   # Still present only because pipeline.py has not been migrated yet.
│   # Must be fully removed before the first production release.
│
├── config.py         # App-wide settings (API keys, model names via pydantic-settings)
└── __init__.py
```

> [!WARNING]
> `managers/` is deprecated. `pipeline.py` currently imports from it, but this is a known tech debt item. All new sub-graph nodes must NOT import from `managers/`.

---

## 2. Centralized Prompt Management (`prompts/`)

All prompt templates must reside inside the `vs_analyst/prompts/` package. Prompts should be logically split into modules based on their domain.

### Guidelines
- **No Inline Prompt Strings:** Prompt strings must never be hardcoded inside nodes, tools, or services.
- **Registration Requirement:** Every prompt must be registered as a key in the `PromptRegistry` enum in `prompts/__init__.py`.
- **Format-Ready:** Prompts containing variable slots (e.g., `{TEXT}`) must document their required variables in a comment above the string.

```python
# prompts/intake_layer.py
INTAKE_SYSTEM_PROMPT = "You are a VC intake specialist..."

# prompts/__init__.py
class PromptRegistry(str, Enum):
    intake_system = INTAKE_SYSTEM_PROMPT
```

---

## 3. Centralized Agent Management (`agents/`)

All AI agents must be declared inside the `vs_analyst/agents/` package. Nodes and tools must **never** instantiate `ChatOpenAI`/LLM instances, set model parameters, or bind tools inline.

### Guidelines
- **Registry Access Only:** Agents must only be accessed through the `AgentRegistry` class in `agents/__init__.py`.
- **Zero LLM Instantiations in Nodes:** Nodes call `AgentRegistry.market` not `llm.bind_tools(...)`.
- **One file per sub-graph:** Each new sub-graph (founder, competitor, due_diligence, report) gets its own agent file.

```python
# agents/founder.py
from vs_analyst.utility.llm import llm
from vs_analyst.tools.deep_research import deep_research_tool

FOUNDER_TOOLS = [deep_research_tool]
founder_agent = llm.bind_tools(FOUNDER_TOOLS)

# agents/__init__.py — register it
from .founder import founder_agent
class AgentRegistry:
    founder = founder_agent
```

---

## 4. Strict Layer Boundaries

| Layer | Responsibility | Prohibited Operations |
| :--- | :--- | :--- |
| **Nodes** (`nodes/`) | LangGraph node functions. Read state, invoke agents or services, return state updates. | Do not declare LLM parameters or bind tools. Do not call `@tool` decorated functions directly. |
| **Services** (`services/`) | Pure Python logic that does significant computational work (file I/O, subprocess calls, vision OCR loops). Callable by nodes directly. | Do not import LangGraph, LangChain, or any graph state. Do not use `@tool`. |
| **Agents** (`agents/`) | Pre-configured LLM instances bound to their tool sets. The `AgentRegistry` is the single access point. | Do not modify graph state directly. |
| **Tools** (`tools/`) | Stateless utility functions callable BY agents. Each tool does one thing and returns a serializable result. | Do not access graph state or import from `nodes/`. Do not make LLM calls. |
| **Orchestrator** (`orchestrator/`) | Graph compilation (`StateGraph`) and the `run_pipeline()` entrypoint. | Do not contain domain business logic. |
| **Managers** (`managers/`) | **[DEPRECATED]** Legacy wrapper classes. | Do not write new code here. Do not import from here in new files. |

---

## 5. The Service Layer Pattern — `file_extractor.py` Anti-Pattern

> [!CAUTION]
> `tools/file_extractor.py` **violates the layer boundary rule**. It contains:
> 1. A `@tool` LangChain decorator wrapping complex business logic.
> 2. Direct LLM calls (`query_vision_model`) inside the tool — **tools must never call LLMs**.
> 3. A LangGraph `Command` return — tools must not be graph-aware.
>
> The correct pattern is to move the extraction logic to `services/deck_reader.py` and call it directly from the intake node function. The `@tool` wrapper (`pdf_extractor_tool`) and the `Command` return must be deleted entirely.

### Correct Pattern: Node Calls Service Directly

```
BEFORE (incorrect):
  intake_agent (LLM) → calls @tool pdf_extractor_tool → tool calls query_vision_model → Command updates state

AFTER (correct):
  intake_node (node function) → calls services.deck_reader.file_extractor() → returns PDFExtractorOutput → node updates state
```

**Rule:** The intake agent (`agents/intake.py`) is only needed for tasks that require LLM reasoning — deciding WHAT to do. Reading a file from a known path at the start of a pipeline is deterministic and requires no LLM reasoning. It should be a direct node call, not an agent tool call.

### Migration Plan for the Coding Agent

| Action | Target File | Description |
| :--- | :--- | :--- |
| **MOVE** logic | `tools/file_extractor.py` → `services/deck_reader.py` | Move `_pdf_extractor`, `_pptx_extractor`, `_convert_pptx_to_pdf_libreoffice`, `_file_path_validation`, `file_extractor()`, `ExtractionMode`, `ExtractedPage`, `PDFExtractorOutput` as-is. Remove the `@tool` wrapper and `Command` return. |
| **DELETE** | `tools/file_extractor.py` | After migration, delete this file. |
| **MODIFY** | `nodes/deck_extraction.py` or `nodes/intake_node.py` | Add an `intake_extraction_node` that calls `services.deck_reader.file_extractor()` and writes `raw_deck_text` and `raw_website_text` to state directly. This node runs before the parallel extraction nodes. |
| **MODIFY** | `agents/intake.py` | Remove `pdf_extractor_tool` from `INTAKE_TOOLS`. The intake agent only needs `website_scraper_tool` if website scraping still requires LLM routing, or eliminate the agent entirely if scraping is also moved to a service. |
| **MODIFY** | `managers/intake.py` | Update tool list accordingly (temporary, until managers/ is fully removed). |
| **MODIFY** | `orchestrator/pipeline.py` | Replace the `intake_agent → intake_tools` loop with a direct `intake_extraction_node`. |

---

## 6. Node File Naming Conventions

Each sub-graph gets its own subdirectory inside `nodes/`. Node functions inside are thin: they read from state, call agents/services, and return state updates. Never more than ~50 lines per node function.

```
nodes/
├── founder/
│   ├── __init__.py           # Exports: founder_profiler_node, founder_risk_analyst_node
│   ├── profiler.py           # founder_profiler_node
│   └── risk_analyst.py      # founder_risk_analyst_node
├── competitor/
│   ├── __init__.py
│   ├── finder_planner.py
│   ├── finder_synthesizer.py
│   ├── investigator_planner.py
│   ├── investigator_synthesizer.py
│   └── risk_analyst.py
```

The parent sub-graph compiler file (e.g., `founder_subgraph.py`) lives at `orchestrator/subgraphs/founder_subgraph.py` and imports node functions from `nodes/founder/`.

---

## 7. Single-Pass Unified Extraction (Intake Design)

To optimize cost, performance, and accuracy during intake:
1. **File Extraction Node:** Call `services.deck_reader.file_extractor()` directly. Write result to `raw_deck_text`.
2. **Website Scraping Node:** Call `tools.website_scraper` as a direct service call (not via agent). Write result to `raw_website_text`.
3. **Parallel Extraction Nodes:** Run `deck_to_company`, `deck_to_founder`, `deck_to_market`, `deck_to_competitor`, `deck_to_financials` nodes in parallel. Each uses both `raw_deck_text` and `raw_website_text` as joint context in a single LLM call.
4. **No redundant LLM calls.** The extraction prompt instructs the LLM to resolve conflicts natively (website beats deck for employee count; deck beats website for mission statement).

---

## 8. AI Partner Interaction Guidelines

For all future model interactions, the agent must adhere to the critical, constructive pedagogical model defined in [agent_interaction_guidelines.md](file:///c:/Users/23add/workspace/The-Automated-Venture-Capital-VC-Investment-Analyst/apps/analyst/docs/agent_interaction_guidelines.md). The agent's goal is to actively challenge the developer, audit plans, catch design mistakes, and direct the implementation toward robust architectural patterns.
