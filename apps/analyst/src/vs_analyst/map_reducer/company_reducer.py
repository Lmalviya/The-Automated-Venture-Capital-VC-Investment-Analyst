from vs_analyst.schemas.company import CompanySchema
from vs_analyst.schemas.shared_enums import BusinessModel

def merge_company_records(current: CompanySchema, update: CompanySchema) -> CompanySchema:
    """
    In-place deep merges fields from update company into current company.
    """
    for field in [
        "name", "founding_year", "problem_statement", "solution",
        "website_url", "sector", "geography", "employee_count",
        "business_model", "value_proposition", "product_stage"
    ]:
        val = getattr(update, field, None)
        if val is not None and val != "" and val != BusinessModel.UNKNOWN:
            setattr(current, field, val)

    # Merge traction sub-model
    if update.traction:
        for field in ["revenue_monthly", "revenue_annual", "user_count", "growth_rate", "key_customers"]:
            val = getattr(update.traction, field, None)
            if val is not None and val != "":
                setattr(current.traction, field, val)
        if update.traction.other_metrics:
            for item in update.traction.other_metrics:
                if item not in current.traction.other_metrics:
                    current.traction.other_metrics.append(item)

    # Merge funding sub-model
    if update.funding:
        for field in ["ask_amount", "valuation"]:
            val = getattr(update.funding, field, None)
            if val is not None and val != "":
                setattr(current.funding, field, val)
        if update.funding.use_of_funds:
            if not current.funding.use_of_funds:
                current.funding.use_of_funds = update.funding.use_of_funds
            else:
                for item in update.funding.use_of_funds:
                    if item not in current.funding.use_of_funds:
                        current.funding.use_of_funds.append(item)
        if update.funding.prior_funding:
            if not current.funding.prior_funding:
                current.funding.prior_funding = update.funding.prior_funding
            else:
                for item in update.funding.prior_funding:
                    if item not in current.funding.prior_funding:
                        current.funding.prior_funding.append(item)

    # Merge extracted_notes
    if update.extracted_notes:
        for item in update.extracted_notes:
            if item not in current.extracted_notes:
                current.extracted_notes.append(item)

    # Merge red_flags
    if update.red_flags:
        for item in update.red_flags:
            if item not in current.red_flags:
                current.red_flags.append(item)

    return current

