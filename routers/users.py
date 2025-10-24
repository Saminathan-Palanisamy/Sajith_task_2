import logging
from core import models, schemas, database
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()
get_db = database.get_db


# Create User
@router.post("/register/", response_model=schemas.UserOut, status_code=200)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    try:
        if db.query(models.User).filter(models.User.username == user.username).first():
            raise HTTPException(status_code=400, detail="Username already registered")
        new_user = models.User(username=user.username, password=user.password, role=models.UserRole(user.role.value), email=user.email, contact_number=user.contact_number)
        db.add(new_user)
        db.commit()
        logging.info("User committed successfully")
        db.refresh(new_user)
        logging.info("User refreshed successfully")

        return {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "role": new_user.role.value
               }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

#----login user
@router.post("/login/", response_model=schemas.UserOut, status_code=200)
def login_user(user: schemas.UserLogin, db: Session = Depends(database.get_db)):
    try:
        db_user = db.query(models.User).filter(models.User.email == user.email,
                                              models.User.password == user.password).first()
        if not db_user:
            raise HTTPException(status_code=400, detail="Invalid email or password")
        return {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "role": db_user.role.value
               }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#----get user by id
@router.get("/{user_id}/", response_model=schemas.UserRead, status_code=200)
def get_user(user_id: int, db: Session = Depends(database.get_db)):
    try:
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "role": db_user.role.value,
                "contact_number": db_user.contact_number
               }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))