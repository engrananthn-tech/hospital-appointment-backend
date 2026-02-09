from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
import models, schemas, utils, oauth2
from datetime import timedelta, datetime, timezone
from typing import List

router = APIRouter(prefix= '/slots')




@router.get("/", response_model= List[schemas.SlotsOutput])
def get_all_slots(db : Session = Depends(get_db), current_user : dict = Depends(oauth2.get_current_user)):

    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Not authorized to check the available slots")
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.user_id).first()
    if not patient:
         raise HTTPException(status_code=404, detail="Patient not found")
    if not patient.is_active:
         raise HTTPException(status_code=403, detail="Patient profile is inactive")
    now = datetime.now()
    today = now.date()
    current_time = now.time()
    results = (db.query(models.Slot, models.User.user_name).outerjoin(models.Appointment,models.Slot.slot_id == models.Appointment.slot_id).join(models.Doctor,models.Slot.doctor_id == models.Doctor.doctor_id).join(models.User,models.User.user_id == models.Doctor.user_id).filter(or_(models.Appointment.appointment_id.is_(None),models.Appointment.status == 'cancelled')).filter(or_(models.Slot.date > today,and_(models.Slot.date == today,models.Slot.start_time > current_time))).all())
    response = []
    for slot_obj, doctor_name in results:
            response.append({
                "slot_id": slot_obj.slot_id,
                "date": slot_obj.date,
                "doctor_id": slot_obj.doctor_id,
                "slot_duration": slot_obj.slot_duration,
                "start_time": slot_obj.start_time,
                "end_time": slot_obj.end_time,
                "status": slot_obj.status,
                "doctor_name": doctor_name
            })
    return response

