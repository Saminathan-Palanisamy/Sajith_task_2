from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
import json
from sqlalchemy.orm import Session
from core import database, models, schemas
from core.auth import get_current_user
import os, json
import uuid
from datetime import datetime
import pytz, shutil
from typing import List
from utilities.pdf_extractor import extract_text_and_tables_json, extract_pdf_to_markdown  
from fastapi.responses import JSONResponse


router = APIRouter()
get_db = database.get_db

UPLOAD_DIR = "uploads"

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload_pdfs")
def upload_pdfs(
    template_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload multiple PDF files.
    
    """
    user = current_user["user"]

    #  Validate template existence
    template = db.query(models.Template).filter(
        models.Template.temp_id == template_id,
        models.Template.is_active == True
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail=f"Template with id {template_id} not found.")

    #  Validate user permission
    if user.role.value != "admin" and template.created_by != user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to upload files to this template.")

    #  Prepare folder structure
    ist = pytz.timezone("Asia/Kolkata")
    upload_time = datetime.now(ist)
    year = upload_time.strftime("%Y")
    month = upload_time.strftime("%m")
    template_folder = f"template_{template_id}"
    folder_path = os.path.join("uploads", year, month, template_folder)
    os.makedirs(folder_path, exist_ok=True)

    uploaded_docs = []

    try:
        #  Process each file
        for file in files:
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF file.")

            file.file.seek(0, os.SEEK_END)
            size = file.file.tell()
            file.file.seek(0)
            if size > 50 * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"{file.filename} exceeds 50 MB size limit.")

            # Generate unique file name
            base_name, ext = os.path.splitext(file.filename)
            safe_filename = f"{base_name}_{uuid.uuid4().hex[:8]}{ext}".replace(" ", "_")
            file_path = os.path.join(folder_path, safe_filename)

            # Save file to disk
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Add DB record
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

        db.commit()
        for doc in uploaded_docs:
            db.refresh(doc)

        #  Build JSON-safe response
        uploaded_files = [
            {
                "document_id": doc.document_id,
                "template_id": doc.template_id,
                "file_name": doc.file_name,
                "file_path": doc.file_path,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "is_active": doc.is_active,
            }
            for doc in uploaded_docs
        ]

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "message": f"{len(uploaded_files)} PDF file(s) uploaded successfully.",
                "uploaded_files": uploaded_files,
            }
        )

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
            with open(parsed_json, "r", encoding="utf-8") as jf:
                parsed_json = json.load(jf)
        document.parsed_content = json.dumps(parsed_json, ensure_ascii=False, indent=4)


        #  Extract PDF → Markdown
        markdown_output = extract_pdf_to_markdown(document.file_path, markdown_folder)
        if isinstance(markdown_output, str) and markdown_output.endswith(".md"):
            with open(markdown_output, "r", encoding="utf-8") as mf:
                markdown_text = mf.read()

        else:
            markdown_text = markdown_output
        document.markdown_content = markdown_text



        db.commit()
        db.refresh(document)

        #  Return success response
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "PDF successfully converted to JSON and Markdown.",
                "document_id": document_id,
                "template_id": template_id,
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
#--------------------------------------------------------------------------------------------------------------    
# matching these words are present in JSON that is stored in the database
template_sections = ["scope","purpose"]


@router.post("/matching_words_present")
def find_matching_words(
    template_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user= current_user["user"]
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
    markdown_content= document.markdown_content
    if not markdown_content:
        raise HTTPException(status_code=400, detail="No markdown content found for this document.")
    
    try:
        
        match_results=[]
        for section in template_sections:
            found = section.lower() in markdown_content.lower()
            match_results.append({
                "section": section,
                "message": f"'{section}'-Section {'found' if found else 'not found.'}"
            })

        total_count = len(template_sections)
        count_within_list = total_count
        count_not_found = sum(1 for r in match_results if "not found" in r["message"].lower())
        status_of_matching = "Success" if count_not_found == 0 else "Re-process"

        new_match = models.WordsMatcher(
            temp_id=template_id,
            document_id=document_id,
            user_id=user.id,
            list_to_search=template_sections,
            result=match_results,
            count_within_list=count_within_list,
            count_not_found=count_not_found,
            status_of_matching=status_of_matching            
        )
        db.add(new_match)
        db.commit()
        db.refresh(new_match)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Markdown ellathium thediten.",
                "template_id": template_id,
                "document_id": document_id,
                "word_matcher_id": new_match.word_matcher_id,
                "count_within_list": count_within_list,
                "count_not_found": count_not_found,
                "status_of_matching": status_of_matching,
                "results": match_results
                
            }

        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"matching failed: {str(e)}")

#--------------------------------------------------------------------------------------------------------------  

# creating get api for fetching the status from word_matcher table
@router.get("/matching_status")
def get_matching_status(
    word_matcher_id: int,
    status_filter: str = "both",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Idhula edhachum kodunga: success, reprocess, both
    """
    user = current_user["user"]

    record = db.query(models.WordsMatcher).filter(
        models.WordsMatcher.word_matcher_id == word_matcher_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Record with id {word_matcher_id} not found.")

    try:
        result_data = record.result if isinstance(record.result, list) else json.loads(record.result)
    except Exception:
        raise HTTPException(status_code=500, detail="Error parsing result JSON from database.")

    filtered_results = []
    status_filter = status_filter.lower()

    if status_filter == "success":
        filtered_results = [r for r in result_data if "not found" not in r["message"].lower()]
    elif status_filter in ["reprocess", "re-process"]:
        filtered_results = [r for r in result_data if "not found" in r["message"].lower()]
    elif status_filter == "both":
        filtered_results = result_data
    else:
        raise HTTPException(status_code=400, detail="Invalid status_filter. Use 'success', 'reprocess', or 'both'.")

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "word_matcher_id": word_matcher_id,
            "filter_type": status_filter,
            "results": filtered_results
        }
    )

# Api that shows the "Success", "Re-process" status count and response of entire word_matcher table on onehit.
@router.get("/overall_matching_status_[DB]")
def overall_matching_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Overall status of word_matcher table- [total count um vandhurum, andha column la irundha. Ilana kanakula edukadhu]
    """
    user = current_user["user"]

    try:
        total_records = db.query(models.WordsMatcher).count()
        success_count = db.query(models.WordsMatcher).filter(models.WordsMatcher.status_of_matching == "Success").count()
        reprocess_count = db.query(models.WordsMatcher).filter(models.WordsMatcher.status_of_matching == "Re-process").count()

        # all_records = db.query(models.WordsMatcher).all()
        # records_data = []
        # for record in all_records:
        #     try:
        #         result_data = record.result if isinstance(record.result, list) else json.loads(record.result)
        #     except Exception:
        #         result_data = []

        #     records_data.append({
        #         "word_matcher_id": record.word_matcher_id,
        #         "result": result_data,
        #         "count_within_list": record.count_within_list,
        #         "count_not_found": record.count_not_found,
        #         "status_of_matching": record.status_of_matching
        #     })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total_records": total_records,
                "success_count": success_count,
                "reprocess_count": reprocess_count,
#               "records": records_data
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



