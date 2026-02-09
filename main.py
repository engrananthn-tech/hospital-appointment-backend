from fastapi import FastAPI
from database import engine
from routers import user, auth, doctor, slot, appointment, patient
import models



app = FastAPI()




app.include_router(user.router)
app.include_router(auth.router)
app.include_router(doctor.router)
app.include_router(slot.router)
app.include_router(appointment.router)
app.include_router(patient.router)

