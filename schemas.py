from pydantic import BaseModel, EmailStr
from enum import Enum
from fastapi import File, UploadFile, Form
from typing import Optional, Literal
from datetime import date, time, datetime

class User(BaseModel):
    user_name : str
    email : EmailStr
    password :str
    role : str

class SlotsInput(BaseModel):
    date: date
    slot_duration: int
    start_time: time
    end_time: time

class SlotsOutput(BaseModel):
    slot_id : int
    doctor_id : int
    doctor_name: str
    date: date
    slot_duration: int
    start_time: time
    end_time: time

class SlotsDocOutput(BaseModel):
    slot_id : int
    date: date
    start_time: time
    end_time: time
    status: str

class UserOutput(BaseModel):
    user_id :int
    user_name: str
    email : EmailStr
    role : str
    created_at : datetime

class UpdateDoctor(BaseModel):
    specialization: str
    experience: int

class DoctorOutput(BaseModel):
    doctor_id: int
    name: str
    specialization: str
    experience: int
    created_at: datetime

class DoctorOwnerOutput(BaseModel):
    doctor_id: int
    name: str
    specialization: str
    experience: int
    created_at: datetime
    is_active: bool

class UpdatePatient(BaseModel):
    gender: Literal['male','female']
    age: int

class PatientOutput(BaseModel):
    patient_id: int
    patient_name: str
    age: int
    created_at: datetime

class PatientOutputDoc(BaseModel):
    patient_id: int
    patient_name: str
    age: int

class PatientOwnerOutput(BaseModel):
    patient_id: int
    patient_name: str
    age: int
    created_at: datetime
    is_active: bool

class TokenData(BaseModel):
    id: int
    role: str

class AppointmentInput(BaseModel):
    slot_id: int

class AppointmentUpdate(BaseModel):
    action: Literal["cancel", "completed"]

class AppointmentOutput(BaseModel):
    appointment_id :int
    slot_id :int
    patient_id: int
    status : str
    created_at :datetime

class AppointmentOutputDoc(BaseModel):
    appointment_id: int
    date: date
    start_time: time
    end_time: time
    patient_name: str
    status: str

class AppointmentOutputPat(BaseModel):
    appointment_id: int
    date: date
    start_time: time
    end_time: time
    doctor_name: str
    status: str

class AppointmentFilter(str, Enum):
    upcoming = "upcoming"
    completed = "completed"
    cancelled = "cancelled"

class SlotsFilter(str, Enum):
    booked =  "booked"
    available = "available"
