# Directory Structure & File Creation Guide

This is the canonical file creation reference for the VC Investment Analyst coding agent. Every new file must be placed in the layer shown here. Cross-layer placement is a hard failure.

---

## Current State (as-is, before sub-graph implementation)

```
apps/analyst/
├── docs/                                     ← Architecture & design specs
│   ├── nodes/                                ← Per-node/sub-graph spec files
│   │   ├── parent_graph_architecture.md      ← Master pipeline overview
│   │   ├── report_sub_graph.md               ← Report sub-graph full spec
│   │   ├── founder_sub_graph.md
│   │   ├── due_diligence_sub_graph.md
│   │   ├── market_communication_strategy.md
│   │   ├── competitive_communication_strategy.md
│   │   └── ...
│   ├── code_guidelines.md                    ← THIS FILE's companion
│   ├── cognitive_utility_tools.md
│   ├── adversarial_search_tool.md
│   └── agent_interaction_guidelines.md
│
└── src/vs_analyst/
    ├── agents/
    │   ├── __init__.py    ← AgentRegistry
    │   ├── intake.py      ← intake_agent (website_scraper_tool only after migration)
    │   └── market.py      ← market_agent
    │
    ├── managers/          ← [DEPRECATED] Do not add new files here.
    │   ├── intake.py      ← Tech debt: still imported by pipeline.py
    │   └── market.py
    │
    ├── nodes/
    │   ├── __init__.py
    │   ├── coordinator.py
    │   ├── deck_extraction.py
    │   └── summary.py
    │
    ├── orchestrator/
    │   ├── pipeline.py       ← StateGraph compilation
    │   └── routing_helper.py
    │
    ├── prompts/
    │   ├── __init__.py       ← PromptRegistry
    │   ├── image.py
    │   ├── intak_layer.py    ← NOTE: typo in filename (intake), do not rename during coding phase
    │   └── pitch_deck_prompts.py
    │
    ├── schemas/
    │   ├── state.py, adapters.py, company.py, founder.py,
    │   │   market.py, competitive.py, due_diligence.py,
    │   │   memo.py, shared_enums.py, shared_models.py, user_inputs.py
    │
    ├── tools/
    │   ├── file_extractor.py   ← [TO BE DELETED after services/deck_reader.py is created]
    │   ├── market_tools.py
    │   ├── query_pitch_deck.py
    │   └── website_scraper.py
    │
    └── utility/
        ├── llm.py
        ├── logs.py
        └── storage/
```

---

## Target State (after sub-graph implementation)

```
apps/analyst/src/vs_analyst/
│
├── agents/
│   ├── __init__.py           ← AgentRegistry (add each new agent here)
│   ├── intake.py             ← MODIFIED: remove pdf_extractor_tool
│   ├── market.py
│   ├── founder.py            ← [NEW] deep_research_tool bound
│   ├── competitor.py         ← [NEW] adversarial_search_tool bound
│   ├── due_diligence.py      ← [NEW] deep_research_tool + scraper bound
│   └── report/
│       ├── section_writers.py   ← [NEW] no tools (pure LLM synthesis)
│       ├── advisory.py          ← [NEW] advocate, adversary, strategist, mitigator agents
│       └── compiler.py          ← [NEW] jinja2_html_renderer, playwright, typst tool bindings
│
├── nodes/
│   ├── __init__.py             ← export all node functions
│   ├── coordinator.py          ← MODIFIED: add sub-graph join coordinator nodes
│   ├── deck_extraction.py      ← MODIFIED: add intake_extraction_node
│   ├── summary.py
│   ├── market/
│   │   ├── __init__.py
│   │   ├── planner.py          ← [NEW] market_planner_node
│   │   ├── synthesizer.py      ← [NEW] market_synthesizer_node
│   │   └── risk_analyst.py     ← [NEW] market_risk_analyst_node
│   ├── competitor/
│   │   ├── __init__.py
│   │   ├── finder_planner.py
│   │   ├── finder_synthesizer.py
│   │   ├── investigator_planner.py
│   │   ├── investigator_synthesizer.py
│   │   └── risk_analyst.py
│   ├── founder/
│   │   ├── __init__.py
│   │   ├── profiler.py         ← [NEW] founder_profiler_node
│   │   └── risk_analyst.py     ← [NEW] founder_risk_analyst_node
│   ├── due_diligence/
│   │   ├── __init__.py
│   │   ├── extractor.py        ← [NEW] dd_extractor_node
│   │   ├── verifier.py         ← [NEW] verification nodes (legal, traction, press)
│   │   └── synthesizer.py      ← [NEW] dd_synthesizer_node
│   └── report/
│       ├── __init__.py
│       ├── assembler.py        ← [NEW] state_assembler_node
│       ├── section_writers.py  ← [NEW] executive_summary_writer_node, etc.
│       ├── advisory.py         ← [NEW] investment_advocate_node, adversary, strategist, mitigator
│       ├── ic_agent.py         ← [NEW] venture_partner_ic_agent_node
│       ├── reviewer.py         ← [NEW] memo_reviewer_node
│       ├── diagram_generator.py ← [NEW] vector_diagram_generator_node (pure Python SVG)
│       └── compiler.py         ← [NEW] document_compiler_node
│
├── services/                  ← [NEW LAYER]
│   ├── __init__.py
│   └── deck_reader.py         ← [NEW] extracted from tools/file_extractor.py
│       # ExtractionMode, ExtractedPage, PDFExtractorOutput
│       # _file_path_validation(), _pdf_extractor(),
│       # _convert_pptx_to_pdf_libreoffice(), _pptx_extractor()
│       # file_extractor()  ← async public entrypoint
│
├── tools/
│   ├── __init__.py
│   ├── market_tools.py
│   ├── website_scraper.py
│   ├── query_pitch_deck.py
│   ├── cognitive_utils.py     ← [NEW] calculate_percentage, parse_numeric_value,
│   │                                   years_since, get_current_date, count_by_competitor_type
│   ├── deep_research.py       ← [NEW] deep research tool (Tavily/Perplexity wrapper)
│   ├── adversarial_search.py  ← [NEW] adversarial competitor search tool
│   └── report/
│       ├── jinja2_renderer.py    ← [NEW] HTML + Typst template renderer (stateless)
│       ├── playwright_exporter.py ← [NEW] PDF export via headless Playwright
│       └── typst_exporter.py     ← [NEW] PDF export via typst CLI
│
├── orchestrator/
│   ├── pipeline.py             ← MAJOR REFACTOR: replace flat graph with sub-graph calls
│   ├── routing_helper.py
│   └── subgraphs/             ← [NEW]
│       ├── __init__.py
│       ├── company_subgraph.py
│       ├── market_subgraph.py
│       ├── competitor_subgraph.py
│       ├── founder_subgraph.py
│       ├── due_diligence_subgraph.py
│       └── report_subgraph.py
│
├── prompts/
│   ├── __init__.py
│   ├── image.py
│   ├── intak_layer.py
│   ├── pitch_deck_prompts.py
│   ├── founder_prompts.py     ← [NEW]
│   ├── market_prompts.py      ← [NEW] (or extend pitch_deck_prompts.py)
│   ├── competitor_prompts.py  ← [NEW]
│   ├── due_diligence_prompts.py ← [NEW]
│   └── report_prompts.py      ← [NEW] section writer + advisory agent system prompts
│
└── schemas/                   ← No structural changes needed; memo.py already updated
```

---

## File Creation Checklist for the Coding Agent

When creating any new file, validate these four rules before writing code:

1. **Layer Check**: Is it a stateless utility? → `tools/`. Is it complex Python logic? → `services/`. Is it an LLM bound to tools? → `agents/`. Is it a graph node function? → `nodes/`.
2. **Prompt Check**: Does the file contain a prompt string? If yes → move it to `prompts/` and register it in `PromptRegistry`.
3. **Import Check**: Does the file import from the same layer or a higher layer? → Fix it. Allowed import directions: `nodes → agents → tools`, `nodes → services`, `nodes → schemas`, `tools → schemas`.
4. **`__init__.py` Check**: Every new public node function must be re-exported from its package `__init__.py` and the parent `nodes/__init__.py`.

---

## Key Spec References

| Component | Specification |
| :--- | :--- |
| Parent Pipeline | [parent_graph_architecture.md](file:///c:/Users/23add/workspace/The-Automated-Venture-Capital-VC-Investment-Analyst/apps/analyst/docs/nodes/parent_graph_architecture.md) |
| Market Sub-Graph | [market_communication_strategy.md](file:///c:/Users/23add/workspace/The-Automated-Venture-Capital-VC-Investment-Analyst/apps/analyst/docs/nodes/market_communication_strategy.md) |
| Competitor Sub-Graph | [competitive_communication_strategy.md](file:///c:/Users/23add/workspace/The-Automated-Venture-Capital-VC-Investment-Analyst/apps/analyst/docs/nodes/competitive_communication_strategy.md) |
| Founder Sub-Graph | [founder_sub_graph.md](file:///c:/Users/23add/workspace/The-Automated-Venture-Capital-VC-Investment-Analyst/apps/analyst/docs/nodes/founder_sub_graph.md) |
| Due-Diligence Sub-Graph | [due_diligence_sub_graph.md](file:///c:/Users/23add/workspace/The-Automated-Venture-Capital-VC-Investment-Analyst/apps/analyst/docs/nodes/due_diligence_sub_graph.md) |
| Report Sub-Graph | [report_sub_graph.md](file:///c:/Users/23add/workspace/The-Automated-Venture-Capital-VC-Investment-Analyst/apps/analyst/docs/nodes/report_sub_graph.md) |
| Cognitive Utility Tools | [cognitive_utility_tools.md](file:///c:/Users/23add/workspace/The-Automated-Venture-Capital-VC-Investment-Analyst/apps/analyst/docs/cognitive_utility_tools.md) |
| Adversarial Search Tool | [adversarial_search_tool.md](file:///c:/Users/23add/workspace/The-Automated-Venture-Capital-VC-Investment-Analyst/apps/analyst/docs/adversarial_search_tool.md) |
| Code Guidelines | [code_guidelines.md](file:///c:/Users/23add/workspace/The-Automated-Venture-Capital-VC-Investment-Analyst/apps/analyst/docs/code_guidelines.md) |
