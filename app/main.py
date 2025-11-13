# app/main.py
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import URL
import csv
import io

from .hospital_core import HospitalSystem

app = FastAPI(title="Hospital Patient Management")

templates = Jinja2Templates(directory="templates")
# If you later add a static folder, mount it:
# app.mount("/static", StaticFiles(directory="static"), name="static")

system = HospitalSystem()

# seed sample data
try:
    system.add_patient("Ravi Kumar", "Fever", 3)
    system.add_patient("Anjali Verma", "Fracture", 2)
    system.add_patient("Suresh Patel", "Cardiac", 1)
except Exception:
    pass

@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard")
def dashboard(request: Request):
    active = system.view_active()
    discharged = system.view_discharged()
    return templates.TemplateResponse("index.html", {"request": request, "active": active, "discharged": discharged})

@app.post("/add")
async def add_patient(name: str = Form(...), disease: str = Form(...), priority: int = Form(...)):
    try:
        system.add_patient(name, disease, priority)
    except Exception as e:
        # redirect back with a simple query parameter message could be implemented
        # For now we just ignore and redirect (client shows messages via server logs)
        pass
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/discharge/{patient_id}")
async def discharge(patient_id: int, reason: str = Form("")):
    try:
        system.discharge_patient(patient_id, reason)
    except Exception:
        pass
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/undo")
async def undo():
    try:
        system.undo_last_discharge()
    except Exception:
        pass
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/history")
def history(request: Request):
    hist = system.view_history()
    return templates.TemplateResponse("history.html", {"request": request, "history": hist})

@app.get("/export")
def export_csv():
    # Build CSV in-memory
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Active Patients"])
    writer.writerow(["ID", "Name", "Disease", "Priority", "AdmittedAt"])
    for p in system.view_active():
        row = [p.id, p.name, p.disease, p.priority, p.admit_time.strftime("%Y-%m-%d %H:%M:%S")]
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Discharged Patients (top-first)"])
    writer.writerow(["ID", "Name", "Disease", "Priority", "DischargedAt"])
    for entry in system.view_discharged():
        patient, t, reason = entry
        writer.writerow([patient.id, patient.name, patient.disease, patient.priority, t.strftime("%Y-%m-%d %H:%M:%S")])
    buffer.seek(0)
    headers = {
        "Content-Disposition": "attachment; filename=patients_export.csv"
    }
    return StreamingResponse(iter([buffer.getvalue().encode("utf-8")]), media_type="text/csv", headers=headers)
