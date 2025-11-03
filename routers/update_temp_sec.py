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

@router.put("/update_details", dependencies=[Depends(admin_required)])
def update_template_or_section(
    temp_id: int = None,
    section_id: int = None,
    details: schemas.UpdateDetails = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
     Unified Update API
    - Updates either Template or Section based on the provided ID.
    - Uses shared schema: UpdateDetails (name, desc).
    - Performs validation, duplication checks, and consistent JSON response.
    """
    try:
        # --- Step 1: Ensure only one ID is provided ---
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

        # --- Step 2: Validate details payload ---
        if not details or (not details.name and not details.desc):
            raise HTTPException(
                status_code=400,
                detail="At least one field (name or desc) is required to update."
            )

        name = details.name.strip() if details.name else None
        desc = details.desc.strip() if details.desc else None

        # --- Step 3: Template update logic ---
        if temp_id:
            template = db.query(models.Template).filter(models.Template.temp_id == temp_id).first()
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")

            #  Check for duplicate template name
            if name and name != template.Temp_name:
                existing_name = (
                    db.query(models.Template)
                    .filter(models.Template.Temp_name == name)
                    .filter(models.Template.temp_id != temp_id)
                    .first()
                )
                if existing_name:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Template name '{name}' already exists."
                    )
                template.Temp_name = name

            if desc:
                template.Temp_desc = desc

            db.commit()
            db.refresh(template)

            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": f"Template ID {temp_id} updated successfully",
                    "data": {
                        "temp_id": template.temp_id,
                        "Temp_name": template.Temp_name,
                        "Temp_desc": template.Temp_desc,
                        "created_by": template.created_by
                    }
                }
            )

        # --- Step 4: Section update logic ---
        if section_id:
            section = db.query(models.Section).filter(models.Section.section_id == section_id).first()
            if not section:
                raise HTTPException(status_code=404, detail="Section not found")

            #  Check for duplicate section name under same template
            if name and name != section.section_name:
                existing_name = (
                    db.query(models.Section)
                    .filter(models.Section.section_name == name)
                    .filter(models.Section.template_id == section.template_id)
                    .filter(models.Section.section_id != section_id)
                    .first()
                )
                if existing_name:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Section name '{name}' already exists under this template."
                    )
                section.section_name = name

            if desc:
                section.section_desc = desc

            db.commit()
            db.refresh(section)

            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": f"Section ID {section_id} updated successfully",
                    "data": {
                        "section_id": section.section_id,
                        "section_name": section.section_name,
                        "section_desc": section.section_desc,
                        "template_id": section.template_id,
                        "order": section.order
                    }
                }
            )

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

