from vs_analyst.schemas.competitive import CompetitorSchema
from typing import List

def merge_competitor_records(current: CompetitorSchema, update: CompetitorSchema) -> CompetitorSchema:
    """
    In-place merges fields from update competitor into current competitor.
    """
    for field in [
        "funding_stage", "funding_amount", "geography", "business_model",
        "founding_year", "positioning"
    ]:
        val = getattr(update, field, None)
        if val is not None and val != "":
            setattr(current, field, val)
            
    # Merge custom dimensions dict
    if update.custom_dimensions:
        current.custom_dimensions.update(update.custom_dimensions)
        
    # Merge key strengths list without duplicates
    for item in update.key_strengths:
        if item not in current.key_strengths:
            current.key_strengths.append(item)
            
    # Merge key weaknesses list without duplicates
    for item in update.key_weaknesses:
        if item not in current.key_weaknesses:
            current.key_weaknesses.append(item)
            
    # Merge profiling notes without duplicates
    for item in update.profiling_notes:
        if item not in current.profiling_notes:
            current.profiling_notes.append(item)
            
    # Merge sources list
    existing_urls = {src.url for src in current.sources if src.url}
    for src in update.sources:
        if src.url and src.url not in existing_urls:
            current.sources.append(src)
            existing_urls.add(src.url)
            
    return current


def merge_competitors_reducer(current: List[CompetitorSchema], updates: List[CompetitorSchema]) -> List[CompetitorSchema]:
    """
    Merges updates into the current list of competitors without duplication based on competitor name.
    """
    competitor_map = {c.name.lower(): c for c in current}
    for updated_competitor in updates:
        key = updated_competitor.name.lower()
        if key in competitor_map:
            competitor_map[key] = merge_competitor_records(competitor_map[key], updated_competitor)
        else:
            competitor_map[key] = updated_competitor
    return list(competitor_map.values())
