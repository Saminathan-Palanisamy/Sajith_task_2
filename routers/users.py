import logging
from core import models, schemas, database
from core.auth import (hash_password, verify_password, create_access_token, decode_access_token)
from core.schemas import (UserCreate, UserLogin, UserRead, LoginResponse, UserOut, Token_Data)
from fastapi import APIRouter, Depends, HTTPException, status
from core import dependencies
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.responses import JSONResponse

router = APIRouter()
get_db = database.get_db

ACCESS_TOKEN_EXPIRE_MINUTES = 50

# Create User
@router.post("/register", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    try:
        if db.query(models.User).filter(models.User.email == user.email).first():
            raise HTTPException(status_code=400, detail="email already registered")
        if len(user.password.encode('utf-8')) > 72:
            logging.warning("Password longer than 72 bytes; truncating for bcrypt")


        hashed_password = hash_password(user.password)
        new_user = models.User(username=user.username, password=hashed_password, role=models.UserRole(user.role.value), email=user.email, contact_number=user.contact_number)
        db.add(new_user)
        db.commit()
        logging.info("User committed successfully")
        db.refresh(new_user)
        logging.info("User refreshed successfully")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "role": new_user.role.value
               }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

#----login user
@router.post("/login", response_model=schemas.LoginResponse)
def login_user(user: schemas.UserLogin, db: Session = Depends(database.get_db)):
    try:
        db_user = db.query(models.User).filter(models.User.email == user.email).first()
        if not db_user:
            raise HTTPException(status_code=400, detail="Invalid email")
        if not verify_password(user.password, db_user.password):
            raise HTTPException(status_code=400, detail="Invalid password")

        access_token_expies = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.email, "role": db_user.role.value}, expires_delta=access_token_expies
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "username": db_user.username,
                "access_token": access_token,
                "status": "success",
                "message": "Successful ah login panitinga, vaalthukal!"
            }
                
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#----logout user
@router.post("/logout", response_model=schemas.Token_Data)
def logout_user(current_user: dict = Depends(dependencies.get_current_user)):
    try:
        # Invalidate the user's token (implementation depends on your auth strategy)
        return {
            "access_token": "",
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# #----get user by id
# @router.get("/{user_id}/", response_model=schemas.UserRead, status_code=200)
# def get_user(user_id: int, db: Session = Depends(database.get_db)):
#     try:
#         db_user = db.query(models.User).filter(models.User.id == user_id).first()
#         if not db_user:
#             raise HTTPException(status_code=404, detail="User not found")
#         return {
#                 "id": db_user.id,
#                 "username": db_user.username,
#                 "email": db_user.email,
#                 "role": db_user.role.value,
#                 "contact_number": db_user.contact_number
#                }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/me", response_model=schemas.UserRead, status_code=200)
# def get_current_user(current_user: dict = Depends(dependencies.get_current_user), db: Session = Depends(database.get_db)):
#     try:
#         db_user = db.query(models.User).filter(models.User.email == current_user["sub"]).first()
#         if not db_user:
#             raise HTTPException(status_code=404, detail="User not found")
#         return {
#                 "id": db_user.id,
#                 "username": db_user.username,
#                 "email": db_user.email,
#                 "role": db_user.role.value,
#                 "contact_number": db_user.contact_number
#                }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))