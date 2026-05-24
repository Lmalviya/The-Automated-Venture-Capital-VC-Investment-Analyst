import asyncio
import base64
import tempfile
import subprocess
import os
from enum import Enum
from pathlib import Path
from typing import Any, List, Dict, Tuple

import fitz
from pydantic import BaseModel

from vs_analyst.prompts import PromptRegistry
from vs_analyst.utility.llm import query_vision_model
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

class ExtractionMode(str, Enum):
    IMAGE_MODEL = "image_model"
    NORMAL = "normal"

class ExtractedPage(BaseModel):
    page_number: int
    mode: ExtractionMode
    text: str
    char_count: int = 0

class PDFExtractorOutput(BaseModel):
    file_path: str
    file_type: str
    page_count: int
    pages: List[ExtractedPage]
    total_chars: int
    output: Dict[str, Any] = {}


def _pdf_extractor(file_path: Path, log) -> List[ExtractedPage]:
    """
    Extracts text and page information from a PDF file.
    Attempts to use an image-based vision model for high-fidelity extraction,
    and falls back to direct PDF text extraction upon failure.
    """
    log.info("Running PDF extractor", file_path=str(file_path))
    doc = fitz.open(file_path)

    extracted_pages = []
    for i in range(len(doc)):
        page = doc[i]
        pix = page.get_pixmap(dpi=150)

        try:
            # Convert Pixmap to base64 encoded PNG for the vision model
            png_bytes = pix.tobytes("png")
            base64_image = base64.b64encode(png_bytes).decode("utf-8")

            system_prompt = PromptRegistry.image_analysis.value
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Analyze the PDF page {i} extremely carefully and extract all text and structured information."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]

            extracted_text = query_vision_model(messages, log)
            if not extracted_text or not len(extracted_text.strip()):
                log.warning("Nothing extracted from the page image, using empty placeholder", page_number=i)
                extracted_text = ""

            log.info("Content extracted successfully using vision model", page_number=i)
            extracted_pages.append(
                ExtractedPage(
                    page_number=i,
                    text=extracted_text,
                    char_count=len(extracted_text),
                    mode=ExtractionMode.IMAGE_MODEL,
                )
            )

        except Exception as e:
            log.warning(
                "Vision model extraction failed, falling back to direct PDF text extraction",
                page_number=i,
                error=str(e),
            )
            extracted_text = page.get_text()
            extracted_pages.append(
                ExtractedPage(
                    page_number=i,
                    text=extracted_text,
                    char_count=len(extracted_text),
                    mode=ExtractionMode.NORMAL,
                )
            )

    return extracted_pages


def _convert_pptx_to_pdf_libreoffice(pptx_path: Path, output_dir: Path, log) -> Path:
    """
    Converts a PPTX file to PDF using headless LibreOffice.
    Returns the Path to the generated PDF file.
    """
    log.info("Converting PPTX to PDF using LibreOffice", pptx_path=str(pptx_path))
    
    commands_to_try = []
    
    # 1. First priority: Check environment variables for cloud / custom configurations
    env_path = os.environ.get("SOFFICE_PATH") or os.environ.get("LIBREOFFICE_PATH")
    if env_path:
        commands_to_try.append(env_path)
        
    # 2. Second priority: Standard executable names on the system PATH
    commands_to_try.extend(["soffice", "libreoffice"])
    
    # 3. Third priority: Friendly developer fallback for local Windows environments
    if os.name == "nt":
        typical_paths = [
            Path("C:/Program Files/LibreOffice/program/soffice.exe"),
            Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
        ]
        for p in typical_paths:
            if p.exists() and str(p) not in commands_to_try:
                commands_to_try.append(str(p))
                
    success = False
    last_err = None
    for cmd in commands_to_try:
        try:
            # Command syntax: soffice --headless --convert-to pdf --outdir <output_dir> <pptx_path>
            args = [cmd, "--headless", "--convert-to", "pdf", "--outdir", str(output_dir), str(pptx_path)]
            log.info("Attempting LibreOffice conversion command", cmd=cmd)
            result = subprocess.run(args, capture_output=True, text=True, check=True)
            success = True
            break
        except Exception as e:
            last_err = e
            log.debug("LibreOffice command attempt failed", cmd=cmd, error=str(e))
            
    if not success:
        log.error("Failed to convert PPTX to PDF using LibreOffice", error=str(last_err))
        raise RuntimeError(f"LibreOffice conversion failed. Is LibreOffice installed? Error: {last_err}")
        
    pdf_path = output_dir / (pptx_path.stem + ".pdf")
    if not pdf_path.exists():
        raise FileNotFoundError(f"LibreOffice conversion succeeded but expected PDF not found: {pdf_path}")
        
    log.info("Successfully converted PPTX to PDF", pdf_path=str(pdf_path))
    return pdf_path


def _pptx_extractor(file_path: Path, log) -> List[ExtractedPage]:
    """
    Extracts text and slide information from a PPTX file.
    Converts it to PDF using headless LibreOffice and processes it using the PDF extractor.
    """
    log.info("Starting PPTX extraction by converting to PDF via LibreOffice", file_path=str(file_path))
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_dir = Path(tmp_dir)
        try:
            pdf_path = _convert_pptx_to_pdf_libreoffice(file_path, temp_dir, log)
            extracted_pages = _pdf_extractor(pdf_path, log)
            return extracted_pages
        except Exception as e:
            log.error("Failed PPTX extraction via LibreOffice conversion", error=str(e))
            return []


def _file_path_validation(file_path: Path, log) -> None:
    """
    Validates that the file exists and is of a supported type (.pdf or .pptx).
    """
    log.info("Validating file path and extension", file_path=str(file_path))
    if not file_path.exists():
        log.error("File path does not exist", file_path=str(file_path))
        raise ValueError(f"File does not exist on given path: {file_path}")

    file_extension = file_path.suffix.lower()
    if file_extension not in (".pdf", ".pptx"):
        log.error(
            "Unsupported file extension",
            file_path=str(file_path),
            extension=file_extension,
        )
        raise ValueError(
            f"File format {file_extension} is not supported. Only .pdf and .pptx are supported."
        )


async def file_extractor(file_path: Path, run_id: str, log) -> PDFExtractorOutput:
    """
    The main file extraction entrypoint. Route by file type and extract text page-by-page.
    """
    log.info("Starting file extraction", run_id=run_id, file_path=str(file_path))

    # Step 0 - Validate file path
    _file_path_validation(file_path, log)

    # Step 1 — Route by file type
    file_extension = file_path.suffix.lower()
    pages = []
    if file_extension == ".pdf":
        pages = _pdf_extractor(file_path, log)
    elif file_extension == ".pptx":
        pages = _pptx_extractor(file_path, log)

    page_count = len(pages)
    full_text = "\n".join([p.text for p in pages])
    total_chars = len(full_text)

    log.info(
        "File extraction completed successfully",
        page_count=page_count,
        total_chars=total_chars,
    )

    return PDFExtractorOutput(
        file_path=str(file_path),
        file_type="pdf" if file_extension == ".pdf" else "pptx",
        page_count=page_count,
        pages=pages,
        total_chars=total_chars,
        output={}
    )
