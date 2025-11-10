import fitz  # PyMuPDF
import pdfplumber
import json
import os, json
from datetime import datetime
from typing import Dict, Any, List, Union
import pypandoc


def extract_text_and_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract text content and metadata from a PDF file.
    Returns a structured dictionary ready for JSON or Markdown conversion.
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        with fitz.open(file_path) as doc:
            metadata = doc.metadata or {}
            pages = []

            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text") or ""
                pages.append({
                    "page_number": page_num,
                    "content": text.strip()
                })

            return {
                "file_name": os.path.basename(file_path),
                "page_count": len(doc),
                "metadata": {
                    "title": metadata.get("title"),
                    "author": metadata.get("author"),
                    "creation_date": metadata.get("creationDate"),
                    "mod_date": metadata.get("modDate"),
                },
                "extracted_at": datetime.now().isoformat(),
                "pages": pages
            }

    except Exception as e:
        return {"error": f"Failed to extract metadata: {str(e)}"}

#this api for converting pdf to json
def extract_text_and_tables_json(pdf_path: str, output_folder: str) -> str:
    """
    Extracts both text and tables from a PDF, saves to JSON file.
    Handles image-based or structured PDFs gracefully.
    """


    os.makedirs(output_folder, exist_ok=True)

    result = {
        "file_name": os.path.basename(pdf_path),
        "extracted_at": datetime.now().isoformat(),
        "pages": []
    }

    try:
        # --- First, use pdfplumber for text + tables ---
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                tables = page.extract_tables() or []

                # If pdfplumber gives no text, try PyMuPDF as fallback
                if not text.strip():
                    doc = fitz.open(pdf_path)
                    if page_num <= len(doc):
                        page_fitz = doc[page_num - 1]
                        text = page_fitz.get_text("blocks") or page_fitz.get_text("layout") or ""

                result["pages"].append({
                    "page_number": page_num,
                    "text": text.strip(),
                    "tables": tables
                })

        # Save JSON
        json_filename = os.path.splitext(os.path.basename(pdf_path))[0] + ".json"
        json_path = os.path.join(output_folder, json_filename)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        return json_path

    except Exception as e:
        error_path = os.path.join(output_folder, "error.json")
        with open(error_path, "w", encoding="utf-8") as f:
            json.dump({"error": str(e)}, f, ensure_ascii=False, indent=4)
        return error_path


#this is for converting pdf to markdown
def extract_pdf_to_markdown(pdf_path: str, output_folder: str) -> str:
    """
    Extracts text + tables from a PDF, converts text to Markdown via Pandoc.
    Handles Pandoc installation automatically.
    """
    os.makedirs(output_folder, exist_ok=True)
    md_filename = os.path.splitext(os.path.basename(pdf_path))[0] + ".md"
    md_path = os.path.join(output_folder, md_filename)

    # Ensure pandoc exists
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        pypandoc.download_pandoc()

    all_text = []
    all_tables = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                all_text.append(f"\n\n## Page {page_num}\n\n{text.strip()}")

                # Extract tables
                tables = page.extract_tables() or []
                for t_index, table in enumerate(tables, start=1):
                    if not table:
                        continue
                    headers = [str(h) if h else "" for h in table[0]]
                    rows = table[1:]
                    md_table = "| " + " | ".join(headers) + " |\n"
                    md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                    for row in rows:
                        md_table += "| " + " | ".join([str(cell) if cell else "" for cell in row]) + " |\n"
                    all_tables.append(f"\n\n### Table {t_index} (Page {page_num})\n{md_table}")

        # Combine extracted text + tables
        combined_text = "\n".join(all_text + all_tables)

        # ✅ FIXED LINE BELOW
        markdown_content = pypandoc.convert_text(combined_text, "md", format="markdown")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return md_path

    except Exception as e:
        error_path = os.path.join(output_folder, "error.md")
        with open(error_path, "w", encoding="utf-8") as f:
            f.write(f"# Markdown Conversion Failed\n\nError: {str(e)}")
        return error_path