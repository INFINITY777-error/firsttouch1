# database.py — MedAssist AI v4.0 (Fixed & Enhanced)
# ─── ALL FIXES APPLIED ────────────────────────────────────────────────────────
# FIX 1: dosage column indentation error → fixed
# FIX 2: db.execute("SELECT 1") → wrapped in text() for SQLAlchemy 2.x
# FIX 3: declarative_base from sqlalchemy.orm (not deprecated ext.declarative)
# FIX 4: DiagnosticTest missing back-reference → added
# FIX 5: Consultation missing `tests` relationship → added
# FIX 6: connect_args missing for SQLite threading → added
# FIX 7: date_of_birth stored as DateTime but received as string → parse in CRUD
# FIX 8: pool_recycle added for MySQL 8hr timeout disconnects
# FIX 9: Symptom model missing to_dict() method → added
# ENHANCEMENT: Added full_name virtual field, BMI calculation, patient age from DOB
# ENHANCEMENT: Added ConsultationCRUD.count_by_patient, get_stats
# ENHANCEMENT: Added created_at to Symptom to_dict
# ──────────────────────────────────────────────────────────────────────────────

from dotenv import load_dotenv
load_dotenv()

import os
import enum
from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    DateTime, Float, ForeignKey, Boolean, Enum as SAEnum, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ─── Database URL ─────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./medassist.db"
)

# FIX 6: SQLite needs check_same_thread=False; MySQL needs pool_recycle to avoid 8hr timeout
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
pool_recycle  = 3600 if "mysql" in DATABASE_URL or "postgresql" in DATABASE_URL else -1

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,        # reconnect if connection dropped
    pool_recycle=pool_recycle, # FIX 8: prevent MySQL gone away error
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()  # FIX 3: from sqlalchemy.orm, not ext.declarative


# ─── Enums ────────────────────────────────────────────────────────────────────

class Gender(str, enum.Enum):
    MALE   = "Male"
    FEMALE = "Female"
    OTHER  = "Other"


class Severity(str, enum.Enum):
    MILD     = "Mild"
    MODERATE = "Moderate"
    SEVERE   = "Severe"
    CRITICAL = "Critical"


class UrgencyLevel(str, enum.Enum):
    NON_URGENT      = "Non-Urgent"
    SCHEDULE_VISIT  = "Schedule Visit Within 48-72 Hours"
    SEEK_CARE_TODAY = "Seek Care Today"
    EMERGENCY       = "Emergency"


# ─── Models ───────────────────────────────────────────────────────────────────

class Patient(Base):
    """Patient master record — stores identity and full clinical profile."""
    __tablename__ = "patients"

    id            = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Identity
    first_name    = Column(String(100), nullable=False)
    last_name     = Column(String(100), nullable=False)
    email         = Column(String(255), unique=True, index=True, nullable=True)
    phone         = Column(String(20),  nullable=True)
    date_of_birth = Column(DateTime,    nullable=True)
    age           = Column(Integer,     nullable=True)
    gender        = Column(String(20),  nullable=True)

    # Physical
    weight     = Column(Float,      nullable=True)  # kg
    height     = Column(Float,      nullable=True)  # cm
    blood_type = Column(String(10), nullable=True)

    # Medical background
    medical_history     = Column(Text, nullable=True)
    current_medications = Column(Text, nullable=True)
    allergies           = Column(Text, nullable=True)
    family_history      = Column(Text, nullable=True)

    # Lifestyle
    smoking_status = Column(String(50), nullable=True)
    alcohol_use    = Column(String(50), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active  = Column(Boolean,  default=True)

    # Relationships
    consultations = relationship(
        "Consultation", back_populates="patient", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Patient(id={self.id}, name='{self.first_name} {self.last_name}')>"

    def _calculate_bmi(self):
        """ENHANCEMENT: Calculate BMI if weight and height are available."""
        if self.weight and self.height and self.height > 0:
            bmi = self.weight / ((self.height / 100) ** 2)
            return round(bmi, 1)
        return None

    def _get_age_from_dob(self):
        """ENHANCEMENT: Auto-calculate age from date_of_birth if age not set."""
        if self.date_of_birth:
            today = date.today()
            dob   = self.date_of_birth.date() if isinstance(self.date_of_birth, datetime) else self.date_of_birth
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return self.age

    def to_dict(self):
        bmi = self._calculate_bmi()
        age = self._get_age_from_dob()
        return {
            "id":                  self.id,
            "first_name":          self.first_name,
            "last_name":           self.last_name,
            "full_name":           f"{self.first_name} {self.last_name}",
            "email":               self.email,
            "phone":               self.phone,
            "date_of_birth":       self.date_of_birth.strftime("%Y-%m-%d") if self.date_of_birth else None,
            "age":                 age,
            "gender":              self.gender,
            "weight":              self.weight,
            "height":              self.height,
            "bmi":                 bmi,
            "bmi_category":        _bmi_category(bmi) if bmi else None,
            "blood_type":          self.blood_type,
            "medical_history":     self.medical_history,
            "current_medications": self.current_medications,
            "allergies":           self.allergies,
            "family_history":      self.family_history,
            "smoking_status":      self.smoking_status,
            "alcohol_use":         self.alcohol_use,
            "created_at":          self.created_at.isoformat() if self.created_at else None,
            "updated_at":          self.updated_at.isoformat() if self.updated_at else None,
            "is_active":           self.is_active,
            "total_consultations": len(self.consultations) if self.consultations else 0,
        }


def _bmi_category(bmi: float) -> str:
    """ENHANCEMENT: Return BMI category string."""
    if bmi < 18.5: return "Underweight"
    if bmi < 25.0: return "Normal"
    if bmi < 30.0: return "Overweight"
    return "Obese"


class Consultation(Base):
    """One AI diagnosis session / clinic visit."""
    __tablename__ = "consultations"

    id         = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(
        Integer, ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Visit details
    consultation_date    = Column(DateTime,    default=datetime.utcnow)
    chief_complaint      = Column(Text,        nullable=True)
    duration_of_symptoms = Column(String(100), nullable=True)
    severity             = Column(String(20),  nullable=True)
    additional_notes     = Column(Text,        nullable=True)

    # AI output
    ai_diagnosis           = Column(Text,       nullable=True)
    differential_diagnoses = Column(Text,       nullable=True)
    urgency_level          = Column(String(50), nullable=True)

    # Model info
    model_used         = Column(String(100), nullable=True)
    model_provider     = Column(String(50),  nullable=True)
    web_search_enabled = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient       = relationship("Patient",         back_populates="consultations")
    symptoms      = relationship("Symptom",         back_populates="consultation", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription",    back_populates="consultation", cascade="all, delete-orphan")
    tests         = relationship("DiagnosticTest",  back_populates="consultation", cascade="all, delete-orphan")  # FIX 5

    def __repr__(self):
        return f"<Consultation(id={self.id}, patient_id={self.patient_id})>"

    def to_dict(self):
        return {
            "id":                    self.id,
            "patient_id":            self.patient_id,
            "consultation_date":     self.consultation_date.isoformat() if self.consultation_date else None,
            "chief_complaint":       self.chief_complaint,
            "duration_of_symptoms":  self.duration_of_symptoms,
            "severity":              self.severity,
            "additional_notes":      self.additional_notes,
            "ai_diagnosis":          self.ai_diagnosis,
            "differential_diagnoses": self.differential_diagnoses,
            "urgency_level":         self.urgency_level,
            "model_used":            self.model_used,
            "model_provider":        self.model_provider,
            "web_search_enabled":    self.web_search_enabled,
            "created_at":            self.created_at.isoformat() if self.created_at else None,
            "symptoms":              [s.to_dict() for s in self.symptoms]      if self.symptoms      else [],
            "prescriptions":         [p.to_dict() for p in self.prescriptions] if self.prescriptions else [],
            "tests":                 [t.to_dict() for t in self.tests]         if self.tests         else [],
        }


class Symptom(Base):
    """Individual symptom row linked to a consultation."""
    __tablename__ = "symptoms"

    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    consultation_id = Column(
        Integer, ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False
    )

    symptom_name = Column(String(200), nullable=False)
    category     = Column(String(100), nullable=True)
    severity     = Column(String(20),  nullable=True)
    onset_date   = Column(DateTime,    nullable=True)
    description  = Column(Text,        nullable=True)
    created_at   = Column(DateTime,    default=datetime.utcnow)

    consultation = relationship("Consultation", back_populates="symptoms")

    def __repr__(self):
        return f"<Symptom(id={self.id}, name='{self.symptom_name}')>"

    # FIX 9: Missing to_dict — caused symptoms to serialize as objects instead of dicts
    def to_dict(self):
        return {
            "id":           self.id,
            "symptom_name": self.symptom_name,
            "category":     self.category,
            "severity":     self.severity,
            "description":  self.description,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
        }


class Prescription(Base):
    """Medication recommendation from a consultation."""
    __tablename__ = "prescriptions"

    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    consultation_id = Column(
        Integer, ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False
    )

    medication_name = Column(String(200), nullable=False)
    medication_type = Column(String(50),  nullable=True)   # OTC or Prescription
    dosage          = Column(String(100), nullable=True)   # FIX 1: indentation was broken
    frequency       = Column(String(100), nullable=True)
    duration        = Column(String(100), nullable=True)
    purpose         = Column(Text,        nullable=True)
    instructions    = Column(Text,        nullable=True)
    warnings        = Column(Text,        nullable=True)
    is_otc          = Column(Boolean, default=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    consultation = relationship("Consultation", back_populates="prescriptions")

    def __repr__(self):
        return f"<Prescription(id={self.id}, medication='{self.medication_name}')>"

    def to_dict(self):
        return {
            "id":              self.id,
            "medication_name": self.medication_name,
            "medication_type": self.medication_type,
            "dosage":          self.dosage,
            "frequency":       self.frequency,
            "duration":        self.duration,
            "purpose":         self.purpose,
            "is_otc":          self.is_otc,
            "warnings":        self.warnings,
            "created_at":      self.created_at.isoformat() if self.created_at else None,
        }


class DiagnosticTest(Base):
    """Recommended lab / imaging test from a consultation."""
    __tablename__ = "diagnostic_tests"

    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    consultation_id = Column(
        Integer, ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False
    )

    test_name  = Column(String(200), nullable=False)
    test_type  = Column(String(100), nullable=True)
    priority   = Column(String(50),  nullable=True)
    reason     = Column(Text,        nullable=True)
    created_at = Column(DateTime,    default=datetime.utcnow)

    # FIX 4: Missing back-reference that caused relationship error
    consultation = relationship("Consultation", back_populates="tests")

    def __repr__(self):
        return f"<DiagnosticTest(id={self.id}, name='{self.test_name}')>"

    def to_dict(self):
        return {
            "id":        self.id,
            "test_name": self.test_name,
            "test_type": self.test_type,
            "priority":  self.priority,
            "reason":    self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ─── DB Lifecycle ─────────────────────────────────────────────────────────────

def init_db():
    """Create all tables. Safe to call on every startup (idempotent)."""
    Base.metadata.create_all(bind=engine)
    safe = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
    print(f"✅ Database tables ready — {safe}")


def drop_db():
    """Drop ALL tables. Irreversible — use only in dev/testing."""
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped!")


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── CRUD Operations ──────────────────────────────────────────────────────────

class PatientCRUD:

    @staticmethod
    def create(db, **kwargs) -> Patient:
        # FIX 7: Parse date_of_birth string → datetime before saving
        if "date_of_birth" in kwargs and isinstance(kwargs["date_of_birth"], str):
            try:
                kwargs["date_of_birth"] = datetime.strptime(kwargs["date_of_birth"], "%Y-%m-%d")
            except ValueError:
                kwargs.pop("date_of_birth")  # drop invalid date rather than crash

        patient = Patient(**kwargs)
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient

    @staticmethod
    def get_by_id(db, patient_id: int) -> Optional[Patient]:
        return db.query(Patient).filter(
            Patient.id == patient_id, Patient.is_active == True
        ).first()

    @staticmethod
    def get_by_email(db, email: str) -> Optional[Patient]:
        return db.query(Patient).filter(Patient.email == email).first()

    @staticmethod
    def get_all(db, skip: int = 0, limit: int = 100) -> List[Patient]:
        return (
            db.query(Patient)
            .filter(Patient.is_active == True)
            .order_by(Patient.created_at.desc())
            .offset(skip).limit(limit).all()
        )

    @staticmethod
    def search(db, query: str) -> List[Patient]:
        q = f"%{query}%"
        return (
            db.query(Patient)
            .filter(Patient.is_active == True)
            .filter(
                Patient.first_name.ilike(q) |
                Patient.last_name.ilike(q)  |
                Patient.email.ilike(q)      |
                Patient.phone.ilike(q)
            ).all()
        )

    @staticmethod
    def update(db, patient_id: int, **kwargs) -> Optional[Patient]:
        # FIX 7: Parse date_of_birth on update too
        if "date_of_birth" in kwargs and isinstance(kwargs["date_of_birth"], str):
            try:
                kwargs["date_of_birth"] = datetime.strptime(kwargs["date_of_birth"], "%Y-%m-%d")
            except ValueError:
                kwargs.pop("date_of_birth")

        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            for key, value in kwargs.items():
                if hasattr(patient, key) and value is not None:
                    setattr(patient, key, value)
            patient.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(patient)
        return patient

    @staticmethod
    def delete(db, patient_id: int) -> bool:
        """Soft delete — marks inactive, never destroys data."""
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            patient.is_active  = False
            patient.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False

    @staticmethod
    def count(db) -> int:
        return db.query(Patient).filter(Patient.is_active == True).count()


class ConsultationCRUD:

    @staticmethod
    def create(db, patient_id: int, symptoms: List[str], **kwargs) -> Consultation:
        """Create consultation + symptom rows in a single transaction."""
        consultation = Consultation(patient_id=patient_id, **kwargs)
        db.add(consultation)
        db.flush()  # get consultation.id before committing

        for symptom_name in symptoms:
            db.add(Symptom(
                consultation_id=consultation.id,
                symptom_name=symptom_name,
                severity=kwargs.get("severity"),
            ))

        db.commit()
        db.refresh(consultation)
        return consultation

    @staticmethod
    def get_by_id(db, consultation_id: int) -> Optional[Consultation]:
        return db.query(Consultation).filter(Consultation.id == consultation_id).first()

    @staticmethod
    def get_by_patient(db, patient_id: int, skip: int = 0, limit: int = 50) -> List[Consultation]:
        return (
            db.query(Consultation)
            .filter(Consultation.patient_id == patient_id)
            .order_by(Consultation.consultation_date.desc())
            .offset(skip).limit(limit).all()
        )

    @staticmethod
    def get_recent(db, limit: int = 20) -> List[Consultation]:
        return (
            db.query(Consultation)
            .order_by(Consultation.consultation_date.desc())
            .limit(limit).all()
        )

    @staticmethod
    def count_by_patient(db, patient_id: int) -> int:
        """ENHANCEMENT: Count consultations for a specific patient."""
        return db.query(Consultation).filter(Consultation.patient_id == patient_id).count()

    @staticmethod
    def add_prescription(db, consultation_id: int, **kwargs) -> Prescription:
        p = Prescription(consultation_id=consultation_id, **kwargs)
        db.add(p)
        db.commit()
        db.refresh(p)
        return p

    @staticmethod
    def add_diagnostic_test(db, consultation_id: int, **kwargs) -> DiagnosticTest:
        t = DiagnosticTest(consultation_id=consultation_id, **kwargs)
        db.add(t)
        db.commit()
        db.refresh(t)
        return t

    @staticmethod
    def count(db) -> int:
        return db.query(Consultation).count()


class PrescriptionCRUD:

    @staticmethod
    def get_by_patient(db, patient_id: int) -> List[Prescription]:
        return (
            db.query(Prescription)
            .join(Consultation)
            .filter(Consultation.patient_id == patient_id)
            .order_by(Prescription.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_consultation(db, consultation_id: int) -> List[Prescription]:
        return db.query(Prescription).filter(
            Prescription.consultation_id == consultation_id
        ).all()


# ─── Connection Test ──────────────────────────────────────────────────────────

def test_connection() -> bool:
    """Verify DB is reachable. Uses text() for SQLAlchemy 2.x compatibility."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # FIX 2: must use text() in SQLAlchemy 2.x
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def get_db_stats(db) -> dict:
    """ENHANCEMENT: Return aggregate DB statistics."""
    return {
        "total_patients":      db.query(Patient).filter(Patient.is_active == True).count(),
        "total_consultations": db.query(Consultation).count(),
        "total_symptoms":      db.query(Symptom).count(),
        "total_prescriptions": db.query(Prescription).count(),
    }


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🏥 MedAssist Database Module v4.0")
    safe_url = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
    print(f"📊 Connecting to: {safe_url}")
    if test_connection():
        init_db()
