from sqlalchemy import func
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
        
        max_order=db.query(func.max(models.Section.order)).filter(models.Section.template_id==section.template_id).scalar()
        next_order = (max_order or 0) + 1

        existing_section_name=db.query(models.Section).filter(models.Section.section_name==section.section_name).first()
        if existing_section_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section name already exists")
        new_section = models.Section(
            section_name=section.section_name,
            section_desc=section.section_desc,
            template_id=section.template_id,
            order=next_order
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

@router.put("/update_section_details", dependencies=[Depends(admin_required)])
def update_section_details(
    section_id: int,
    details: schemas.UpdateDetails,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update section name and description by section_id.
    - Keeps the same order and template_id.
    - Validates unique section name under same template.
    """
    try:
        #  Validate section_id
        section = db.query(models.Section).filter(models.Section.section_id == section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")

        #  Validate details input
        if not details or (not details.name and not details.desc):
            raise HTTPException(
                status_code=400,
                detail="At least one field (name or desc) is required to update."
            )

        name = details.name.strip() if details.name else None
        desc = details.desc.strip() if details.desc else None

        #  If name provided, check for duplicates under same template
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

        #  Update description (if provided)
        if desc:
            section.section_desc = desc

        #  Keep order and template_id unchanged
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


#-- delete section with reordering according to the last section order. Once deleted, the order against the template id will be rearranged.
@router.delete("/delete_section/{section_id}", dependencies=[Depends(admin_required)])
def delete_section(section_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    try:
        #  Step 1: Find section to delete
        section_to_delete = db.query(models.Section).filter(models.Section.section_id == section_id).first()
        if not section_to_delete:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

        template_id = section_to_delete.template_id
        deleted_order = section_to_delete.order

        #  Step 2: Delete the section
        db.delete(section_to_delete)
        db.commit()

        #  Step 3: Shift remaining sections' order numbers down by 1
        remaining_sections = (
            db.query(models.Section)
            .filter(models.Section.template_id == template_id)
            .filter(models.Section.order > deleted_order)
            .order_by(models.Section.order.asc())
            .all()
        )

        for section in remaining_sections:
            section.order -= 1
        db.commit()

        # Step 4: Return success response
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"Section ID {section_id} deleted successfully and order adjusted.",
            },
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
