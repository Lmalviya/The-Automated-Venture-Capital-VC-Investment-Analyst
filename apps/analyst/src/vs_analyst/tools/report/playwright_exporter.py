# playwright_exporter.py
from pathlib import Path
from langchain_core.tools import tool
from playwright.sync_api import sync_playwright
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

@tool
def playwright_pdf_exporter(html_string: str, output_path: str) -> str:
    """
    Stateless @tool function that spawns headless Playwright Chromium,
    renders the provided HTML string, and exports it as a PDF to the specified output_path.
    Returns the output_path string on success.
    """
    logger.info("Playwright PDF Exporter tool triggered", output_path=output_path)
    try:
        # Ensure output directory exists
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            logger.info("Launching headless Chromium browser")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            logger.info("Setting HTML content in page")
            await_content_load = True
            page.set_content(html_string)
            
            logger.info("Exporting page to PDF", path=output_path)
            page.pdf(
                path=str(out_p.absolute()),
                format="A4",
                print_background=True,
                margin={
                    "top": "20mm",
                    "bottom": "20mm",
                    "left": "20mm",
                    "right": "20mm"
                }
            )
            browser.close()
            
        logger.info("PDF exported successfully via Playwright", path=output_path)
        return output_path
    except Exception as e:
        logger.error("Failed to export PDF via Playwright", error=str(e))
        raise ValueError(f"Playwright PDF export failed: {e}")
