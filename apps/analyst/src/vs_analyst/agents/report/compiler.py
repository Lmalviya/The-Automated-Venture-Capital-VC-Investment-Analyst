# compiler.py
from vs_analyst.utility.llm import llm
from vs_analyst.tools.report.jinja2_renderer import jinja2_html_renderer
from vs_analyst.tools.report.playwright_exporter import playwright_pdf_exporter
from vs_analyst.tools.report.typst_exporter import typst_pdf_exporter

# Pre-configure compiler agent bound with its rendering & export tools
compiler_agent = llm.bind_tools([
    jinja2_html_renderer,
    playwright_pdf_exporter,
    typst_pdf_exporter,
])
