from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DATE, TIME, Enum, Boolean, UniqueConstraint
from datetime import datetime
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from typing import Annotated

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key= True)
    user_name = Column(String, nullable= False)
    email = Column(String, nullable= False, unique= True)
    password = Column(String, nullable=False)
    role = Column(Enum("doctor", "patient", name="user_role", create_constraint=True),nullable=False)
    created_at = Column(TIMESTAMP(timezone = True), server_default= text('now()'))

class Doctor(Base):
    __tablename__ = 'doctors'
    doctor_id = Column(Integer, primary_key= True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), unique=True) 
    name = Column(String, nullable= False)
    specialization = Column(String, nullable= False)
    experience = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone = True), server_default= text('now()'))
    is_active = Column(Boolean,nullable=False, default=True)

class Patient(Base):
    __tablename__ = 'patients'
    patient_id = Column(Integer, primary_key= True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), unique=True) 
    patient_name = Column(String, nullable= False)
    age = Column(Integer, nullable= False)
    gender = Column(Enum('male', 'female', name = "patient_gender", create_constraint = True), nullable=False)
    created_at = Column(TIMESTAMP(timezone = True), server_default= text('now()'))
    is_active = Column(Boolean,nullable=False, default=True)
    weight = Column(Integer, nullable=True)





class Slot(Base):
    __tablename__ = 'slots'
    slot_id = Column(Integer, primary_key= True)
    doctor_id = Column(Integer, ForeignKey('doctors.doctor_id', ondelete= 'CASCADE'))
    slot_duration = Column(Integer, nullable=False)
    date = Column(DATE, nullable=False)
    start_time = Column(TIME, nullable=False)
    end_time = Column(TIME, nullable=False)
    status = Column(Enum("available", "booked", name="doctor_slots", create_constraint=True),nullable=False)
    __table_args__ = (UniqueConstraint("doctor_id","date","start_time","end_time",name="uq_doctor_slot"),)

class Appointment(Base):
    __tablename__ = "appointments"
    appointment_id = Column(Integer, primary_key= True)
    slot_id = Column(Integer, ForeignKey('slots.slot_id', ondelete= 'CASCADE'))
    patient_id = Column(Integer, ForeignKey('patients.patient_id', ondelete= 'CASCADE'))
    status = Column(Enum("booked", "completed", "cancelled", name="appointment_status", create_constraint=True),nullable=False) 
    created_at = Column(TIMESTAMP(timezone = True), server_default= text('now()'))

class Appointment_audit(Base):
    __tablename__ = "appointment_audit"
    audit_id = Column(Integer, primary_key= True)
    appointment_id = Column(Integer, ForeignKey("appointments.appointment_id", ondelete="CASCADE"))
    old_status = Column(Enum("booked", "completed", "cancelled", name="appointment_status", create_constraint=True),nullable=False)
    new_status = Column(Enum("booked", "completed", "cancelled", name="appointment_status", create_constraint=True),nullable=False)
    changed_by = Column(Enum("doctor", "patient", "system", name="audit_changed_by", create_constraint=True),nullable=False)
    timestamp = Column(TIMESTAMP(timezone = True), server_default= text('now()'))