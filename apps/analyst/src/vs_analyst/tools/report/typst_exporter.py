# typst_exporter.py
import json
from pathlib import Path
import tempfile
import os
from jinja2 import Template
from langchain_core.tools import tool
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

@tool
def typst_pdf_exporter(sections_json: str, recommendation_json: str, output_path: str) -> str:
    """
    Stateless @tool function that renders a Jinja2 Typst template, writes the .typ file
    to a temporary location, compiles it to a PDF at output_path using the typst library,
    and returns the output_path string on success.
    """
    logger.info("Typst PDF Exporter tool triggered", output_path=output_path)
    try:
        sections = json.loads(sections_json)
        recommendation = json.loads(recommendation_json)
    except Exception as e:
        logger.error("Failed to deserialize JSON in Typst PDF Exporter", error=str(e))
        raise ValueError(f"JSON parsing error: {e}")

    # Build template path
    template_path = Path(__file__).parent / "templates" / "memo_template.typ"
    if not template_path.exists():
        logger.error("Typst memo template not found", path=str(template_path))
        raise FileNotFoundError(f"Template not found at {template_path}")

    # Load template content
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Compile sections map for easy lookups in template
    sections_map = {}
    for s in sections:
        title = s.get("title", "")
        key = title.lower().replace(" ", "_")
        
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

    # Render template via Jinja2
    logger.info("Rendering Typst template via Jinja2")
    template = Template(template_content)
    rendered_typst = template.render(
        sections=sections,
        sections_map=sections_map,
        recommendation=recommendation
    )

    # Write rendered Typst content to temporary file
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_typ_path = Path(tmp_dir) / "document.typ"
        logger.info("Writing temporary .typ file", path=str(temp_typ_path))
        with open(temp_typ_path, "w", encoding="utf-8") as f:
            f.write(rendered_typst)

        # Create parent output directory if needed
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        # Compile .typ to PDF using typst library
        logger.info("Compiling Typst file to PDF", output=output_path)
        try:
            import typst
            typst.compile(str(temp_typ_path), output=str(out_p.absolute()))
            logger.info("Typst compilation completed successfully")
        except Exception as e:
            logger.error("Failed to compile typst file using typst library", error=str(e))
            raise ValueError(f"Typst compilation failed: {e}")

    return output_path
