from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DataError
from database import get_db
import models, schemas, utils, oauth2

router = APIRouter(prefix= '/users')

@router.post("/", response_model= schemas.UserOutput)
def createuser(user: schemas.User, db:Session = Depends(get_db)):
    user.role = user.role.lower()
    user.password = utils.hash(user.password)
    try:
        new = models.User(**user.model_dump())
        db.add(new)
        db.commit()
        db.refresh(new)
    except DataError as d:
        raise HTTPException(status_code=422, detail="Role must be 'doctor' or 'patient'")
    except IntegrityError as i:
        raise HTTPException(status_code=409, detail="Email already exists")
    return new

@router.get("/me", response_model= schemas.UserOutput)
def get_me(db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(models.User.user_id == current_user.user_id).first()
    return user

@router.delete("/me")
def deactivate(db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(models.User.user_id == current_user.user_id).first()
    user.status = "inactive"
    db.commit()
    return {"Message" : "Deactivated"}
