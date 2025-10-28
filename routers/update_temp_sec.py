from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from core import database
from routers import template_check, section_check
from routers.template_check import (update_template)
from routers.section_check import (update_section)
from core import models,schemas
from core.schemas import UnifiedUpdateRequest

router = APIRouter()
get_db = database.get_db


@router.put("/update_data", tags=["Update Data"])
def update_data(payload: schemas.UnifiedUpdateRequest, db: Session = Depends(get_db)):
    try:
        # Case 1: Template update
        if payload.temp_id:
            template_data = schemas.TemplateUpdate(
                Temp_name=payload.Temp_name,
                Temp_desc=payload.Temp_desc,
                created_by=payload.created_by
            )
            result= template_check.update_template(
                temp_id=payload.temp_id,
                template=template_data,
                db=db
            )
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message":"Template updated successfully",
                    "data": result
                }
            )

        # Case 2: Section update
        elif payload.section_id:
            section_data = schemas.SectionUpdate(
                section_name=payload.section_name,
                section_desc=payload.section_desc,
                template_id=payload.template_id,
                order=payload.order
            )
            result= section_check.update_section(
                section_id=payload.section_id,
                section=section_data,
                db=db
            )
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message":"section updated successfully",
                    "data":result
                }
            )

        # Case 3: No ID provided
        else:
            raise HTTPException(status_code=400, detail="Must include either temp_id or section_id")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



"""
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from core import database, models, schemas
from typing import Union

router = APIRouter()
get_db = database.get_db


@router.put("/update_data", response_model=Union[schemas.TemplateRead, schemas.SectionRead])
def update_data(payload: dict, db: Session = Depends(get_db)):
    
    try:
        # ================================
        # Case 1: Update Template
        # ================================
        if "temp_id" in payload:
            db_template = db.query(models.Template).filter(models.Template.temp_id == payload["temp_id"]).first()
            if not db_template:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

            if "Temp_name" in payload:
                db_template.Temp_name = payload["Temp_name"]
            if "Temp_desc" in payload:
                db_template.Temp_desc = payload["Temp_desc"]
            if "created_by" in payload:
                db_template.created_by = payload["created_by"]

            db.commit()
            db.refresh(db_template)

            response_template = {
                "temp_id":db_template.temp_id,
                "Temp_name":db_template.Temp_name,
                "Temp_desc":db_template.Temp_desc,
                "created_by":db_template.created_by
                } 

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": f"Template '{db_template.Temp_name}' updated successfully",
                    "data": response_template
                }
            )

        # ================================
        # Case 2: Update Section
        # ================================
        elif "section_id" in payload:
            db_section = db.query(models.Section).filter(models.Section.section_id == payload["section_id"]).first()
            if not db_section:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

            # Check order duplication (only if changed)
            if "template_id" in payload and "order" in payload:
                existing_order = db.query(models.Section).filter(
                    models.Section.template_id == payload["template_id"],
                    models.Section.order == payload["order"],
                    models.Section.section_id != payload["section_id"]
                ).first()
                if existing_order:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Order number {payload['order']} already exists for template ID {payload['template_id']}."
                    )

            # Check section name duplication
            if "section_name" in payload:
                existing_section_name = db.query(models.Section).filter(
                    models.Section.section_name == payload["section_name"],
                    models.Section.section_id != payload["section_id"]
                ).first()
                if existing_section_name:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section name already exists")

            # Perform updates
            if "section_name" in payload:
                db_section.section_name = payload["section_name"]
            if "section_desc" in payload:
                db_section.section_desc = payload["section_desc"]
            if "template_id" in payload:
                db_section.template_id = payload["template_id"]
            if "order" in payload:
                db_section.order = payload["order"]

            db.commit()
            db.refresh(db_section)

            response_section = {
                "section_id":db_section.section_id,
                "section_name":db_section.section_name,
                "section_desc":db_section.section_desc,
                "template_id":db_section.template_id,
                "order":db_section.order
            }

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": f"Section '{db_section.section_name}' updated successfully",
                    "data": response_section
                }
            )

        # ================================
        # Case 3: Missing Identifiers
        # ================================
        else:
            raise HTTPException(status_code=400, detail="Must include either 'temp_id' or 'section_id' in payload")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
"""