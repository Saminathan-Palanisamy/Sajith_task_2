import os
import sys

# Add project root (one level up from /test) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utilities.pdf_extractor import extract_text_and_metadata, extract_text_and_tables_json
import json

# 👇 Give the actual path to one of your uploaded PDF files
pdf_path = r"C:\Users\ib-69\Documents\My learnings_Python\Sajith_sample\Task_2_project\uploads\2025\11\template_11\large-doc-testing_b461e938.pdf"

# 👇 Folder to save extracted JSON
output_folder = r"C:\Users\ib-69\Documents\My learnings_Python\Sajith_sample\Task_2_project\uploads\2025\11\template_11\processed"

# Step 1: Extract metadata + text
metadata_result = extract_text_and_metadata(pdf_path)
print("=== Metadata + text ===")
print(json.dumps(metadata_result, indent=4, ensure_ascii=False))

# Step 2: Extract text + tables as JSON file
json_file_path = extract_text_and_tables_json(pdf_path, output_folder)
print("\n=== JSON file saved at ===")
print(json_file_path)

# Step 3 (optional): Print the content of saved JSON
with open(json_file_path, "r", encoding="utf-8") as f:
    json_content = json.load(f)

print("\n=== JSON content preview ===")
print(json.dumps(json_content, indent=4, ensure_ascii=False)[:1000])  # print first 1000 chars
