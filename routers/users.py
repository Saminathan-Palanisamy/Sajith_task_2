import logging
from core import models, schemas, database
from core.auth import (hash_password, verify_password, create_access_token, decode_access_token, get_current_user)
from core.schemas import (UserCreate, UserLogin, UserRead, LoginResponse, UserOut, Token_Data)
from fastapi import APIRouter, Depends, HTTPException, status, Request
from core import auth
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta


router = APIRouter()
get_db = database.get_db

ACCESS_TOKEN_EXPIRE_MINUTES = 10

# Create User
@router.post("/register", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    try:
        if db.query(models.User).filter(models.User.email == user.email).first():
            raise HTTPException(status_code=400, detail="email already registered")
        if len(user.password.encode('utf-8')) > 72:
            logging.warning("Password longer than 72 bytes; truncating for bcrypt")


        hashed_password = hash_password(user.password)
        new_user = models.User(
            username=user.username, 
            password=hashed_password, 
            role=models.UserRole(user.role.value), 
            email=user.email, 
            contact_number=user.contact_number)
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
def login_user(form_data: schemas.UserLogin = Depends(), db: Session = Depends(database.get_db), request: Request = None):
    try:
        db_user = db.query(models.User).filter(models.User.email == form_data.email).first()
        if not db_user:
            raise HTTPException(status_code=400, detail="Invalid email")
        if not verify_password(form_data.password, db_user.password):
            raise HTTPException(status_code=400, detail="Invalid password")

        access_token_expies = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.email, "role": db_user.role.value}, expires_delta=access_token_expies
        )
        auth_entry= models.Authenticator(
            User_id=db_user.id,
            Token=access_token,
            is_active=True,
            Login_time=datetime.utcnow()
        )
        db.add(auth_entry)
        db.commit()
        db.refresh(auth_entry)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "email": db_user.email,
                "access_token": access_token,
                "token_type": "bearer",
                "status": "success",
                "message": f"Welcome {db_user.username}, login successful!"
            }
                
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#----logout user
@router.post("/logout")
def logout_user(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Cheking the logout is working or not, work achuna sandhosam"""

    try:
        user = current_user["user"]
        token = current_user["token"]
        # --- Step 1: Find active session for this user ---
        active_session = db.query(models.Authenticator).filter(
            models.Authenticator.User_id == user.id,
            models.Authenticator.Token == token,
            models.Authenticator.is_active == True
        ).first()

        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active session found for this user."
            )

        # --- Step 2: Calculate session duration  ---
        Logout_time=datetime.utcnow()
        Login_time=active_session.Login_time or Logout_time
        Session_duration=int((Logout_time - Login_time).total_seconds())

        # --- Step 3: Update record ---
        active_session.is_active = False
        active_session.Logout_time = Logout_time
        active_session.Session_duration = Session_duration

        db.commit()
        db.refresh(active_session)

        # --- Step 4: Return JSON response ---
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"Logout successful for user {user.username}, adutha aala erakunga",
                "session_duration_seconds": Session_duration,
                "Logout time": Logout_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )

    except HTTPException as http_err:
        # Explicit FastAPI exceptions (e.g., no active session)
        raise http_err

    except Exception as e:
        # Any other unhandled error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during logout or Logout failed: {str(e)}"
        )
    

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