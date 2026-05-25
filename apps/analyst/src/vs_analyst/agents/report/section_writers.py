# section_writers.py
from vs_analyst.utility.llm import llm
from vs_analyst.schemas.memo import MemoSection

# All section writers operate strictly on the collected state with NO tools
# and return structured MemoSection objects containing markdown text.

executive_summary_writer_agent = llm.with_structured_output(MemoSection)
market_section_writer_agent = llm.with_structured_output(MemoSection)
competitor_section_writer_agent = llm.with_structured_output(MemoSection)
founder_section_writer_agent = llm.with_structured_output(MemoSection)
dd_section_writer_agent = llm.with_structured_output(MemoSection)
