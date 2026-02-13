from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
import models, schemas, utils, oauth2
from typing import List
from datetime import datetime, timedelta

router = APIRouter(prefix= '/doctors',tags=['Doctors'])

@router.post("/me", response_model= schemas.DoctorOwnerOutput)
def update_info(doctor : schemas.UpdateDoctor, db: Session = Depends(get_db), user: dict = Depends(oauth2.get_current_user)):
    print(user.role)
    if user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not authorized to update doctor information")
    try:
        doctor_info = models.Doctor(name = user.user_name, user_id = user.user_id, **doctor.model_dump())
        db.add(doctor_info)
        db.commit() 
    except IntegrityError as i:
        raise HTTPException(status_code=409, detail= "Doctor profile already exists")
    db.refresh(doctor_info)
    return doctor_info

@router.get("/me", response_model= schemas.DoctorOwnerOutput)
def get_user(db: Session = Depends(get_db),current_user: dict = Depends(oauth2.get_current_user)):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not authorized to get doctor information")
    current_doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.user_id).first()
    if not current_doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    if not current_doctor.is_active:
        raise HTTPException(status_code=403, detail="Doctor profile is inactive")
    else:
        return current_doctor
    

@router.patch("/me", response_model=schemas.DoctorOwnerOutput)
def update_doctor_status(payload: schemas.UpdateProfileStatus,db: Session = Depends(get_db),current_user=Depends(oauth2.get_current_user)):
    current_doctor = (db.query(models.Doctor).filter(models.Doctor.user_id == current_user.user_id).one_or_none())
    if not current_doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    if payload.is_active:
        if current_doctor.is_active:
            raise HTTPException(status_code=409, detail="Profile already active")
        current_doctor.is_active = True
    else:
        now = datetime.now()
        active_appointment = (db.query(models.Appointment).join(models.Slot, models.Appointment.slot_id == models.Slot.slot_id).filter(models.Slot.doctor_id == current_doctor.doctor_id).filter(models.Appointment.status == "booked").filter((models.Slot.date > now.date()) |((models.Slot.date == now.date()) & (models.Slot.start_time > now.time()))).first())
        if active_appointment:
            raise HTTPException(status_code=409,detail="Cannot deactivate doctor with upcoming appointments",)
        if not current_doctor.is_active:
            raise HTTPException(status_code=409, detail="Profile already inactive")
        current_doctor.is_active = False
    db.commit()
    db.refresh(current_doctor)
    return current_doctor

@router.get("/", response_model= List[schemas.DoctorOutput])
def get_doctor(db: Session = Depends(get_db),current_user: dict = Depends(oauth2.get_current_user)):
    doctor = db.query(models.Doctor).filter(models.Doctor.is_active == True).all()
    if not doctor:
        raise HTTPException(status_code=404, detail="No doctors found")
    else:
        return doctor
    
@router.get("/{id}", response_model= schemas.DoctorOutput)
def get_doctor(id : int,  db: Session = Depends(get_db),current_user: dict = Depends(oauth2.get_current_user)):
    doctor = db.query(models.Doctor).filter(models.Doctor.doctor_id == id).filter(models.Doctor.is_active == True).one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="No doctors found")
    else:
        return doctor

@router.post("/me/slots", response_model=List[schemas.SlotsOutput])
def update_slot(slot: schemas.SlotsInput, db: Session = Depends(get_db), current_user : dict = Depends(oauth2.get_current_user)):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not authorized to update slot")
    start_dt = datetime.combine(slot.date, slot.start_time)
    if start_dt < datetime.now():
         raise HTTPException(status_code=422, detail="Availability time must be in the future")
    try:
        if slot.start_time >= slot.end_time:
            raise HTTPException(status_code=422, detail="end_time must be after start_time")
        doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.user_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor profile not found")
        if not doctor.is_active:
             raise HTTPException(status_code=403, detail="Not authorized to update slot")
        start_dt = datetime.combine(slot.date, slot.start_time)
        end_dt = datetime.combine(slot.date, slot.end_time)
        current = start_dt
        duration = timedelta(minutes=slot.slot_duration)

        while current + duration <= end_dt:
            new_slot = models.Slot(
                doctor_id=doctor.doctor_id,
                status="available",
                date=slot.date,
                slot_duration = slot.slot_duration,
                start_time=current.time(),
                end_time=(current + duration).time()
            )
            db.add(new_slot)
            current += duration
        db.commit()
        results = db.query(models.Slot, models.User.user_name).join(models.Doctor, models.Slot.doctor_id == models.Doctor.doctor_id,).join(models.User, models.User.user_id == models.Doctor.user_id).filter(models.Slot.doctor_id == doctor.doctor_id).all()
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
    except IntegrityError as i:
          raise HTTPException(status_code=409, detail="Slot already exists")
    
@router.get("/me/slots", response_model= List[schemas.SlotsDocOutput])
def get_all_slots(status: schemas.SlotsFilter | None = Query(None), past: bool = Query(True), db : Session = Depends(get_db), current_user : dict = Depends(oauth2.get_current_user)):

    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not authorized")
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.user_id).first()
    if not doctor:
         raise HTTPException(status_code=404, detail="Doctor not found")
    if not doctor.is_active:
         raise HTTPException(status_code=403, detail="Doctor profile is inactive")
    query = db.query(models.Slot).filter(models.Slot.doctor_id == doctor.doctor_id)
    now = datetime.now()
    if past:
        if status == schemas.SlotsFilter.booked:
            slots = query.filter(models.Slot.status == "booked").all()
        elif status == schemas.SlotsFilter.available:
            slots = query.filter(models.Slot.status == "available").all()
        else:
            slots = query.all()
    else:
        if status == schemas.SlotsFilter.booked:
            slots = query.filter(models.Slot.status == "booked").filter(models.Slot.date > now.date(), models.Slot.time > now.time()).all()
        elif status == schemas.SlotsFilter.available:
            slots = query.filter(models.Slot.status == "available").filter(models.Slot.date > now.date(), models.Slot.time > now.time()).all()
        else:
            slots = query.filter(models.Slot.date > now.date(), models.Slot.time > now.time()).all()
    return slots

@router.delete("/me/slots/{id}")
def delete_slot(id:int = id, db : Session = Depends(get_db), current_user : dict = Depends(oauth2.get_current_user)):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not authorized to delete slot")
    slot = db.query(models.Slot).filter(models.Slot.slot_id == id).first()
    db.delete(slot)
    db.commit()
    return {"Message": "Deleted successfully"}

@router.get("/me/patients", response_model= List[schemas.PatientOutputDoc])
def get_my_patients(db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not authorized to check the patients info")
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.user_id).first()
    if not doctor:
         raise HTTPException(status_code=404, detail="Doctor not found")
    if not doctor.is_active:
         raise HTTPException(status_code=403, detail="Doctor profile is not active")
    patients = db.query(models.Patient, models.User.user_name).join(models.Appointment, models.Appointment.patient_id == models.Patient.patient_id).join(models.Slot, models.Slot.slot_id == models.Appointment.slot_id).join(models.User, models.User.user_id == models.Patient.user_id).filter(models.Slot.doctor_id == doctor.doctor_id).all()
    response = []
    for patient, patient_name in patients:
        response.append(
            {
                "patient_id": patient.patient_id,
                "patient_name": patient_name,
                "age" : patient.age
            }
        )
    return response
    
@router.get("/me/appointments", response_model=List[schemas.AppointmentOutputDoc])
def get_my_appointments(db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.user_id).first()
    results = db.query(models.Appointment, models.Slot.start_time, models.Slot.end_time, models.Slot.date, models.User.name).join(models.Slot, models.Appointment.slot_id == models.Slot.slot_id).join(models.Patient, models.Appointment.patient_id == models.Patient.patient_id).join(models.User, models.User.user_id == models.Patient.user_id).filter(models.Slot.doctor_id == doctor.doctor_id).all()
    response = []
    for appt, start_time, end_time, date, patient_name in results:
        response.append({
            "appointment_id": appt.appointment_id,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "patient_name": patient_name,
            "status": appt.status
        })
    return response



