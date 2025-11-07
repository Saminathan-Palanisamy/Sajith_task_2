from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from core import database, models, schemas
from core.auth import get_current_user
import os
import uuid
from datetime import datetime
import pytz
from typing import List


router = APIRouter()
get_db = database.get_db

UPLOAD_DIR = "uploads"


@router.post("/upload_pdfs", response_model=schemas.MultipleUploadResponse)
def upload_pdfs(
    template_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload multiple PDF files.
    - Supports Admin and User roles.
    - Stores files in organized folders by year/month/template.
    - Saves metadata in DB.
    """
    try:

        uploaded_docs = []

        user = current_user["user"]

        # Timezone-aware timestamp
        ist = pytz.timezone("Asia/Kolkata")
        upload_time = datetime.now(ist)


        for file in files:
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF file.")

            year = upload_time.strftime("%Y")
            month = upload_time.strftime("%m")
            template_folder = f"template_{template_id}"

            folder_path = os.path.join(UPLOAD_DIR, year, month, template_folder)
            os.makedirs(folder_path, exist_ok=True)

            original_name, ext = os.path.splitext(file.filename)
            unique_suffix = uuid.uuid4().hex[:8]
            safe_filename = f"{original_name}_{unique_suffix}{ext}".replace(" ", "_")
            file_path = os.path.join(folder_path, safe_filename)

            with open(file_path, "wb") as buffer:
                buffer.write(file.file.read())

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
            db.commit()
            db.refresh(new_doc)

            uploaded_docs.append(new_doc)

        return {
            "status": "success",
            "message": f"{len(uploaded_docs)} PDF file(s) uploaded successfully.",
            "uploaded_files": uploaded_docs
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
