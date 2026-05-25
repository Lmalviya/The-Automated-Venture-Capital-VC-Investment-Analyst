from typing import List
from vs_analyst.schemas.founder import FounderSchema
\
def merge_founder_records(current: FounderSchema, update: FounderSchema) -> FounderSchema:
    """
    In-place merges fields from update founder into current founder.
    """
    for field in [
        "role", "linkedin_url", "linkedin_summary", "verified_background", "github_url",
        "github_public_repos", "github_account_age", "github_active"
    ]:
        val = getattr(update, field, None)
        if val is not None and val != "":
            setattr(current, field, val)

    # Merge bio_from_deck (only if current doesn't have it)
    if not current.bio_from_deck and update.bio_from_deck:
        current.bio_from_deck = update.bio_from_deck

    # Merge simple lists
    for item in update.past_companies:
        if item not in current.past_companies:
            current.past_companies.append(item)
            
    for item in update.past_roles:
        if item not in current.past_roles:
            current.past_roles.append(item)
            
    if update.notable_achievements:
        if not current.notable_achievements:
            current.notable_achievements = update.notable_achievements
        else:
            for item in update.notable_achievements:
                if item not in current.notable_achievements:
                    current.notable_achievements.append(item)

    if update.red_flags:
        if not current.red_flags:
            current.red_flags = update.red_flags
        else:
            for item in update.red_flags:
                if item not in current.red_flags:
                    current.red_flags.append(item)

    # Github list fields
    for item in update.github_languages:
        if item not in current.github_languages:
            current.github_languages.append(item)
    for item in update.github_oss_notable:
        if item not in current.github_oss_notable:
            current.github_oss_notable.append(item)

    # Merge education sub-models list without duplicates based on collage/level/branch
    if update.education:
        if not current.education:
            current.education = update.education
        else:
            existing_edu = {
                (e.collage.lower() if e.collage else "", 
                 e.level.lower() if e.level else "", 
                 e.branch.lower() if e.branch else "") 
                for e in current.education
            }
            for e in update.education:
                key = (
                    e.collage.lower() if e.collage else "", 
                    e.level.lower() if e.level else "", 
                    e.branch.lower() if e.branch else ""
                )
                if key not in existing_edu:
                    current.education.append(e)
                    existing_edu.add(key)

    return current


def merge_founders_reducer(current: List[FounderSchema], updates: List[FounderSchema]) -> List[FounderSchema]:
    """
    Merges updates into the current list of founders without duplication based on founder name.
    """
    founder_map = {f.name.lower(): f for f in current}
    for updated_founder in updates:
        key = updated_founder.name.lower()
        if key in founder_map:
            founder_map[key] = merge_founder_records(founder_map[key], updated_founder)
        else:
            founder_map[key] = updated_founder
    return list(founder_map.values())
