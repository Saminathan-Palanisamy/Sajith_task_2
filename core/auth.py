# core/auth.py
from fastapi import HTTPException, status, Depends
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core import database, models
from fastapi.responses import JSONResponse


#--JWT Oauth2_scheme router
oauth2_scheme = HTTPBearer()
#---------------------------------------------------------------------

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a plain password"""
    truncated = password[:72]
    return pwd_context.hash(truncated)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    truncated = plain_password[:72]
    return pwd_context.verify(truncated, hashed_password)
#---------------------------------------------------------------------
# JWT Secret and Algorithm
SECRET_KEY = "BeingGood"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES =  30

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_current_user(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    try:
        payload = decode_access_token(token.credentials)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return {"user": user, "token": token.credentials}
    except HTTPException as e:
        if "expired" in e.detail.lower():
            # mark session as inactive if token expired
            db.query(models.Authenticator).filter(models.Authenticator.Token == token.credentials).update({
                models.Authenticator.is_active: False,
                models.Authenticator.Logout_time: datetime.utcnow()
            })
            db.commit()
            # return JSONResponse(
            #     status_code=status.HTTP_200_OK,
            #     content={
            #         "message":"Access token Time limit expired.",
            #         "Session_duration":ACCESS_TOKEN_EXPIRE_MINUTES
                    
            #     }
            # )
        raise e

#---------------------------------------------------------------------
