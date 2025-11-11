from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from core import database, models, schemas
from core.auth import get_current_user
import os, json
import uuid
from datetime import datetime
import pytz
from typing import List
from utilities.pdf_extractor import extract_text_and_tables_json, extract_pdf_to_markdown  


router = APIRouter()
get_db = database.get_db

UPLOAD_DIR = "uploads"

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from core import database, models, schemas
from core.auth import get_current_user
from datetime import datetime
import pytz
import os
import uuid
import shutil
from typing import List

router = APIRouter()
get_db = database.get_db

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload_pdfs", response_model=schemas.MultipleUploadResponse)
def upload_pdfs(
    template_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload multiple PDF files.
    Validations:
    - Template must exist and be active
    - User must have permission
    - Files must be PDF and <= 15MB
    - Saves metadata + stores in year/month/template folder
    """
    user = current_user["user"]

    # --- 1️⃣ Validate template existence ---
    template = db.query(models.Template).filter(
        models.Template.temp_id == template_id,
        models.Template.is_active == True
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail=f"Template with id {template_id} not found.")

    # --- 2️⃣ Validate user permission ---
    if user.role.value != "admin" and template.created_by != user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to upload files to this template.")

    # --- 3️⃣ Prepare folder structure ---
    ist = pytz.timezone("Asia/Kolkata")
    upload_time = datetime.now(ist)
    year = upload_time.strftime("%Y")
    month = upload_time.strftime("%m")
    template_folder = f"template_{template_id}"
    folder_path = os.path.join(UPLOAD_DIR, year, month, template_folder)
    os.makedirs(folder_path, exist_ok=True)

    uploaded_docs = []

    try:
        # --- 4️⃣ Loop through each file with validation ---
        for file in files:
            # Check file extension
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF file.")

            # Check file size (without reading entire file into memory)
            file.file.seek(0, os.SEEK_END)
            size = file.file.tell()
            file.file.seek(0)
            if size > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail=f"{file.filename} exceeds 50 MB size limit.")

            # Generate safe filename
            original_name, ext = os.path.splitext(file.filename)
            safe_filename = f"{original_name}_{uuid.uuid4().hex[:8]}{ext}".replace(" ", "_")
            file_path = os.path.join(folder_path, safe_filename)

            # Efficient file save
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Create new Document record
            new_doc = models.Document(
                template_id=template_id,
                user_id=user.id,
                file_name=file.filename,
                file_path=file_path.replace("\\", "/"),
                uploaded_at=upload_time,
                parsed_content=None,
                markdown_content=None,
                is_active=True
            )
            db.add(new_doc)
            uploaded_docs.append(new_doc)

        # --- 5️⃣ Commit once for all files ---
        db.commit()

        # Refresh objects for response
        for doc in uploaded_docs:
            db.refresh(doc)

        # --- 6️⃣ Build clean response ---
        response_docs = [schemas.DocumentResponse.from_orm(doc) for doc in uploaded_docs]
        return schemas.MultipleUploadResponse(
            status="success",
            message=f"{len(response_docs)} PDF file(s) uploaded successfully.",
            uploaded_files=response_docs
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# validate api for JSON and Markdown conversion
@router.post("/validate_and_convert")
def validate_and_convert(
    template_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    temp id and doc id matum tharuven, rendum okay achuna adha Json and markdown convert pani adhoda path ah matum db la store panuren.
    """
    user = current_user["user"]

    #  Validate template existence
    template = db.query(models.Template).filter(
        models.Template.temp_id == template_id,
        models.Template.is_active == True
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail=f"Template with id {template_id} not found.")

    #  Validate document existence and belonging
    document = db.query(models.Document).filter(
        models.Document.document_id == document_id,
        models.Document.template_id == template_id,
        models.Document.is_active == True
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with id {document_id} not found for this template.")

    #  Check file existence
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Original PDF file not found on disk.")

    #  Prepare folder paths
    ist = pytz.timezone("Asia/Kolkata")
    conversion_time = datetime.now(ist)
    year = conversion_time.strftime("%Y")
    month = conversion_time.strftime("%m")
    template_folder = f"template_{template_id}"

    json_folder = os.path.join(UPLOAD_DIR, year, month, template_folder, "json")
    markdown_folder = os.path.join(UPLOAD_DIR, year, month, template_folder, "markdown")
    os.makedirs(json_folder, exist_ok=True)
    os.makedirs(markdown_folder, exist_ok=True)

    # Generate unique file names
    unique_id = uuid.uuid4().hex[:8]
    json_file_name = f"doc_{document_id}_{unique_id}.json"
    md_file_name = f"doc_{document_id}_{unique_id}.md"

    json_file_path = os.path.join(json_folder, json_file_name)
    md_file_path = os.path.join(markdown_folder, md_file_name)

    try:
        #  Extract PDF → JSON
        parsed_json = extract_text_and_tables_json(document.file_path, json_folder)
        if isinstance(parsed_json, str) and parsed_json.endswith(".json"):  # function already saved file and returned its path
            json_file_path = parsed_json
        else: # function returned data, so we write it
            with open(json_file_path, "w", encoding="utf-8") as jf:
                json.dump(parsed_json, jf, ensure_ascii=False, indent=4)
            return json_file_path


        #  Extract PDF → Markdown
        markdown_text = extract_pdf_to_markdown(document.file_path, markdown_folder)
        if isinstance(markdown_text, str) and markdown_text.endswith(".md"):
            # function already saved file and returned its path
            md_file_path = markdown_text
        else:
            with open(md_file_path, "w", encoding="utf-8") as mf:
                mf.write(markdown_text) 
            return md_file_path


        #  Update DB with file paths (not content)
        document.parsed_content = json_file_path.replace("\\", "/")
        document.markdown_content = md_file_path.replace("\\", "/")
        db.commit()
        db.refresh(document)

        #  Return success response
        return {
            "status": "success",
            "message": "PDF successfully converted to JSON and Markdown.",
            "document_id": document_id,
            "template_id": template_id,
            "json_path": document.parsed_content,
            "markdown_path": document.markdown_content
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")