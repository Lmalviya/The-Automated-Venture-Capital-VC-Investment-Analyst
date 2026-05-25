from vs_analyst.schemas.market import MarketSchema
from vs_analyst.schemas.shared_enums import ConfidenceLevel

def merge_market_records(current: MarketSchema, update: MarketSchema) -> MarketSchema:
    """
    In-place deep merges fields from update market into current market.
    """
    for size_type in ["tam", "sam", "som"]:
        u_size = getattr(update, size_type, None)
        if u_size:
            c_size = getattr(current, size_type)
            for field in ["value", "year", "source", "source_url", "notes"]:
                val = getattr(u_size, field, None)
                if val is not None and val != "":
                    setattr(c_size, field, val)
            if u_size.confidence != ConfidenceLevel.LOW:
                c_size.confidence = u_size.confidence

    for field in ["growth_rate", "growth_source", "summary"]:
        val = getattr(update, field, None)
        if val is not None and val != "":
            setattr(current, field, val)

    if update.overall_confidence != ConfidenceLevel.LOW:
        current.overall_confidence = update.overall_confidence

    if update.key_trends:
        for item in update.key_trends:
            if item not in current.key_trends:
                current.key_trends.append(item)

    if update.market_risks:
        for item in update.market_risks:
            if item not in current.market_risks:
                current.market_risks.append(item)

    # Merge research_sources
    if update.research_sources:
        existing_urls = {src.url for src in current.research_sources if src.url}
        for src in update.research_sources:
            if src.url and src.url not in existing_urls:
                current.research_sources.append(src)
                existing_urls.add(src.url)

    # Merge queries_used
    if update.queries_used:
        for item in update.queries_used:
            if item not in current.queries_used:
                current.queries_used.append(item)

    return current

