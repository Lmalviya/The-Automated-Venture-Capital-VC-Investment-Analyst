# Sub-Graph Specification: Competitor Sub-Graph Strategy

This document describes the compilation, nested loops, parallel map-reduce steps, and state synchronization of the compiled **Competitor Sub-Graph** (`competitor_subgraph`).

---

## 1. Sub-Graph Architecture & Compilation Flow

The Competitor Sub-Graph runs as a nested graph. It coordinates competitor discovery, parallel profiling, and moat assessments.

```mermaid
graph TD
    Start([Start competitor_subgraph]) --> Extract[1. deck_to_competitor]
    Extract --> FinderPlanner[2. competitor_finder_planner]
    FinderPlanner --> FinderRouter{Finder Edge}
    
    FinderRouter -- INCOMPLETE & attempts < Max --> FinderExecutor[3. discovery_executor]
    FinderExecutor --> FinderPlanner
    
    FinderRouter -- COMPLETE or Max Hit --> FinderSynthesizer[4. competitor_finder_synthesizer]
    
    %% Parallel Split
    FinderSynthesizer --> MapSplit[Map Phase: Split per Competitor]
    
    subgraph Parallel Profiling Loop (per Competitor)
        MapSplit --> InvPlanner[5. competitor_investigator_planner]
        InvPlanner --> InvRouter{Investigator Edge}
        InvRouter -- INCOMPLETE & attempts < Max --> InvExecutor[6. profiling_executor]
        InvExecutor --> InvPlanner
        InvRouter -- COMPLETE or Max Hit --> InvSynthesizer[7. competitor_investigator_synthesizer]
    end
    
    InvSynthesizer --> ReduceMerge[Reduce: Key-Based Merge]
    ReduceMerge --> Moat[8. moat_assessment]
    Moat --> Risk[9. competitive_risk_analyst]
    Risk --> End([Exit Sub-Graph])
```

---

## 2. Child State Variable Contracts

The Competitor Sub-Graph contains global and branch-local state namespaces. It writes strictly to `AnalysisState.competitive`.

| Variable | Scope | Type | Owner | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `competitor_search_attempts` | Local (Global to sub-graph) | `int` | Discovery loop | Discovery attempt cutoff (default: 2) |
| `competitor_planner_decision` | Local (Global to sub-graph) | `CompetitorPlannerDecision` | Finder Planner | Controls discovery branch |
| `custom_dimension_keys` | Global | `List[str]` | Finder Synthesizer | Sector-specific dimensions to check |
| `competitor_research_attempts` | Branch-Local | `int` | Profiling loop | Investigator loop cutoff (default: 2) |
| `competitor` | Branch-Local | `CompetitorSchema` | Investigator | Work item profile |

---

## 3. Map-Reduce & State Merging Logic

### 3.1 Map Phase (State Isolation)
When `competitor_finder_synthesizer` locks the final list of candidates, the sub-graph spawns parallel branches, one for each competitor.
* **Isolation Rule**: Each worker runs independently in its own coroutine, writing intermediate crawler summary content strictly to its branch-local `competitor` object.

### 3.2 Reduce Phase (Key-Based Merging)
When the parallel investigator branches complete, they return their updated `CompetitorSchema` records. The sub-graph uses a custom reducer function to merge them without duplication:
```python
def merge_competitors_reducer(current: List[CompetitorSchema], updates: List[CompetitorSchema]) -> List[CompetitorSchema]:
    """
    Merges parallel investigator updates back into the competitor registry.
    """
    competitor_map = {c.name.lower(): c for c in current}
    for updated_competitor in updates:
        key = updated_competitor.name.lower()
        if key in competitor_map:
            # Preserve non-empty fields, merge citations and sources
            competitor_map[key] = merge_competitor_records(competitor_map[key], updated_competitor)
          else:
            competitor_map[key] = updated_competitor
    return list(competitor_map.values())
```

---

## 4. Node Coordination

### 4.1 Step 1: Discovery Loop (`finder_planner` $\rightarrow$ `discovery_executor` $\rightarrow$ `finder_synthesizer`)
* The **Planner** checks coverage. If incomplete, it plans 2-3 discovery queries.
* The **Synthesizer** deduplicates seed + discovered entries, classifies them (`DIRECT`, `INDIRECT`), and selects 2-3 sector-specific custom dimensions.

### 4.2 Step 2: Parallel Investigation Loop (`investigator_planner` $\rightarrow$ `profiling_executor` $\rightarrow$ `investigator_synthesizer`)
* The **Planner** identifies missing fixed or custom dimensions and plans positive/adversarial queries.
* The **Synthesizer** utilizes **cognitive utility tools** (`parse_numeric_value`, `years_since`) to fill dimensions deterministically.

### 4.3 Step 3: Synthesis & Audit (`moat_assessment` $\rightarrow$ `competitive_risk_analyst`)
* The **Moat Assessment Node** applies defensibility frameworks (7 Powers).
* The **Risk Analyst Node** evaluates landscape risks and updates the memo adaptation schemas.
