# jinja2_renderer.py
import json
from pathlib import Path
from jinja2 import Template
from langchain_core.tools import tool
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

@tool
def jinja2_html_renderer(sections_json: str, recommendation_json: str, diagrams_json: str) -> str:
    """
    Stateless @tool function that renders a Jinja2 HTML template with all memo sections,
    recommendation parameters, and SVG diagrams embedded.
    Returns the rendered HTML string.
    """
    logger.info("Jinja2 HTML Renderer tool triggered")
    try:
        sections = json.loads(sections_json)
        recommendation = json.loads(recommendation_json)
        diagrams = json.loads(diagrams_json)
    except Exception as e:
        logger.error("Failed to deserialize JSON parameters in Jinja2 HTML Renderer", error=str(e))
        raise ValueError(f"JSON parsing error: {e}")

    # Build template path
    template_path = Path(__file__).parent / "templates" / "memo_template.html"
    if not template_path.exists():
        logger.error("HTML memo template not found", path=str(template_path))
        raise FileNotFoundError(f"Template not found at {template_path}")

    # Load template content
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Compile sections map for easy lookups in Jinja template
    # Mapping titles like "Market Analysis" to keys like "market_analysis"
    sections_map = {}
    for s in sections:
        # Check if structure is MemoSection (has title and content)
        title = s.get("title", "")
        key = title.lower().replace(" ", "_")
        
        # Support mapping from titles like "Executive Summary" -> "executive_summary"
        if "executive" in key:
            sections_map["executive_summary"] = s
        elif "market" in key:
            sections_map["market_analysis"] = s
        elif "competitive" in key:
            sections_map["competitive_landscape"] = s
        elif "team" in key:
            sections_map["team_assessment"] = s
        elif "due_diligence" in key or "diligence" in key:
            sections_map["due_diligence_notes"] = s
        else:
            sections_map[key] = s

    # Handle caveats formatting
    # If the state has no caveats, we pass an empty list
    caveats = []
    
    # Render template
    template = Template(template_content)
    rendered_html = template.render(
        sections=sections,
        sections_map=sections_map,
        recommendation=recommendation,
        diagrams=diagrams,
        caveats=caveats
    )

    logger.info("HTML rendering completed successfully", html_size=len(rendered_html))
    return rendered_html
