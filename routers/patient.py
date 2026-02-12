from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
import models, schemas, utils, oauth2
from typing import List
from datetime import datetime
router = APIRouter(prefix= '/patients', tags=['Patients'])

@router.post("/me", response_model= schemas.PatientOwnerOutput)
def create_profile(patient : schemas.UpdatePatient, db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Not authorized to update patient information")
    try:
        patient_info = models.Patient(user_id = current_user.user_id, patient_name = current_user.user_name, **patient.model_dump())
        db.add(patient_info)
        db.commit() 
    except IntegrityError as i:
        raise HTTPException(status_code=409, detail= "Patient already exists")
    db.refresh(patient_info)
    return patient_info



@router.get("/doctors/me", response_model= List[schemas.DoctorOutput])
def get_my_doctors(db: Session = Depends(get_db),current_user: dict = Depends(oauth2.get_current_user)):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Not authorized to get patient information")
    current_patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.user_id).first()
    if not current_patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    if not current_patient.is_active:
        raise HTTPException(status_code=403, detail="Your account is deactivated")
    doctor = db.query(models.Doctor).join(models.Appointment, models.Appointment.patient_id == current_patient.patient_id).join(models.Slot, models.Appointment.slot_id == models.Slot.slot_id).filter(models.Slot.doctor_id == models.Doctor.doctor_id).all()
    
    return doctor


@router.get("/me", response_model= schemas.PatientOwnerOutput)
def get_patient(db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Not authorized to get patient information")
    current_patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.user_id).first()
    if not current_patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    if not current_patient.is_active:
        raise HTTPException(status_code=403, detail="Your account is deactivated")
    return current_patient
    
@router.patch("/me", response_model=schemas.PatientOwnerOutput)
def update_patient_status(payload: schemas.UpdateProfileStatus,db: Session = Depends(get_db),current_user=Depends(oauth2.get_current_user)):
    current_patient = (db.query(models.Patient).filter(models.Patient.user_id == current_user.user_id).one_or_none())
    if not current_patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    if payload.is_active:
        if current_patient.is_active:
            raise HTTPException(status_code=409, detail="Profile already active")
        current_patient.is_active = True
    else:
        if not current_patient.is_active:
            raise HTTPException(status_code=409, detail="Profile already inactive")        
        now = datetime.now()
        active_appointment = db.query(models.Appointment).filter(models.Appointment.patient_id == current_patient.patient_id).filter(models.Appointment.status == "booked").filter((models.Slot.date > now.date()) |((models.Slot.date == now.date()) & (models.Slot.start_time > now.time()))).first()
        if active_appointment:
            raise HTTPException(status_code=409,detail="Cannot deactivate patient with upcoming appointments")
        current_patient.is_active = False
    db.commit()
    db.refresh(current_patient)
    return current_patient
