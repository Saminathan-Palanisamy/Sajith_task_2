import fitz  # PyMuPDF
import pdfplumber
import json
import os, json
from datetime import datetime
from typing import Dict, Any, List, Union
import pypandoc
import pymupdf4llm, re


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
# def extract_text_and_tables_json(pdf_path: str, output_folder: str) -> str:
#     """
#     Extracts both text and tables from a PDF, saves to JSON file.
#     Handles image-based or structured PDFs gracefully.
#     """


#     os.makedirs(output_folder, exist_ok=True)

#     result = {
#         "file_name": os.path.basename(pdf_path),
#         "extracted_at": datetime.now().isoformat(),
#         "pages": []
#     }

#     try:
#         # --- First, use pdfplumber for text + tables ---
#         with pdfplumber.open(pdf_path) as pdf:
#             for page_num, page in enumerate(pdf.pages, start=1):
#                 text = page.extract_text() or ""
#                 tables = page.extract_tables() or []

#                 # If pdfplumber gives no text, try PyMuPDF as fallback
#                 if not text.strip():
#                     doc = fitz.open(pdf_path)
#                     if page_num <= len(doc):
#                         page_fitz = doc[page_num - 1]
#                         text = page_fitz.get_text("blocks") or page_fitz.get_text("layout") or ""

#                 result["pages"].append({
#                     "page_number": page_num,
#                     "text": text.strip(),
#                     "tables": tables
#                 })

#         # Save JSON
#         json_filename = os.path.splitext(os.path.basename(pdf_path))[0] + ".json"
#         json_path = os.path.join(output_folder, json_filename)
#         with open(json_path, "w", encoding="utf-8") as f:
#             json.dump(result, f, ensure_ascii=False, indent=4)

#         return json_path

#     except Exception as e:
#         error_path = os.path.join(output_folder, "error.json")
#         with open(error_path, "w", encoding="utf-8") as f:
#             json.dump({"error": str(e)}, f, ensure_ascii=False, indent=4)
#         return error_path

def extract_text_and_tables_json(pdf_path: str, output_folder: str) -> str:
    """
    Extracts structured text (with styles) and tables from PDF.
    Output JSON format:
    {
        "paragraphs": [{"text": ..., "style": ...}],
        "tables": [{"TableName": ..., "Rows": [...]}]
    }
    """
    os.makedirs(output_folder, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    json_path = os.path.join(output_folder, base_name + ".json")

    result = {"paragraphs": [], "tables": []}
    try:
        # ----------- Extract Text with Font Styles (Headings, etc.) ----------
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        size = span.get("size", 10)
                        font = span.get("font", "").lower()

                        # Determine style heuristically
                        if size >= 16:
                            style = "H1"
                        elif 13 <= size < 16:
                            style = "H2"
                        elif 11 <= size < 13:
                            style = "H3"
                        else:
                            style = "Normal"

                        result["paragraphs"].append({
                            "text": text,
                            "style": style
                        })

        # ----------- Extract Tables using pdfplumber ----------
        with pdfplumber.open(pdf_path) as pdf:
            table_counter = 1
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    table_name = f"Table_{table_counter}"
                    clean_rows = [
                        [cell if cell is not None else "" for cell in row]
                        for row in table
                    ]
                    result["tables"].append({
                        "TableName": table_name,
                        "Rows": clean_rows
                    })
                    table_counter += 1

        # ----------- Save JSON ----------
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        return json_path

    except Exception as e:
        error_path = os.path.join(output_folder, "error.json")
        with open(error_path, "w", encoding="utf-8") as f:
            json.dump({"error": str(e)}, f, ensure_ascii=False, indent=4)
        return error_path
    
#-----------------------------------------------------------------------------------
def extract_pdf_to_markdown(pdf_path: str, output_folder: str) -> str:
    """
    Extracts a PDF to Markdown with:
    ✅ Per-page headers
    ✅ Clean aligned tables
    ✅ Footer removal (e.g., "Page 1 of 5", "Confidential", etc.)
    ✅ Handles multi-line table cells
    """
    os.makedirs(output_folder, exist_ok=True)
    md_filename = os.path.splitext(os.path.basename(pdf_path))[0] + ".md"
    md_path = os.path.join(output_folder, md_filename)

    try:
        all_pages_md = []
        all_tables_md = []

        # Footer patterns to remove (customizable)
        footer_patterns = [
            r"page\s*\d+\s*of\s*\d+",   # Page 1 of 5
            r"confidential",             # Confidential
            r"inmar\s+internal\s+use",   # Inmar Internal Use
            r"©\s*\d{4}",                # Copyright © 2024
        ]
        footer_regex = re.compile("|".join(footer_patterns), re.IGNORECASE)

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages, start=1):
                # --- Extract text with pymupdf4llm ---
                page_text_md = pymupdf4llm.to_markdown(pdf_path, pages=[page_num - 1])
                cleaned_lines = []

                for line in page_text_md.splitlines():
                    # Skip footer-like lines
                    if footer_regex.search(line.strip()):
                        continue
                    cleaned_lines.append(line)

                page_text_cleaned = "\n".join(cleaned_lines).strip()
                page_section = f"## Page {page_num}\n\n{page_text_cleaned}"
                all_pages_md.append(page_section)

                # --- Extract tables with pdfplumber ---
                tables = page.extract_tables() or []
                for t_index, table in enumerate(tables, start=1):
                    if not table or len(table) < 1:
                        continue

                    # Clean cells (remove newlines, extra spaces)
                    cleaned_table = []
                    for row in table:
                        cleaned_row = []
                        for cell in row:
                            if cell:
                                cell = str(cell).strip().replace("\r", " ").replace("\n", "<br>").replace("  ", " ")
                            else:
                                cell = ""
                            cleaned_row.append(cell)
                        cleaned_table.append(cleaned_row)

                    headers = cleaned_table[0]
                    rows = cleaned_table[1:]

                    # --- Align table columns properly ---
                    col_widths = [
                        max(len(cell) for cell in col)
                        for col in zip(*cleaned_table)
                    ]

                    def pad(cell, width):
                        return cell + " " * (width - len(cell))

                    # Header row
                    header_line = "| " + " | ".join(pad(h, col_widths[i]) for i, h in enumerate(headers)) + " |"
                    divider_line = "| " + " | ".join("-" * col_widths[i] for i in range(len(headers))) + " |"

                    md_table = f"\n\n### Table {t_index} (Page {page_num})\n"
                    md_table += header_line + "\n" + divider_line + "\n"

                    for row in rows:
                        line = "| " + " | ".join(pad(row[i], col_widths[i]) for i in range(len(row))) + " |"
                        md_table += line + "\n"

                    all_tables_md.append(md_table)

        # --- Combine text and tables ---
        final_markdown = "\n\n".join(all_pages_md + all_tables_md)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(final_markdown)

        return md_path

    except Exception as e:
        error_path = os.path.join(output_folder, "error.md")
        with open(error_path, "w", encoding="utf-8") as f:
            f.write(f"# Markdown Conversion Failed\n\nError: {str(e)}")
        return error_path
#-----------------------------------------------------------------------------------
# def extract_pdf_to_markdown(pdf_path: str, output_folder: str) -> str:
#     """
#     Extracts text + tables from a PDF, converts text to Markdown via Pandoc.
#     Handles Pandoc installation automatically.
#     """
#     os.makedirs(output_folder, exist_ok=True)
#     md_filename = os.path.splitext(os.path.basename(pdf_path))[0] + ".md"
#     md_path = os.path.join(output_folder, md_filename)

#     #  Ensure pandoc exists
#     try:
#         pypandoc.get_pandoc_version()
#     except OSError:
#         pypandoc.download_pandoc()

#     all_text = []
#     all_tables = []

#     try:
#         with pdfplumber.open(pdf_path) as pdf:
#             for page_num, page in enumerate(pdf.pages, start=1):
#                 # ---- Extract plain text ----
#                 text = page.extract_text() or ""
#                 if text.strip():
#                     all_text.append(f"\n\n## Page {page_num}\n\n{text.strip()}")
#                 else:
#                     all_text.append(f"\n\n## Page {page_num}\n\n(No readable text found)")

#                 # ---- Extract tables ----
#                 tables = page.extract_tables() or []
#                 for t_index, table in enumerate(tables, start=1):
#                     if not table:
#                         continue

#                     # Clean and ensure all rows are strings
#                     cleaned = [[str(cell or "") for cell in row] for row in table]

#                     headers = cleaned[0]
#                     rows = cleaned[1:] if len(cleaned) > 1 else []

#                     # Markdown table generation
#                     md_table = "| " + " | ".join(headers) + " |\n"
#                     md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
#                     for row in rows:
#                         md_table += "| " + " | ".join(row) + " |\n"

#                     all_tables.append(f"\n\n### Table {t_index} (Page {page_num})\n{md_table}")

#         #  Combine text + tables neatly
#         combined_text = "\n".join(all_text + all_tables)

#         #  Convert with Pandoc to standard Markdown
#         markdown_content = pypandoc.convert_text(
#             combined_text,
#             "md",
#             format="markdown_strict",  # use stricter markdown parsing
#             extra_args=['--wrap=none']  # avoid auto-line wrapping
#         )

#         #  Save to file
#         with open(md_path, "w", encoding="utf-8") as f:
#             f.write(markdown_content)

#         return md_path

#     except Exception as e:
#         error_path = os.path.join(output_folder, "error.md")
#         with open(error_path, "w", encoding="utf-8") as f:
#             f.write(f"# Markdown Conversion Failed\n\nError: {str(e)}")
#         return error_path
#------------------------------------------------------------------------------------------------
#this is for converting pdf to markdown
# def extract_pdf_to_markdown(pdf_path: str, output_folder: str) -> str:
#     """
#     Extracts text + tables from a PDF, converts text to Markdown via Pandoc.
#     Handles Pandoc installation automatically.
#     """
#     os.makedirs(output_folder, exist_ok=True)
#     md_filename = os.path.splitext(os.path.basename(pdf_path))[0] + ".md"
#     md_path = os.path.join(output_folder, md_filename)

#     # Ensure pandoc exists
#     try:
#         pypandoc.get_pandoc_version()
#     except OSError:
#         pypandoc.download_pandoc()

#     all_text = []
#     all_tables = []

#     try:
#         with pdfplumber.open(pdf_path) as pdf:
#             for page_num, page in enumerate(pdf.pages, start=1):
#                 text = page.extract_text() or ""
#                 all_text.append(f"\n\n## Page {page_num}\n\n{text.strip()}")

#                 # Extract tables
#                 tables = page.extract_tables() or []
#                 for t_index, table in enumerate(tables, start=1):
#                     if not table:
#                         continue
#                     headers = [str(h) if h else "" for h in table[0]]
#                     rows = table[1:]
#                     md_table = "| " + " | ".join(headers) + " |\n"
#                     md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
#                     for row in rows:
#                         md_table += "| " + " | ".join([str(cell) if cell else "" for cell in row]) + " |\n"
#                     all_tables.append(f"\n\n### Table {t_index} (Page {page_num})\n{md_table}")

#         # Combine extracted text + tables
#         combined_text = "\n".join(all_text + all_tables)

        
#         markdown_content = pypandoc.convert_text(combined_text, "md", format="markdown")

#         with open(md_path, "w", encoding="utf-8") as f:
#             f.write(markdown_content)

#         return md_path

#     except Exception as e:
#         error_path = os.path.join(output_folder, "error.md")
#         with open(error_path, "w", encoding="utf-8") as f:
#             f.write(f"# Markdown Conversion Failed\n\nError: {str(e)}")
#         return error_path