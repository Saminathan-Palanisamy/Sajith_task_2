from core import schemas, models, database
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse



router = APIRouter()
get_db = database.get_db


#---create details to template check
@router.post("/fill", response_model=schemas.TemplateRead)
def create_template(template: schemas.TemplateCreate, db: Session = Depends(database.get_db)):
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

# update template details
@router.put("/update/{temp_id}", response_model=schemas.TemplateRead)
def update_template(temp_id: int, template: schemas.TemplateUpdate, db: Session = Depends(database.get_db)):
    try:
        db_template = db.query(models.Template).filter(models.Template.temp_id == temp_id).first()
        if not db_template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

        db_template.Temp_name = template.Temp_name
        db_template.Temp_desc = template.Temp_desc
        db_template.created_by = template.created_by

        db.commit()
        db.refresh(db_template)

        response_template = {
            "temp_id": db_template.temp_id,
            "Temp_name": db_template.Temp_name,
            "Temp_desc": db_template.Temp_desc,
            "created_by": db_template.created_by
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Template updated successfully",
                "data": response_template
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))