from core import schemas, models, database
from core.role_based import (admin_required, user_required)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from core.auth import get_current_user

router = APIRouter()
get_db = database.get_db

#---create details to section check
@router.post("/fill_the_section", response_model=schemas.SectionRead, dependencies=[Depends(admin_required)])
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
@router.put("/update_section/{section_id}", response_model=schemas.SectionRead, dependencies=[Depends(admin_required)])
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


#-- rearranging order
@router.put("/reorder_sections", dependencies=[Depends(admin_required)])
def reorder_sections(
    reorder_data: list[schemas.SectionReorderItem],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        if not reorder_data:
            raise HTTPException(status_code=400, detail="No data provided")

        #  Step 1: Basic duplicate ID check
        section_ids = [item.section_id for item in reorder_data]
        if len(section_ids) != len(set(section_ids)):
            raise HTTPException(status_code=400, detail="Duplicate section_id in input")

        #  Step 2: Fetch all target sections
        sections = db.query(models.Section).filter(models.Section.section_id.in_(section_ids)).all()
        if len(sections) != len(reorder_data):
            existing_ids = [s.section_id for s in sections]
            missing = list(set(section_ids) - set(existing_ids))
            raise HTTPException(status_code=404, detail=f"Sections not found: {missing}")

        #  Step 3: Build mapping {section_id: new_order}
        new_order_map = {item.section_id: item.new_order for item in reorder_data}

        #  Step 4: Group validation - check duplicates within same template
        grouped = {}
        for s in sections:
            grouped.setdefault(s.template_id, []).append(new_order_map[s.section_id])

        for template_id, new_orders in grouped.items():
            # (a) Check duplicate new orders within template
            if len(new_orders) != len(set(new_orders)):
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate new order values found within template_id {template_id}"
                )

            # (b) Check if provided orders are valid ones from existing order list
            existing_orders = [
                s.order for s in sections if s.template_id == template_id
            ]

            invalid_orders = [o for o in new_orders if o not in existing_orders]
            if invalid_orders:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid new order(s) {invalid_orders} for template_id {template_id}. "
                           f"Allowed orders: {sorted(existing_orders)} Enter the order numbers that are already exists against the template id"
                )

        #  Step 5: Temporarily clear orders to bypass unique constraint
        for s in sections:
            s.order = None
        db.flush()

        #  Step 6: Apply final new orders
        for s in sections:
            s.order = new_order_map[s.section_id]
        db.commit()

        #  Step 7: Return success
        return {
            "status": "success",
            "message": "Sections reordered successfully",
            "data": [
                {"section_id": s.section_id, "template_id": s.template_id, "order": s.order}
                for s in sections
            ]
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
