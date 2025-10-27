from core import schemas, models, database
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session



router = APIRouter()
get_db = database.get_db


#---create details to template check
@router.post("/fill", response_model=schemas.TemplateRead)
def create_template(template: schemas.TemplateCreate, db: Session = Depends(database.get_db)):
    try:
        db_template = db.query(models.Template).filter(models.Template.Temp_name == template.Temp_name).first()
        if db_template:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Template already exists")

        new_template = models.Template(
            Temp_name=template.Temp_name,
            Temp_desc=template.Temp_desc,
            created_by=template.created_by
        )
        db.add(new_template)
        db.commit()
        db.refresh(new_template)
        
        response_template = schemas.TemplateData(
            temp_id=new_template.temp_id,
            Temp_name=new_template.Temp_name,
            Temp_desc=new_template.Temp_desc,
            created_by=new_template.created_by
        )
        return {
            "status": "success",
            "message": "Template created successfully",
            "data": response_template
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))