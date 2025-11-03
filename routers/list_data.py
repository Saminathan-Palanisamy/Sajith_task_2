# routers/list_data.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from core import database, models, schemas
from core.auth import get_current_user
from core.role_based import admin_or_user_required

router = APIRouter()
get_db = database.get_db

# -------------------------------------------------------------
# Role-based list API
# -------------------------------------------------------------
@router.get("/list_items", dependencies=[Depends(admin_or_user_required)])
def list_templates_or_sections(
    temp_id: int = None,
    template: bool = False,
    section: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Lists templates or sections based on query params.

    - Only active ones shown for normal users
    - Admins can view all (active + inactive)
    - Section list pakanum na template false la vechu parunga, then temp_id kodunga.
    - NOTE: Provide either `template=True` or `section= True`, not both.
    - Selective section list pakanum na `temp_id` kodunga, ilana empty ah vitrunga ellame kamikum.
    """

    user = current_user["user"]
    is_admin = user.role.value == "admin"

    try:
        # -----------------------------------------------------
        # List Templates
        # -----------------------------------------------------
        if template:
            query = db.query(models.Template)
            if not is_admin:
                query = query.filter(models.Template.is_active == True)
            templates = query.all()

            if not templates:
                raise HTTPException(status_code=404, detail="No templates found.")

            data = [
                {
                    "temp_id": t.temp_id,
                    "Temp_name": t.Temp_name,
                    "Temp_desc": t.Temp_desc,
                    "created_by": t.created_by,
                    "is_active": t.is_active,
                }
                for t in templates
            ]
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Templates fetched successfully",
                    "count": len(data),
                    "data": data,
                },
            )

        # -----------------------------------------------------
        # List Sections
        # -----------------------------------------------------
        elif section:
            query = db.query(models.Section)
            if temp_id:
                query = query.filter(models.Section.template_id == temp_id)
            if not is_admin:
                query = query.filter(models.Section.is_active == True)
            sections = query.all()

            if not sections:
                raise HTTPException(status_code=404, detail="No sections found.")

            data = [
                {
                    "section_id": s.section_id,
                    "section_name": s.section_name,
                    "section_desc": s.section_desc,
                    "template_id": s.template_id,
                    "order": s.order,
                    "is_active": s.is_active,
                }
                for s in sections
            ]
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Sections fetched successfully",
                    "count": len(data),
                    "data": data,
                },
            )

        # -----------------------------------------------------
        # If neither flag provided
        # -----------------------------------------------------
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either template=True or section=True in query params.",
            )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
