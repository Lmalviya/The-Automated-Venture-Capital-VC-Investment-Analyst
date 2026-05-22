from enum import Enum

class PipelineStatus(str, Enum):
    PENDING = "pending" # created, not yet started
    RUNNING = "running" # at least one agent is active
    PARTIAL = "partial" # completed with non-fatal errors
    COMPLETE = "complete" # all agents finished successfully
    FAILED = "failed" # fatal error, pipeline stopped

class AgentStatus(str, Enum):
    PENDING = "pending" # not yet called
    RUNNING = "running" # currently executing
    COMPLETE = "complete" # finished, output written to state
    PARTIAL = "partial" # finished, but some tools failed
    FAILED = "failed" # agent itself crashed
    SKIPPED = "skipped" # upstream dep failed, agent not run

class DDStatus(str, Enum):
    PENDING = "pending" # DD Agent hasn't run yet
    VERIFIED = "verified" # background confirmed
    PARTIAL = "partial" # some info found, some missing
    FAILED = "failed" # scraping blocked / no data found

class ConfidenceLevel(str, Enum):
    HIGH = "high" # sourced from industry report / known publication
    MEDIUM = "medium" # inferred from multiple web sources
    LOW = "low" # estimated, weak sourcing

class BusinessModel(str, Enum):
    B2B = "b2b"
    B2C = "b2c"
    B2B2C = "b2b2c"
    MARKETPLACE = "marketplace"
    UNKNOWN = "unknown"

class ProductStage(str, Enum):
    IDEA = "idea" # concept only, no code
    RESEARCH = "research" # customer discovery, no product
    PROTOTYPE = "prototype" # non-functional / demo only

    # ── Building ──────────────────────────────────────────
    MVP = "mvp" # functional, internal / friends use
    PRIVATE_BETA = "private_beta" # invite-only early users
    PUBLIC_BETA = "public_beta" # open but explicitly pre-launch

    # ── Live ──────────────────────────────────────────────
    LAUNCHED = "launched" # v1 live, early paying customers
    GROWTH = "growth" # scaling, product-market fit found
    MATURE = "mature" # established, optimising

    # ── Fallback ──────────────────────────────────────────
    UNKNOWN = "unknown" # Intake Agent could not determine


class ErrorType(str, Enum):
    FILE_NOT_FOUND = "file_not_found"
    PARSE_FAILED = "parse_failed" # PDF/PPTX unreadable
    SCRAPE_BLOCKED = "scrape_blocked" # 429, bot detection
    SCRAPE_EMPTY = "scrape_empty" # page loaded, no useful content
    SEARCH_FAILED = "search_failed" # search API/SearXNG unreachable
    LLM_TIMEOUT = "llm_timeout"
    LLM_PARSE_ERROR = "llm_parse_error" # LLM returned malformed JSON
    VALIDATION_ERROR = "validation_error" # Pydantic rejected output
    UNKNOWN = "unknown"