from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from core import database, models
from core.auth import get_current_user
from core.role_based import (admin_required,user_required)

router = APIRouter()
get_db = database.get_db

@router.put("/soft_delete", dependencies=[Depends(admin_required)])
def soft_delete_template_or_section(
    temp_id: int = None,
    section_id: int = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Soft delete for Template or Section.
    - If temp_id is given: marks Template and its Sections as inactive (is_active = False)
    - If section_id is given: marks only that Section as inactive
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

        # ---------- Template soft delete ----------
        if temp_id:
            template = db.query(models.Template).filter(models.Template.temp_id == temp_id).first()
            if not template:
                raise HTTPException(status_code=404, detail=f"Template ID {temp_id} not found")

            if not template.is_active:
                raise HTTPException(status_code=400, detail="Template already inactive")

            # Mark template as inactive
            template.is_active = False

            # Also mark all sections under it as inactive
            sections = db.query(models.Section).filter(models.Section.template_id == temp_id).all()
            for section in sections:
                section.is_active = False

            db.commit()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": f"Template ID {temp_id} and its sections have been soft deleted successfully"
                }
            )

        # ---------- Section soft delete ----------
        if section_id:
            section = db.query(models.Section).filter(models.Section.section_id == section_id).first()
            if not section:
                raise HTTPException(status_code=404, detail=f"Section ID {section_id} not found")

            if not section.is_active:
                raise HTTPException(status_code=400, detail="Section already inactive")

            section.is_active = False
            db.commit()

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": f"Section ID {section_id} has been soft deleted successfully"}
            )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
