from core import schemas, models, database
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()
get_db = database.get_db

#---create details to section check
@router.post("/fill_the_section", response_model=schemas.SectionRead)
def create_section(section: schemas.SectionCreate, db: Session = Depends(database.get_db)):
    try:
        # db_section = db.query(models.Section).filter(models.Section.section_name == section.section_name).first()
        # if db_section:
        #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section already exists")

        new_section = models.Section(
            section_name=section.section_name,
            section_desc=section.section_desc,
            template_id=section.template_id
        )
        db.add(new_section)
        db.commit()
        db.refresh(new_section)
        response_section=schemas.SectionData(
            section_id=new_section.section_id,
            section_name=new_section.section_name,
            section_desc=new_section.section_desc,
            template_id=new_section.template_id
        )
        return {
            "status": "success",
            "message": "Section created successfully",
            "data": response_section
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
