from fastapi import FastAPI
from database import engine
from routers import user, auth, doctor, slot, appointment, patient
import models
from fastapi.responses import HTMLResponse



app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head><title>API Server</title></head>
        <body>
            <h1>Backend Running</h1>
            <p>If you're a developer:
Open /docs to explore and test the API.<p>

<p>If you're reviewing the project:
See the GitHub repository for architecture and implementation details.</p>
<p><a href="https://github.com/engrananthn-tech/hospital-appointment-backend">Git hub repo<a><p>

        </body>
    </html>
    """

app.include_router(user.router)
app.include_router(auth.router) 
app.include_router(doctor.router)
app.include_router(slot.router)
app.include_router(appointment.router)
app.include_router(patient.router)

