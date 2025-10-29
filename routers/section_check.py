from core import schemas, models, database
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from core.auth import get_current_user

router = APIRouter()
get_db = database.get_db

#---create details to section check
@router.post("/fill_the_section", response_model=schemas.SectionRead)
def create_section(section: schemas.SectionCreate, db: Session = Depends(database.get_db),current_user: models.User = Depends(get_current_user)):
    try:
        existing_order=db.query(models.Section).filter(models.Section.template_id==section.template_id, models.Section.order==section.order).first()
        if existing_order:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Order number {section.order} already exists for template ID {section.template_id}.")
        
        existing_section_name=db.query(models.Section).filter(models.Section.section_name==section.section_name).first()
        if existing_section_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section name already exists")
        new_section = models.Section(
            section_name=section.section_name,
            section_desc=section.section_desc,
            template_id=section.template_id,
            order=section.order
        )
        db.add(new_section)
        db.commit()
        db.refresh(new_section)    
        response_section = {
            "section_id": new_section.section_id,
            "section_name": new_section.section_name,
            "section_desc": new_section.section_desc,
            "template_id": new_section.template_id,
            "order": new_section.order
        }
        
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
            "status": "success",
            "message": "Section created successfully",
            "data": response_section
        }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#-------------------------------------------------------------------------------

# update section details
@router.put("/update_section/{section_id}", response_model=schemas.SectionRead)
def update_section(section_id: int, section: schemas.SectionUpdate, db: Session = Depends(database.get_db),current_user: models.User = Depends(get_current_user)):
    try:
        db_section = db.query(models.Section).filter(models.Section.section_id == section_id).first()
        if not db_section:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

        existing_order=db.query(models.Section).filter(models.Section.template_id==section.template_id, models.Section.order==section.order, models.Section.section_id!=section_id).first()
        if existing_order:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Order number {section.order} already exists for template ID {section.template_id}.")

        existing_section_name=db.query(models.Section).filter(models.Section.section_name==section.section_name, models.Section.section_id!=section_id).first()
        if existing_section_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section name already exists")

        db_section.section_name = section.section_name
        db_section.section_desc = section.section_desc
        db_section.template_id = section.template_id
        db_section.order = section.order

        db.commit()
        db.refresh(db_section)

        response_section = {
            "section_id": db_section.section_id,
            "section_name": db_section.section_name,
            "section_desc": db_section.section_desc,
            "template_id": db_section.template_id,
            "order": db_section.order
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Section updated successfully",
                "data": response_section
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

