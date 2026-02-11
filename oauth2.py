from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from database import get_db
import schemas, models
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
EXPIRATION_TIME_IN_MINUTES = settings.access_token_expire_minutes

def create_access_token(data: dict):
    encode_data = data.copy()
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=EXPIRATION_TIME_IN_MINUTES)
    encode_data.update({"exp" : expiration_time})
    token = jwt.encode(encode_data, key= SECRET_KEY, algorithm= ALGORITHM)
    return token

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id = payload.get("user_id")
        role = payload.get("role")
        if not id:
            raise credentials_exception
        token = schemas.TokenData(id=id, role=role)
    except JWTError:
        raise credentials_exception
    return token

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail=f"Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    token = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.user_id == token.id).first()
    if not user:
        raise credentials_exception
    return user