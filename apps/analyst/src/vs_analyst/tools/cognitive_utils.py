import json
from datetime import date
from langchain_core.tools import tool, BaseTool

# Monkey-patch BaseTool to make @tool decorated functions directly callable for tests and validation
BaseTool.__call__ = lambda self, *args, **kwargs: self.func(*args, **kwargs)

from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


@tool
def get_current_date() -> str:
    """
    Returns the current date in ISO 8601 format (YYYY-MM-DD).
    This provides a reliable temporal baseline to ground the LLM's time-based reasoning.
    """
    logger.info("get_current_date tool invoked")
    return str(date.today())


@tool
def years_since(year: int) -> int:
    """
    Calculates and returns the number of complete years elapsed from a given reference year
    up to the current year. Validates that the input year is at least 1900.

    Args:
        year: The starting/reference year to calculate elapsed years from (e.g., 2017).
    """
    logger.info("years_since tool invoked", year=year)
    if year < 1900:
        raise ValueError("Year must be >= 1900")
    current_year = date.today().year
    return current_year - year


@tool
def calculate_percentage(part: float, whole: float) -> float:
    """
    Given a part and a whole, calculates and returns the percentage that the part
    represents of the whole, rounded to 2 decimal places. If the whole is 0, returns 0.0.

    Args:
        part: The numerator value.
        whole: The denominator value.
    """
    logger.info("calculate_percentage tool invoked", part=part, whole=whole)
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, 2)


@tool
def parse_numeric_value(value_string: str) -> float:
    """
    Parses a human-readable financial or metric string and converts it to a flat USD-equivalent float number.
    Handles currency symbols ($ for USD, € for EUR, ₹ for INR) and multipliers (K, M, B, Cr, L).
    If no currency is specified, USD is assumed. If unparseable, returns 0.0.

    Args:
        value_string: A human-readable financial string (e.g., '$4B', '₹800Cr', '€1.2M', '500k').
    """
    logger.info("parse_numeric_value tool invoked", value_string=value_string)
    s = value_string.strip()
    if not s:
        return 0.0

    # Currency exchange lookup: USD = 1.0, EUR = 1.1, INR = 0.012
    currency_rates = {
        "$": 1.0,
        "€": 1.1,
        "₹": 0.012
    }
    
    rate = 1.0
    symbol_found = None
    for sym, r in currency_rates.items():
        if s.startswith(sym):
            rate = r
            symbol_found = sym
            s = s[len(sym):].strip()
            break

    # Suffix multipliers (including native INR conversions for Indian notation Cr and L)
    suffix_multipliers = {
        "k": 1e3,
        "m": 1e6,
        "b": 1e9,
        "cr": 1e7 * 0.012,
        "l": 1e5 * 0.012
    }

    multiplier = 1.0
    suffix_found = None
    s_lower = s.lower()
    for suff, mult in suffix_multipliers.items():
        if s_lower.endswith(suff):
            multiplier = mult
            suffix_found = suff
            s = s[:-len(suff)].strip()
            break

    # To avoid double conversion when both currency symbol (₹) and Indian suffixes (Cr/L) are found,
    # we override the currency symbol rate to 1.0 since the suffix multiplier already includes the conversion.
    if suffix_found in ("cr", "l") and symbol_found == "₹":
        rate = 1.0

    s = s.replace(",", "")
    try:
        val = float(s)
        return val * rate * multiplier
    except ValueError:
        logger.warning("Unparseable financial or numeric string", value_string=value_string)
        return 0.0


@tool
def count_by_competitor_type(competitors_json: str) -> str:
    """
    Given a JSON string representing a list of competitor objects (each containing a 'competitor_type' field),
    calculates and returns a JSON string detailing the count breakdown of competitor types and the total count.

    Args:
        competitors_json: A JSON string containing a list of competitor objects.
    """
    logger.info("count_by_competitor_type tool invoked")
    try:
        competitors = json.loads(competitors_json)
    except Exception as e:
        logger.warning("Invalid JSON passed to count_by_competitor_type", error=str(e))
        return json.dumps({
            "total": 0,
            "direct": 0,
            "indirect": 0,
            "emerging": 0,
            "substitute": 0
        })

    if not isinstance(competitors, list):
        logger.warning("JSON parsed successfully but is not a list in count_by_competitor_type")
        return json.dumps({
            "total": 0,
            "direct": 0,
            "indirect": 0,
            "emerging": 0,
            "substitute": 0
        })

    counts = {
        "total": len(competitors),
        "direct": 0,
        "indirect": 0,
        "emerging": 0,
        "substitute": 0
    }

    for comp in competitors:
        if not isinstance(comp, dict):
            continue
        comp_type = comp.get("competitor_type")
        if comp_type:
            comp_type_str = str(comp_type).strip().lower()
            if comp_type_str in counts:
                counts[comp_type_str] += 1
            else:
                counts[comp_type_str] = 1

    return json.dumps(counts)
