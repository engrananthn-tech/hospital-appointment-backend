from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import schemas, models, utils, oauth2
from database import get_db

router = APIRouter(prefix= "/auth")

@router.post("/login")
def user_login(credentials: OAuth2PasswordRequestForm = Depends(), db : Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not utils.verify(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = oauth2.create_access_token({"user_id":user.user_id, "role": user.role})
    return {"access_token": access_token}

@router.post("/logout")
def user_login(db : Session = Depends(get_db)):
    raise HTTPException(status_code=204)