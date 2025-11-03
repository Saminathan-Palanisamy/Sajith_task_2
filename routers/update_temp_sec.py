from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from core import database
from routers import template_check, section_check
from core import models,schemas
from core.schemas import UpdateDetails
from core.auth import get_current_user
from core.role_based import admin_required

router = APIRouter()
get_db = database.get_db

@router.put("/update_details",dependencies=[Depends(admin_required)])
def update_template_or_section(temp_id: int = None, section_id: int = None, details: UpdateDetails = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """
    Update either template or section based on the given ID.
    - If template_id is provided -> update template name & desc
    - If section_id is provided -> update section name & desc
    """
    try:
        if not temp_id and not section_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either template_id or section_id."
            )
        
        if temp_id and section_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide only one ID (template_id or section_id), not both."
            )

        if temp_id:
            template = db.query(models.Template).filter(models.Template.temp_id == temp_id).first()
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")

            template.Temp_name = details.name
            template.Temp_desc = details.desc
            db.commit()
            db.refresh(template)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": f"Template ID {temp_id} updated successfully", 
                    "temp_id": template.temp_id,
                    "Temp_name": template.Temp_name,
                    "Temp_desc": template.Temp_desc
                    }
            )

        if section_id:
            section = db.query(models.Section).filter(models.Section.section_id == section_id).first()
            if not section:
                raise HTTPException(status_code=404, detail="Section not found")

            section.section_name = details.name
            section.section_desc = details.desc
            db.commit()
            db.refresh(section)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": f"Section ID {section_id} updated successfully", 
                    "section_id": section.section_id,
                    "section_name": section.section_name,
                    "section_desc": section.section_desc
                    }
            )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

