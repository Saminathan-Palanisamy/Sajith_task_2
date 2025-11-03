from core import schemas, models, database
from core.role_based import (admin_required, user_required)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from core.auth import get_current_user


router = APIRouter()
get_db = database.get_db


#---create details to template check
@router.post("/fill", response_model=schemas.TemplateRead, dependencies=[Depends(admin_required)])
def create_template(template: schemas.TemplateCreate, db: Session = Depends(database.get_db),current_user: models.User = Depends(get_current_user)):
    try:
        db_template = db.query(models.Template).filter(models.Template.Temp_name == template.Temp_name).first()
        if db_template:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Template name already exists")

        new_template = models.Template(
            Temp_name=template.Temp_name,
            Temp_desc=template.Temp_desc,
            created_by=template.created_by
        )
        db.add(new_template)
        db.commit()
        db.refresh(new_template)
        
        response_template = {
            "temp_id": new_template.temp_id,
            "Temp_name": new_template.Temp_name,
            "Temp_desc": new_template.Temp_desc,
            "created_by": new_template.created_by
        }
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "message": "Template created successfully",
                "data": response_template
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#-------------------------------------------------------------------------------
@router.put("/update_template_details", dependencies=[Depends(admin_required)])
def update_template_details(
    temp_id: int,
    details: schemas.UpdateDetails,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update template name and description by template ID.
    Uses common schema: UpdateDetails (name, desc)
    """
    try:
        #  Fetch template by ID
        db_template = db.query(models.Template).filter(models.Template.temp_id == temp_id).first()
        if not db_template:
            raise HTTPException(status_code=404, detail="Template not found")

        #  Validate name uniqueness (ignore current template)
        existing_name = (
            db.query(models.Template)
            .filter(models.Template.Temp_name == details.name)
            .filter(models.Template.temp_id != temp_id)
            .first()
        )
        if existing_name:
            raise HTTPException(
                status_code=400,
                detail=f"Template name '{details.name}' already exists."
            )

        #  Apply updates
        db_template.Temp_name = details.name.strip() 
        db_template.Temp_desc = details.desc.strip() 

        #  Commit and refresh
        db.commit()
        db.refresh(db_template)

        #  Response
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"Template ID {temp_id} updated successfully",
                "data": {
                    "temp_id": db_template.temp_id,
                    "Temp_name": db_template.Temp_name,
                    "Temp_desc": db_template.Temp_desc,
                    "created_by": db_template.created_by
                }
            }
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
