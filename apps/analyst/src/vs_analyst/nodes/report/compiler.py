# compiler.py
import json
from pathlib import Path
from typing import Any, Dict
from vs_analyst.tools.report.jinja2_renderer import jinja2_html_renderer
from vs_analyst.tools.report.playwright_exporter import playwright_pdf_exporter
from vs_analyst.tools.report.typst_exporter import typst_pdf_exporter
from vs_analyst.schemas.state import PipelineGraphState, AnalysisState
from vs_analyst.schemas.shared_enums import AgentStatus, PipelineStatus
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

async def document_compiler_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Document Compiler Node.
    Uses the stateless PDF compiler tools to render both Pattern A (HTML/Playwright)
    and Pattern B (Typst) institutional investment memos and write the absolute paths
    to the state.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    run_id = analysis_state.run_id
    logger.info("Document Compiler node started", run_id=run_id)

    memo = analysis_state.memo
    
    # 1. Gather non-null written sections
    sections_list = []
    for field in [
        "executive_summary",
        "company_overview",
        "market_analysis",
        "competitive_landscape",
        "team_assessment",
        "due_diligence_notes"
    ]:
        val = getattr(memo, field, None)
        if val is not None:
            sections_list.append(val.dict())
            
    # Serialize to JSON strings as required by tools
    sections_json = json.dumps(sections_list, default=str)
    recommendation_json = json.dumps(memo.recommendation.dict() if memo.recommendation else {}, default=str)
    diagrams_json = json.dumps(memo.diagrams, default=str)
    
    # Define outputs directory
    outputs_dir = Path("outputs") / run_id
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    html_pdf_dest = str(outputs_dir / "memo_web.pdf")
    typst_pdf_dest = str(outputs_dir / "memo_typst.pdf")

    try:
        # 2. Render and compile HTML via Playwright
        logger.info("Rending HTML report and compiling via Playwright")
        # Call jinja2_html_renderer tool
        rendered_html = jinja2_html_renderer.invoke({
            "sections_json": sections_json,
            "recommendation_json": recommendation_json,
            "diagrams_json": diagrams_json
        })
        
        # Call playwright_pdf_exporter tool
        playwright_pdf_exporter.invoke({
            "html_string": rendered_html,
            "output_path": html_pdf_dest
        })
        
        # 3. Compile Typst report
        logger.info("Compiling Typst report")
        # Call typst_pdf_exporter tool
        typst_pdf_exporter.invoke({
            "sections_json": sections_json,
            "recommendation_json": recommendation_json,
            "output_path": typst_pdf_dest
        })
        
        # Create state update
        parent_update = AnalysisState(
            run_id=analysis_state.run_id,
            user_input=analysis_state.user_input,
            created_at=analysis_state.created_at
        )
        
        # Store absolute paths to final state
        parent_update.memo.html_pdf_path = str(Path(html_pdf_dest).absolute())
        parent_update.memo.typst_pdf_path = str(Path(typst_pdf_dest).absolute())
        
        # Set overall pipeline status to complete
        parent_update.status = PipelineStatus.COMPLETE
        parent_update.agent_statuses = {"document_compiler": AgentStatus.COMPLETE}
        
        logger.info(
            "Document Compiler completed successfully",
            run_id=run_id,
            html_pdf=parent_update.memo.html_pdf_path,
            typst_pdf=parent_update.memo.typst_pdf_path
        )
        return {"analysis_state": parent_update}

    except Exception as e:
        logger.error("Error in document_compiler_node", run_id=run_id, error=str(e))
        raise e
