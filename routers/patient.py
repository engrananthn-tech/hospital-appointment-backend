from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
import models, schemas, utils, oauth2
from typing import List

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

@router.patch("/me", response_model= schemas.PatientOwnerOutput)
def activate(db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    query = db.query(models.Patient).filter(models.Patient.user_id == current_user.user_id)
    current_patient = query.first()
    if not current_patient:
        raise HTTPException(status_code=404, detail="Patient does'nt exist")
    if current_patient.is_active:
        raise HTTPException(status_code=409, detail="Profile is already active")
    current_patient.is_active = True
    db.commit()
    return query.first()



@router.get("/doctors/me", response_model= List[schemas.DoctorOutput])
def get_user(db: Session = Depends(get_db),current_user: dict = Depends(oauth2.get_current_user)):
    current_patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.user_id).first()
    doctor = db.query(models.Doctor).join(models.Appointment, models.Appointment.patient_id == current_patient.patient_id).join(models.Slot, models.Appointment.slot_id == models.Slot.slot_id).filter(models.Slot.doctor_id == models.Doctor.doctor_id).all()
    if not current_patient:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    if not current_patient.is_active:
        raise HTTPException(status_code=403, detail="Not authorized to get doctor information")
    else:
        return doctor


@router.get("/me", response_model= schemas.PatientOwnerOutput)
def get_patient(db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    current_patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.user_id).first()
    if not current_patient.is_active:
        raise HTTPException(status_code=403, detail="Your account is deactivated")
    return current_patient
    
@router.patch("/me")
def deactivate(db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    current_patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.user_id).first()
    appointment = db.query(models.Appointment).filter(models.Appointment.patient_id == current_patient.patient_id).first()
    if appointment:
        raise HTTPException(status_code=409, detail="Cannot deactivate doctor with active appointments")
    current_patient.is_active = False
    db.commit()
    return {"Message" : "Deactivated"}
