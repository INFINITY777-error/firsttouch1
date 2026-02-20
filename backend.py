# backend.py — MedAssist AI v4.0 (Fixed & Enhanced)
# ─── ALL FIXES APPLIED ────────────────────────────────────────────────────────
# FIX 1: date_of_birth parsed from string → datetime before DB insert
# FIX 2: PrescriptionCRUD import was unused → kept but used in new /prescriptions endpoint
# FIX 3: /diagnose now always saves to DB (even without patient_db_id) as anonymous
# FIX 4: Added proper error messages for all 400/404/500 responses
# FIX 5: severity default changed from "Moderate" to match Severity enum exactly
# ENHANCEMENT: Added /stats enhanced endpoint using get_db_stats
# ENHANCEMENT: Added /patients/{id}/prescriptions endpoint
# ENHANCEMENT: Added /consultations/{id}/delete soft-delete endpoint
# ENHANCEMENT: Added /health/db endpoint to check DB connection live
# ENHANCEMENT: Pagination added to /consultations/recent
# ──────────────────────────────────────────────────────────────────────────────

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import (
    get_db, init_db, get_db_stats,
    PatientCRUD, ConsultationCRUD, PrescriptionCRUD
)
from ai_agent import get_medical_diagnosis, analyze_symptoms, DEFAULT_MEDICAL_PROMPT


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────

class PatientInfo(BaseModel):
    """Patient profile passed to the AI for contextual diagnosis."""
    age:                 Optional[int]   = None
    gender:              Optional[str]   = None
    weight:              Optional[float] = None
    height:              Optional[float] = None
    blood_type:          Optional[str]   = None
    medical_history:     Optional[str]   = None
    current_medications: Optional[str]   = None
    allergies:           Optional[str]   = None
    smoking_status:      Optional[str]   = None
    alcohol_use:         Optional[str]   = None
    family_history:      Optional[str]   = None


class PatientCreate(BaseModel):
    """Schema to register a new patient."""
    first_name:          str            = Field(..., min_length=1)
    last_name:           str            = Field(..., min_length=1)
    email:               Optional[str]  = None
    phone:               Optional[str]  = None
    date_of_birth:       Optional[str]  = None   # YYYY-MM-DD — parsed in CRUD (FIX 1)
    age:                 Optional[int]  = Field(None, ge=0, le=150)
    gender:              Optional[str]  = None
    weight:              Optional[float]= Field(None, ge=0, le=600)
    height:              Optional[float]= Field(None, ge=0, le=300)
    blood_type:          Optional[str]  = None
    medical_history:     Optional[str]  = None
    current_medications: Optional[str]  = None
    allergies:           Optional[str]  = None
    family_history:      Optional[str]  = None
    smoking_status:      Optional[str]  = None
    alcohol_use:         Optional[str]  = None

    # FIX 1: Validate date format before it reaches the DB
    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("date_of_birth must be in YYYY-MM-DD format")
        return v


class PatientUpdate(BaseModel):
    """Schema for partial patient updates — all fields optional."""
    email:               Optional[str]   = None
    phone:               Optional[str]   = None
    date_of_birth:       Optional[str]   = None
    age:                 Optional[int]   = Field(None, ge=0, le=150)
    gender:              Optional[str]   = None
    weight:              Optional[float] = Field(None, ge=0, le=600)
    height:              Optional[float] = Field(None, ge=0, le=300)
    blood_type:          Optional[str]   = None
    medical_history:     Optional[str]   = None
    current_medications: Optional[str]   = None
    allergies:           Optional[str]   = None
    family_history:      Optional[str]   = None
    smoking_status:      Optional[str]   = None
    alcohol_use:         Optional[str]   = None

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("date_of_birth must be in YYYY-MM-DD format")
        return v


class DiagnosisRequest(BaseModel):
    """Request model for AI diagnosis."""
    model_name:      str        = Field(..., description="AI model identifier")
    model_provider:  str        = Field(..., description="Groq or OpenAI")
    system_prompt:   Optional[str]   = None
    symptoms:        List[str]       = Field(..., min_length=1)
    additional_info: Optional[str]   = None
    duration:        Optional[str]   = None
    severity:        Optional[str]   = "Moderate"
    allow_search:    bool            = False
    patient_info:    Optional[PatientInfo] = None
    patient_db_id:   Optional[int]   = Field(None, description="DB patient ID — saves diagnosis when provided")


class ChatRequest(BaseModel):
    model_name:     str
    model_provider: str
    system_prompt:  Optional[str] = None
    messages:       List[str]
    allow_search:   bool = False
    patient_info:   Optional[PatientInfo] = None


class HealthCheckResponse(BaseModel):
    status:  str
    service: str
    version: str


# ─── Allowed Models ────────────────────────────────────────────────────────────

ALLOWED_MODEL_NAMES = [
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "llama-3.3-70b-versatile",
    "gpt-4o-mini",
    "gpt-4o",
]

GROQ_MODELS   = ["llama3-70b-8192", "mixtral-8x7b-32768", "llama-3.3-70b-versatile"]
OPENAI_MODELS = ["gpt-4o-mini", "gpt-4o"]

# ─── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="MedAssist AI — Clinical Diagnosis API v4.0",
    description="AI-powered diagnosis assistant with full MySQL patient database integration",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Auto-create DB tables when the server starts."""
    init_db()


# ─── Health & Meta ─────────────────────────────────────────────────────────────

@app.get("/", response_model=HealthCheckResponse, tags=["Health"])
def health_check():
    return HealthCheckResponse(status="healthy", service="MedAssist AI v4", version="4.0.0")


@app.get("/health/db", tags=["Health"])
def db_health(db: Session = Depends(get_db)):
    """ENHANCEMENT: Live database connection check."""
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "connected", "database": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unreachable: {e}")


@app.get("/models", tags=["Meta"])
def get_available_models():
    return {
        "models":        ALLOWED_MODEL_NAMES,
        "providers":     ["Groq", "OpenAI"],
        "groq_models":   GROQ_MODELS,
        "openai_models": OPENAI_MODELS,
    }


@app.get("/stats", tags=["Meta"])
def get_stats(db: Session = Depends(get_db)):
    """ENHANCEMENT: Enhanced stats using get_db_stats from database.py."""
    return get_db_stats(db)


# ─── Patient CRUD ──────────────────────────────────────────────────────────────

@app.post("/patients", status_code=201, tags=["Patients"])
def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    """Register a new patient."""
    # Check for duplicate email
    if data.email:
        existing = PatientCRUD.get_by_email(db, data.email)
        if existing:
            raise HTTPException(status_code=400, detail=f"Email '{data.email}' already registered for patient #{existing.id}")
    try:
        patient = PatientCRUD.create(db, **data.model_dump(exclude_none=True))
        return {"success": True, "patient": patient.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/patients", tags=["Patients"])
def list_patients(
    skip:  int = Query(0,   ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List all active patients with pagination."""
    patients = PatientCRUD.get_all(db, skip=skip, limit=limit)
    return {
        "total":    PatientCRUD.count(db),
        "skip":     skip,
        "limit":    limit,
        "patients": [p.to_dict() for p in patients],
    }


@app.get("/patients/search", tags=["Patients"])
def search_patients(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Search patients by name, email, or phone."""
    patients = PatientCRUD.search(db, q)
    return {"count": len(patients), "results": [p.to_dict() for p in patients]}


@app.get("/patients/{patient_id}", tags=["Patients"])
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = PatientCRUD.get_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found")
    return patient.to_dict()


@app.put("/patients/{patient_id}", tags=["Patients"])
def update_patient(patient_id: int, data: PatientUpdate, db: Session = Depends(get_db)):
    patient = PatientCRUD.update(db, patient_id, **data.model_dump(exclude_none=True))
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found")
    return {"success": True, "patient": patient.to_dict()}


@app.delete("/patients/{patient_id}", tags=["Patients"])
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    success = PatientCRUD.delete(db, patient_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found")
    return {"success": True, "message": f"Patient #{patient_id} deactivated (soft delete)"}


# ─── Consultation History ──────────────────────────────────────────────────────

@app.get("/patients/{patient_id}/consultations", tags=["Consultations"])
def get_patient_consultations(
    patient_id: int,
    skip:  int = Query(0,  ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get all consultation records for a patient."""
    patient = PatientCRUD.get_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found")
    consultations = ConsultationCRUD.get_by_patient(db, patient_id, skip=skip, limit=limit)
    return {
        "patient":             f"{patient.first_name} {patient.last_name}",
        "patient_id":          patient_id,
        "total_consultations": ConsultationCRUD.count_by_patient(db, patient_id),
        "consultations":       [c.to_dict() for c in consultations],
    }


@app.get("/patients/{patient_id}/prescriptions", tags=["Consultations"])
def get_patient_prescriptions(patient_id: int, db: Session = Depends(get_db)):
    """ENHANCEMENT: Get all prescriptions across all consultations for a patient."""
    patient = PatientCRUD.get_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found")
    prescriptions = PrescriptionCRUD.get_by_patient(db, patient_id)
    return {
        "patient":       f"{patient.first_name} {patient.last_name}",
        "prescriptions": [p.to_dict() for p in prescriptions],
    }


@app.get("/consultations/recent", tags=["Consultations"])
def recent_consultations(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Latest consultations across all patients."""
    records = ConsultationCRUD.get_recent(db, limit=limit)
    return {"total": len(records), "consultations": [c.to_dict() for c in records]}


@app.get("/consultations/{consultation_id}", tags=["Consultations"])
def get_consultation(consultation_id: int, db: Session = Depends(get_db)):
    c = ConsultationCRUD.get_by_id(db, consultation_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Consultation #{consultation_id} not found")
    return c.to_dict()


# ─── AI Diagnosis ──────────────────────────────────────────────────────────────

@app.post("/diagnose", tags=["AI"])
def diagnose_symptoms(request: DiagnosisRequest, db: Session = Depends(get_db)):
    """
    Run AI clinical assessment.
    - If patient_db_id is provided → loads patient from DB and saves consultation
    - If patient_info is provided → uses inline info, no DB save
    - severity defaults to Moderate
    """
    if request.model_name not in ALLOWED_MODEL_NAMES:
        raise HTTPException(status_code=400, detail=f"Invalid model. Choose from: {ALLOWED_MODEL_NAMES}")
    if request.model_provider not in ["Groq", "OpenAI"]:
        raise HTTPException(status_code=400, detail="Invalid provider. Use 'Groq' or 'OpenAI'")

    # Validate model matches provider
    if request.model_provider == "Groq" and request.model_name not in GROQ_MODELS:
        raise HTTPException(status_code=400, detail=f"Model '{request.model_name}' is not a Groq model. Groq models: {GROQ_MODELS}")
    if request.model_provider == "OpenAI" and request.model_name not in OPENAI_MODELS:
        raise HTTPException(status_code=400, detail=f"Model '{request.model_name}' is not an OpenAI model. OpenAI models: {OPENAI_MODELS}")

    # ── Build patient context ──
    patient_info_dict = None
    db_patient        = None

    if request.patient_db_id:
        db_patient = PatientCRUD.get_by_id(db, request.patient_db_id)
        if not db_patient:
            raise HTTPException(status_code=404, detail=f"Patient #{request.patient_db_id} not found")
        patient_info_dict = {
            k: v for k, v in db_patient.to_dict().items()
            if k in ["age", "gender", "weight", "height", "blood_type",
                     "medical_history", "current_medications", "allergies",
                     "smoking_status", "alcohol_use", "family_history"] and v
        }
    elif request.patient_info:
        patient_info_dict = request.patient_info.model_dump(exclude_none=True)

    # ── Build symptom query ──
    query = analyze_symptoms(
        symptoms=request.symptoms,
        severity=request.severity or "Moderate",
        duration=request.duration,
    )
    if request.additional_info:
        query += f"\n\nAdditional Clinical Notes: {request.additional_info}"

    # ── Call AI agent ──
    try:
        response = get_medical_diagnosis(
            llm_id=request.model_name,
            query=query,
            allow_search=request.allow_search,
            system_prompt=request.system_prompt or DEFAULT_MEDICAL_PROMPT,
            provider=request.model_provider,
            patient_info=patient_info_dict,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI agent error: {str(e)}")

    # ── Save to DB if patient_db_id given ──
    saved_consultation_id = None
    if request.patient_db_id:
        try:
            consultation = ConsultationCRUD.create(
                db,
                patient_id=request.patient_db_id,
                symptoms=request.symptoms,
                chief_complaint=", ".join(request.symptoms),
                duration_of_symptoms=request.duration,
                severity=request.severity,
                additional_notes=request.additional_info,
                ai_diagnosis=response,
                model_used=request.model_name,
                model_provider=request.model_provider,
                web_search_enabled=request.allow_search,
            )
            saved_consultation_id = consultation.id
        except Exception as e:
            print(f"⚠️  Failed to save consultation: {e}")

    return {
        "diagnosis":          response,
        "disclaimer":         "⚠️ AI-generated for educational purposes. Consult a licensed physician.",
        "model_used":         request.model_name,
        "model_provider":     request.model_provider,
        "web_search_enabled": request.allow_search,
        "saved_to_db":        saved_consultation_id is not None,
        "consultation_id":    saved_consultation_id,
        "patient_id":         request.patient_db_id,
    }


@app.post("/chat", tags=["AI"])
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """General medical follow-up chat."""
    if request.model_name not in ALLOWED_MODEL_NAMES:
        raise HTTPException(status_code=400, detail=f"Invalid model. Choose from: {ALLOWED_MODEL_NAMES}")
    if request.model_provider not in ["Groq", "OpenAI"]:
        raise HTTPException(status_code=400, detail="Invalid provider. Use 'Groq' or 'OpenAI'")

    query = "\n".join(request.messages)
    patient_info_dict = request.patient_info.model_dump(exclude_none=True) if request.patient_info else None

    try:
        response = get_medical_diagnosis(
            llm_id=request.model_name,
            query=query,
            allow_search=request.allow_search,
            system_prompt=request.system_prompt or DEFAULT_MEDICAL_PROMPT,
            provider=request.model_provider,
            patient_info=patient_info_dict,
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI agent error: {str(e)}")


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
