from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, NoResultFound
from database import get_db
import models, schemas, utils, oauth2
from datetime import datetime, timedelta
from typing import List

router = APIRouter(prefix= "/appointments")

@router.post("/", response_model= schemas.AppointmentOutput)
def post_appointment(slot: schemas.AppointmentInput, db: Session = Depends(get_db), current_user : dict = Depends(oauth2.get_current_user)):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Not authorized to update appointments")
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.user_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Could'nt find patient")
    if not patient.is_active:
        raise HTTPException(status_code=403, detail="Not authorized to update appointments")
    try:
        selected_slot = db.query(models.Slot).filter(models.Slot.slot_id == slot.slot_id).with_for_update().one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Slot not found") 
    now = datetime.now()
    cutoff = now-timedelta(minutes = 30)

    if (selected_slot.date < now.date()) or ((selected_slot.date == now.date()) and (selected_slot.start_time < (cutoff.time()))):
        raise HTTPException(status_code=409, detail="Booking window closed")
    
    patient_id = patient.patient_id

    if selected_slot.status == "booked":
        raise HTTPException(status_code=409, detail="Slot not available")      

    new = models.Appointment(patient_id = patient_id, slot_id = slot.slot_id, status = "booked")
    selected_slot.status="booked"
    db.add(new)
    db.flush()
    db.refresh(new)
    return new

@router.get("/me", response_model= List[schemas.AppointmentOutputPat])
def get_my_appointments(status: schemas.AppointmentFilter | None = Query(None), db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    ##current_patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.user_id).first()
    if current_user.role == "patient":
        query = db.query(models.Appointment, models.Slot.date, models.Slot.start_time, models.Slot.end_time, models.User.user_name).join(models.Slot, models.Appointment.slot_id == models.Slot.slot_id).join(models.Patient, models.Appointment.patient_id == models.Patient.patient_id).filter(models.Patient.user_id == current_user.user_id).order_by(models.Slot.date, models.Slot.start_time)
        if status == schemas.AppointmentFilter.completed:
            appointments = query.filter(models.Appointment.status == "completed").all()
        elif status == schemas.AppointmentFilter.cancelled:
            appointments = query.filter(models.Appointment.status == "cancelled").all()
        elif status == schemas.AppointmentFilter.upcoming:
            appointments = query.filter(models.Appointment.status == "booked").all()
        else:
            appointments = query.all()
        response = []
        for appt, date, start_time, end_time, doctor_name in appointments:
            response.append({
                "appointment_id": appt.appointment_id,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "doctor_name": doctor_name,
                "status": appt.status
            })
    else:
        doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.user_id).first()
        query = db.query(models.Appointment, models.Slot.start_time, models.Slot.end_time, models.Slot.date, models.User.user_name).join(models.Slot, models.Appointment.slot_id == models.Slot.slot_id).join(models.Patient, models.Appointment.patient_id == models.Patient.patient_id).join(models.User, models.User.user_id == models.Patient.user_id).filter(models.Slot.doctor_id == doctor.doctor_id).order_by(models.Slot.date, models.Slot.start_time)
        if status == schemas.AppointmentFilter.completed:
            appointments = query.filter(models.Appointment.status == "completed").all()
        elif status == schemas.AppointmentFilter.cancelled:
            appointments = query.filter(models.Appointment.status == "cancelled").all()
        elif status == schemas.AppointmentFilter.upcoming:
            appointments = query.filter(models.Appointment.status == "booked").all()
        else:
            appointments = query.all()
        response = []
        for appt, start_time, end_time, date, patient_name in appointments:
            response.append({
                "appointment_id": appt.appointment_id,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "patient_name": patient_name,
                "status": appt.status
            })
    return response

@router.patch("/{id}/cancel", response_model= schemas.AppointmentOutput)
def cancel_appointment(db: Session = Depends(get_db), current_user : dict = Depends(oauth2.get_current_user)):
    if current_user.role == "patient":
        patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.user_id).first()
        if not patient.is_active:
            raise HTTPException(status_code=403, detail="Patient profile is inactive")
        query = db.query(models.Appointment).filter(models.Appointment.patient_id == patient.patient_id).filter(models.Appointment.appointment_id == id).with_for_update()
    else:
        doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.user_id).first()
        if not doctor.is_active:
            raise HTTPException(status_code=403, detail="Doctor profile is inactive")
        query = db.query(models.Appointment).join(models.Slot, models.Slot.slot_id == models.Appointment.slot_id).filter(models.Slot.doctor_id == doctor.doctor_id).filter(models.Appointment.appointment_id == id).with_for_update()
    appointment = query.first()
    now = datetime.now()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment does'nt exist")
    slot = db.query(models.Slot).filter(models.Slot.slot_id == appointment.slot_id).first()
    if appointment.status == "cancelled":
        raise HTTPException(status_code=409, detail="Appointment already cancelled")
    if appointment.status == "completed":
        raise HTTPException(status_code=409, detail="Invalid appointment state transition")
    with db.begin():
        if current_user.role == "patient":
            cutoff = (datetime.combine(slot.date, slot.start_time) - timedelta(minutes=30))
            if now > cutoff:
                raise HTTPException(status_code=403, detail="Cancellation window has passed")
            appointment.status = "cancelled"
            new_audit = models.Appointment_audit(appointment_id = appointment.appointment_id, old_status = "booked", new_status = "cancelled", changed_by = "patient")
            
            slot.status = "available"
        else:
            appointment.status = "cancelled"
            new_audit = models.Appointment_audit(appointment_id = appointment.appointment_id, old_status = "booked", new_status = "cancelled", changed_by = "patient")
            now = datetime.now()
            if (now.date() < slot.date) or (now.date() == slot.date and now.time() < slot.time()):
                slot.status = "available" 
        db.add(new_audit)
    return query.first()

@router.patch("/{id}/complete", response_model= schemas.AppointmentOutput)
def complete_appointment(db: Session = Depends(get_db), current_user : dict = Depends(oauth2.get_current_user)):
    if current_user.role == "patient":
        raise HTTPException(status_code=403, detail="Not authorized to complete appointments")
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.user_id).first()
    if not doctor.is_active:
        raise HTTPException(status_code=403, detail="Doctor profile is inactive")
    query = db.query(models.Appointment).join(models.Slot, models.Slot.slot_id == models.Appointment.slot_id).filter(models.Slot.doctor_id == doctor.doctor_id).filter(models.Appointment.appointment_id == id).with_for_update()
    appointment = query.first()
    now = datetime.now()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment does'nt exist")
    slot = db.query(models.Slot).filter(models.Slot.slot_id == appointment.slot_id).first()
    start_dt = datetime.combine(slot.date, slot.start_time)
    if now < start_dt:
        raise HTTPException(status_code=403,detail="Cannot complete appointment before it starts")
    if appointment.status == "completed":
        raise HTTPException(status_code=409, detail="Appointment already completed")
    if appointment.status == "cancelled":
        raise HTTPException(status_code=409, detail="Cannot complete cancelled appointments")
    with db.begin():
        appointment.status = "completed"
        new_audit = models.Appointment_audit(appointment_id = appointment.appointment_id, old_status = "booked", new_status = "completed", changed_by = "doctor")
        db.add(new_audit)
    return query.first()

