# frontend.py — MedAssist AI v4.0 (Fixed & Enhanced)
# ─── ALL FIXES APPLIED ────────────────────────────────────────────────────────
# FIX 1: patient_db_id never sent in /diagnose payload → now sent from sidebar
# FIX 2: Sidebar patient dropdown was missing → added with live DB load
# FIX 3: No DB save confirmation shown → added success/warning message
# FIX 4: API_URL defined inside tab scope → moved to top-level constant
# FIX 5: Chat sent empty {} for patient_info → now sends None if empty
# ENHANCEMENT: Added full Patient Management tab (register, view, search, history)
# ENHANCEMENT: Added DB Stats dashboard in sidebar
# ENHANCEMENT: Added BMI display in patient cards
# ENHANCEMENT: Added soft-delete button per patient
# ──────────────────────────────────────────────────────────────────────────────

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"  # FIX 4: top-level constant

st.set_page_config(
    page_title="Dr. MedAssist AI — Clinical Diagnosis",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');
*,*::before,*::after{box-sizing:border-box}
.stApp{background:#0a0f1e;font-family:'DM Sans',sans-serif;color:#e8edf5}
#MainMenu,footer,header{visibility:hidden}.stDeployButton{display:none}
.stApp::before{content:'';position:fixed;top:0;left:0;right:0;bottom:0;
  background-image:radial-gradient(ellipse at 20% 10%,rgba(0,102,204,.12) 0%,transparent 50%),
  radial-gradient(ellipse at 80% 90%,rgba(0,196,180,.08) 0%,transparent 50%);
  pointer-events:none;z-index:0}
.clinic-header{background:linear-gradient(135deg,#0d1628 0%,#0a1525 40%,#0d2040 100%);
  border:1px solid rgba(0,150,255,.15);border-radius:20px;padding:2.5rem 3rem;
  margin-bottom:2rem;position:relative;overflow:hidden}
.clinic-header::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,#0096ff,#00c4b4,transparent)}
.clinic-header::after{content:'✚';position:absolute;right:2rem;top:50%;transform:translateY(-50%);
  font-size:5rem;opacity:.04;color:#0096ff}
.clinic-title{font-family:'DM Serif Display',serif;font-size:2.8rem;font-weight:400;
  color:#fff;letter-spacing:-.02em;margin:0 0 .3rem 0;line-height:1.1}
.clinic-title span{background:linear-gradient(135deg,#0096ff,#00c4b4);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.clinic-subtitle{font-size:.95rem;color:#6b8cad;font-weight:300;letter-spacing:.05em;text-transform:uppercase;margin:0}
.clinic-badge{display:inline-block;background:rgba(0,150,255,.1);border:1px solid rgba(0,150,255,.25);
  border-radius:20px;padding:.25rem .75rem;font-size:.75rem;color:#4db8ff;
  letter-spacing:.1em;text-transform:uppercase;margin-top:.75rem}
.alert-warning{background:linear-gradient(135deg,rgba(255,152,0,.08),rgba(255,193,7,.05));
  border:1px solid rgba(255,152,0,.25);border-left:3px solid #ff9800;border-radius:12px;
  padding:1rem 1.25rem;margin-bottom:1.5rem;font-size:.88rem;color:#f0b96b;line-height:1.6}
.alert-emergency{background:linear-gradient(135deg,rgba(244,67,54,.1),rgba(229,57,53,.06));
  border:1px solid rgba(244,67,54,.3);border-left:3px solid #f44336;border-radius:12px;
  padding:1.25rem 1.5rem;margin:1.5rem 0;color:#ff8a80}
.alert-emergency h4{color:#ff5252;font-weight:600;margin:0 0 .75rem 0;font-size:.9rem;
  text-transform:uppercase;letter-spacing:.08em}
.alert-emergency ul{margin:0;padding-left:1.25rem;font-size:.87rem;line-height:1.9}
.diagnosis-panel{background:linear-gradient(145deg,#0b1a2e,#081422);
  border:1px solid rgba(0,150,255,.2);border-radius:16px;padding:2rem;margin-top:1rem;
  position:relative;overflow:hidden}
.diagnosis-panel::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,#0096ff,#00c4b4,#0096ff)}
.diagnosis-header{display:flex;align-items:center;gap:.75rem;margin-bottom:1.5rem;
  padding-bottom:1rem;border-bottom:1px solid rgba(255,255,255,.05)}
.diagnosis-header h3{font-family:'DM Serif Display',serif;font-size:1.3rem;color:#e8edf5;margin:0}
.status-dot{width:10px;height:10px;background:#00c4b4;border-radius:50%;animation:pulse-dot 2s infinite;flex-shrink:0}
@keyframes pulse-dot{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.6;transform:scale(.8)}}
.diagnosis-panel h2{font-family:'DM Serif Display',serif;font-size:1.4rem;color:#e8edf5;
  border-bottom:1px solid rgba(0,150,255,.15);padding-bottom:.5rem;margin-top:1.5rem}
.diagnosis-panel h3{font-size:1rem;color:#4db8ff;font-weight:500;margin-top:1.25rem}
.diagnosis-panel table{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.87rem}
.diagnosis-panel th{background:rgba(0,150,255,.1);color:#4db8ff;padding:.6rem 1rem;text-align:left;
  font-weight:500;font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;border:1px solid rgba(0,150,255,.15)}
.diagnosis-panel td{padding:.6rem 1rem;border:1px solid rgba(255,255,255,.05);color:#b0c4d8;line-height:1.5}
.diagnosis-panel tr:hover td{background:rgba(0,150,255,.04)}
.diagnosis-panel blockquote{border-left:3px solid rgba(255,152,0,.4);background:rgba(255,152,0,.05);
  padding:.75rem 1rem;margin:.75rem 0;border-radius:0 8px 8px 0;color:#f0b96b;font-size:.87rem}
.diagnosis-panel code{background:rgba(0,150,255,.12);color:#4db8ff;padding:.15rem .4rem;border-radius:4px;font-size:.85em}
.diagnosis-panel ul,.diagnosis-panel ol{padding-left:1.5rem;line-height:1.8;color:#b0c4d8}
.diagnosis-panel li{margin-bottom:.25rem}
.diagnosis-panel strong{color:#e8edf5}
.diagnosis-panel hr{border:none;border-top:1px solid rgba(255,255,255,.06);margin:1.5rem 0}
.diagnosis-panel p{line-height:1.7;color:#b0c4d8}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#080e1c 0%,#060b16 100%) !important;
  border-right:1px solid rgba(255,255,255,.05) !important}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stNumberInput>div>div>input{
  background:rgba(255,255,255,.04) !important;border:1px solid rgba(255,255,255,.1) !important;
  border-radius:10px !important;color:#e8edf5 !important;font-family:'DM Sans',sans-serif !important;font-size:.9rem !important}
.stSelectbox>div>div{background:rgba(255,255,255,.04) !important;border:1px solid rgba(255,255,255,.1) !important;
  border-radius:10px !important;color:#e8edf5 !important}
.stButton>button{font-family:'DM Sans',sans-serif !important;font-weight:500 !important;border-radius:10px !important;transition:all .2s ease !important}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#0066cc,#0096ff) !important;
  border:none !important;color:white !important;font-size:.95rem !important;box-shadow:0 4px 15px rgba(0,100,200,.3) !important}
.stButton>button[kind="primary"]:hover{transform:translateY(-1px) !important;box-shadow:0 6px 20px rgba(0,100,200,.4) !important}
.stButton>button[kind="secondary"]{background:rgba(255,255,255,.05) !important;border:1px solid rgba(255,255,255,.12) !important;color:#b0c4d8 !important}
.stTabs [data-baseweb="tab-list"]{gap:.25rem;background:rgba(255,255,255,.03);border-radius:12px;padding:.3rem}
.stTabs [data-baseweb="tab"]{background:transparent;border-radius:8px;color:#6b8cad;font-size:.87rem;font-weight:500;padding:.5rem 1rem;transition:all .2s}
.stTabs [aria-selected="true"]{background:rgba(0,150,255,.15) !important;color:#4db8ff !important}
.metric-row{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:1rem 0}
.metric-card{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:1rem 1.25rem;text-align:center}
.metric-value{font-family:'DM Serif Display',serif;font-size:1.8rem;color:#4db8ff;line-height:1;margin-bottom:.25rem}
.metric-label{font-size:.75rem;color:#6b8cad;text-transform:uppercase;letter-spacing:.1em}
.symptom-tag{display:inline-block;background:rgba(0,150,255,.12);border:1px solid rgba(0,150,255,.25);
  border-radius:20px;padding:.25rem .75rem;font-size:.8rem;color:#4db8ff;margin:.2rem}
.symptom-tags-container{margin:.75rem 0;line-height:2}
.model-info-card{background:rgba(0,150,255,.06);border:1px solid rgba(0,150,255,.15);
  border-radius:10px;padding:.75rem 1rem;font-size:.82rem;color:#6b8cad;margin-top:.5rem}
.model-info-card strong{color:#4db8ff}
.db-stat-card{background:rgba(0,196,180,.06);border:1px solid rgba(0,196,180,.2);border-radius:10px;
  padding:.6rem 1rem;font-size:.82rem;color:#6b8cad;margin:.3rem 0;display:flex;justify-content:space-between}
.db-stat-card strong{color:#00c4b4}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:rgba(255,255,255,.03)}
::-webkit-scrollbar-thumb{background:rgba(0,150,255,.25);border-radius:3px}
@keyframes shimmer{0%{background-position:-1000px 0}100%{background-position:1000px 0}}
.loading-bar{height:3px;background:linear-gradient(90deg,transparent,#0096ff,#00c4b4,transparent);
  background-size:1000px 100%;animation:shimmer 2s linear infinite;border-radius:2px;margin-bottom:1rem}
.severity-label-low{color:#81c784;font-weight:600}
.severity-label-moderate{color:#ffd54f;font-weight:600}
.severity-label-severe{color:#ff8a80;font-weight:600}
.severity-label-critical{color:#ff1744;font-weight:600}
.stCheckbox>label{color:#b0c4d8 !important;font-size:.88rem !important}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="clinic-header">
    <div class="clinic-title">🩺 Dr. MedAssist <span>AI</span></div>
    <p class="clinic-subtitle">Advanced Clinical Diagnosis System · Powered by Large Language Models</p>
    <span class="clinic-badge">🔴 Live System · v4.0</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="alert-warning">
    <strong>⚠️ Medical Disclaimer:</strong> Dr. MedAssist AI provides preliminary health information for
    <strong>educational purposes only</strong>. It does NOT replace licensed medical advice, diagnosis, or treatment.
    All prescription recommendations are general guidelines. <strong>Emergency? Call 112 / 911 immediately.</strong>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Clinical Configuration")
    st.divider()

    MODEL_GROQ   = ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768"]
    MODEL_OPENAI = ["gpt-4o-mini", "gpt-4o"]

    provider = st.radio("Provider:", ("Groq", "OpenAI"), horizontal=True)
    if provider == "Groq":
        selected_model = st.selectbox("Model:", MODEL_GROQ)
        st.markdown(f'<div class="model-info-card"><strong>🟢 Groq</strong> — Ultra-fast inference<br>Model: <strong>{selected_model}</strong></div>', unsafe_allow_html=True)
    else:
        selected_model = st.selectbox("Model:", MODEL_OPENAI)
        st.markdown(f'<div class="model-info-card"><strong>🔵 OpenAI</strong> — Highest accuracy<br>Model: <strong>{selected_model}</strong></div>', unsafe_allow_html=True)

    st.divider()
    allow_web_search = st.checkbox("🌐 Enable Medical Research Search", value=False,
        help="Allows AI to search for latest clinical research via Tavily")
    st.divider()

    # FIX 1 & 2: Patient DB selector
    st.markdown("### 🗄️ Link to Database Patient")
    st.caption("Select a registered patient to save diagnosis to DB")

    selected_patient_db_id = None
    try:
        pts_resp = requests.get(f"{API_URL}/patients", timeout=5)
        if pts_resp.status_code == 200:
            pts_data = pts_resp.json().get("patients", [])
            options  = {"— None (don't save to DB) —": None}
            for p in pts_data:
                label = f"#{p['id']} — {p['first_name']} {p['last_name']}"
                if p.get("age"):    label += f" ({p['age']}y)"
                if p.get("gender"): label += f" · {p['gender']}"
                options[label] = p["id"]
            sel                    = st.selectbox("Select Patient:", list(options.keys()))
            selected_patient_db_id = options[sel]
        else:
            st.caption("⚠️ Could not load patients.")
    except Exception:
        st.caption("⚠️ Backend not connected.")

    st.divider()

    st.markdown("### 👤 Manual Patient Profile")
    st.caption("Used when no DB patient is selected")

    with st.expander("📋 Basic Information"):
        col_a, col_b = st.columns(2)
        with col_a:
            patient_age    = st.number_input("Age", min_value=0, max_value=120, value=None, step=1)
        with col_b:
            patient_gender = st.selectbox("Sex", ["", "Male", "Female", "Other"])
        col_c, col_d = st.columns(2)
        with col_c:
            patient_weight = st.number_input("Weight (kg)", min_value=0.0, max_value=500.0, value=None, step=0.5)
        with col_d:
            patient_height = st.number_input("Height (cm)", min_value=0.0, max_value=300.0, value=None, step=0.5)
        blood_type = st.selectbox("Blood Type", ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"])

    with st.expander("🏥 Medical History"):
        medical_history     = st.text_area("Chronic Conditions", placeholder="e.g., Diabetes...", height=70)
        current_medications = st.text_area("Current Medications", placeholder="e.g., Metformin 500mg...", height=70)
<<<<<<< HEAD
        allergies           = st.text_area("⚠️ Known Allergies", placeholder="e.g., Penicillin...", height=100)
        family_history      = st.text_area("Family History", placeholder="e.g., Father — Heart disease...", height=100)
=======
        allergies           = st.text_area("⚠️ Known Allergies", placeholder="e.g., Penicillin...", height=60)
        family_history      = st.text_area("Family History", placeholder="e.g., Father — Heart disease...", height=60)
>>>>>>> 538e32a97e76771e475982fd7138b67f0b94a2ad

    with st.expander("🧬 Lifestyle"):
        smoking_status = st.selectbox("Smoking Status", ["", "Non-smoker", "Ex-smoker", "Light smoker", "Heavy smoker"])
        alcohol_use    = st.selectbox("Alcohol Use", ["", "None", "Occasional", "Moderate", "Heavy"])

    st.divider()
    with st.expander("🤖 Agent Customization"):
        custom_prompt = st.text_area("Custom System Prompt", placeholder="Override AI behavior...", height=100)

    st.divider()
    st.markdown("### 📊 Database Stats")
    try:
        stats_resp = requests.get(f"{API_URL}/stats", timeout=3)
        if stats_resp.status_code == 200:
            s = stats_resp.json()
            st.markdown(f"""
            <div class="db-stat-card">Patients <strong>{s.get('total_patients',0)}</strong></div>
            <div class="db-stat-card">Consultations <strong>{s.get('total_consultations',0)}</strong></div>
            <div class="db-stat-card">Symptoms logged <strong>{s.get('total_symptoms',0)}</strong></div>
            <div class="db-stat-card">Prescriptions <strong>{s.get('total_prescriptions',0)}</strong></div>
            """, unsafe_allow_html=True)
        else:
            st.caption("Could not load stats.")
    except Exception:
        st.caption("Backend not connected.")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_diagnose, tab_chat, tab_patients = st.tabs([
    "🔬 Symptom Analysis & Diagnosis",
    "💬 Follow-up Consultation",
    "👤 Patient Management"
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: DIAGNOSIS
# ─────────────────────────────────────────────────────────────────────────────
with tab_diagnose:
    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        st.markdown("### 📋 Clinical Intake Form")
        input_method = st.radio("Symptom Entry Method:", ["✍️ Free-form Description", "☑️ Symptom Checklist"], horizontal=True)
        st.markdown("")

        if "✍️" in input_method:
            symptoms_text = st.text_area(
                "Describe your symptoms in detail:",
                placeholder="Example: I have been experiencing a persistent throbbing headache for the past 3 days, accompanied by a fever of 38.5°C, photophobia, and neck stiffness...",
                height=180
            )
            symptoms_list = [symptoms_text.strip()] if symptoms_text.strip() else []
        else:
            st.caption("Select all symptoms that apply:")
            symptom_categories = {
                "🌡️ General":        ["Fever","Chills","Fatigue","Weakness","Weight Loss","Night Sweats","Malaise"],
                "🧠 Neurological":   ["Headache","Migraine","Dizziness","Confusion","Seizure","Memory Issues","Numbness","Tingling"],
                "👁️ Head & ENT":    ["Vision Changes","Eye Pain","Ear Pain","Hearing Loss","Nasal Congestion","Sore Throat","Neck Stiffness"],
                "🫁 Respiratory":    ["Cough","Dry Cough","Productive Cough","Shortness of Breath","Wheezing","Chest Tightness"],
                "❤️ Cardiovascular": ["Chest Pain","Palpitations","Irregular Heartbeat","Leg Swelling","Fainting"],
                "🫃 Digestive":      ["Nausea","Vomiting","Diarrhea","Constipation","Abdominal Pain","Bloating","Heartburn","Blood in Stool"],
                "🦴 Musculoskeletal":["Joint Pain","Muscle Aches","Back Pain","Neck Pain","Stiffness","Swelling","Limited Mobility"],
                "🩹 Skin":           ["Rash","Itching","Hives","Skin Discoloration","Bruising","Lesions","Jaundice"],
                "🚽 Urinary":        ["Frequent Urination","Painful Urination","Blood in Urine","Urinary Incontinence"],
                "🧠 Mental Health":  ["Anxiety","Depression","Insomnia","Mood Changes","Panic Attacks"],
            }
            selected_symptoms = []
            for category, symptoms in symptom_categories.items():
                with st.expander(category):
                    cols = st.columns(2)
                    for i, symptom in enumerate(symptoms):
                        with cols[i % 2]:
                            if st.checkbox(symptom, key=f"s_{symptom}"):
                                selected_symptoms.append(symptom)
            symptoms_list = selected_symptoms
            if symptoms_list:
                tags_html = "".join([f'<span class="symptom-tag">✓ {s}</span>' for s in symptoms_list])
                st.markdown(f'<div class="symptom-tags-container">{tags_html}</div>', unsafe_allow_html=True)

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            duration = st.text_input("⏱️ Duration of Symptoms", placeholder="e.g., 3 days, 2 weeks...")
        with col2:
            severity = st.select_slider("📊 Severity", options=["Mild","Moderate","Severe","Critical"], value="Moderate")

        severity_colors = {"Mild":"severity-label-low","Moderate":"severity-label-moderate",
                           "Severe":"severity-label-severe","Critical":"severity-label-critical"}
        st.markdown(f'<span class="{severity_colors[severity]}">Severity: {severity}</span>', unsafe_allow_html=True)

        additional_info = st.text_area("📝 Additional Clinical Notes",
            placeholder="Aggravating/relieving factors, recent travel, exposures, previous similar episodes...", height=90)

        st.markdown("")
        analyze_btn = st.button("🔬 Run Clinical Analysis", type="primary", use_container_width=True)

    with right_col:
        st.markdown("### 📊 Clinical Assessment Report")

        if analyze_btn:
            if symptoms_list and any(s.strip() for s in symptoms_list):
                with st.spinner("⚕️ Performing clinical analysis..."):
                    progress_placeholder = st.empty()
                    progress_placeholder.markdown('<div class="loading-bar"></div>', unsafe_allow_html=True)

                    patient_info = {}
                    if patient_age:         patient_info["age"]                 = patient_age
                    if patient_gender:      patient_info["gender"]              = patient_gender
                    if patient_weight:      patient_info["weight"]              = patient_weight
                    if patient_height:      patient_info["height"]              = patient_height
                    if blood_type:          patient_info["blood_type"]          = blood_type
                    if medical_history:     patient_info["medical_history"]     = medical_history
                    if current_medications: patient_info["current_medications"] = current_medications
                    if allergies:           patient_info["allergies"]           = allergies
                    if family_history:      patient_info["family_history"]      = family_history
                    if smoking_status:      patient_info["smoking_status"]      = smoking_status
                    if alcohol_use:         patient_info["alcohol_use"]         = alcohol_use

                    # FIX 1: Include patient_db_id
                    payload = {
                        "model_name":      selected_model,
                        "model_provider":  provider,
                        "system_prompt":   custom_prompt if custom_prompt else None,
                        "symptoms":        symptoms_list,
                        "additional_info": f"Severity: {severity}. {additional_info}" if additional_info else f"Severity: {severity}",
                        "duration":        duration if duration else None,
                        "allow_search":    allow_web_search,
                        "patient_info":    patient_info if patient_info and not selected_patient_db_id else None,
                        "patient_db_id":   selected_patient_db_id,
                    }

                    try:
                        response = requests.post(f"{API_URL}/diagnose", json=payload, timeout=180)
                        progress_placeholder.empty()

                        if response.status_code == 200:
                            result = response.json()

                            st.markdown(f"""
                            <div class="metric-row">
                                <div class="metric-card">
                                    <div class="metric-value">{"🌐" if result.get("web_search_enabled") else "🧠"}</div>
                                    <div class="metric-label">{"Web Enhanced" if result.get("web_search_enabled") else "Knowledge Base"}</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" style="font-size:1.1rem">⚕️</div>
                                    <div class="metric-label">{result.get('model_used','N/A')}</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value">{len(symptoms_list)}</div>
                                    <div class="metric-label">Symptoms</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            st.markdown("""
                            <div class="diagnosis-panel">
                                <div class="diagnosis-header">
                                    <div class="status-dot"></div>
                                    <h3>Clinical Assessment Report</h3>
                                </div>
                            </div>""", unsafe_allow_html=True)

                            with st.container():
                                st.markdown(result["diagnosis"])

                            st.divider()
                            st.warning(f"⚕️ {result.get('disclaimer','Consult a licensed physician.')}")

                            # FIX 3: DB save confirmation
                            if result.get("saved_to_db"):
                                st.success(f"✅ Diagnosis saved to database! Consultation ID: **#{result.get('consultation_id')}**")
                            elif selected_patient_db_id:
                                st.warning("⚠️ Diagnosis ran but could not be saved to database. Check backend logs.")
                            else:
                                st.info("💡 Tip: Select a patient in the sidebar to save this diagnosis to the database.")

                        else:
                            progress_placeholder.empty()
                            st.error(f"❌ API Error {response.status_code}: {response.json().get('detail','Unknown error')}")

                    except requests.exceptions.ConnectionError:
                        progress_placeholder.empty()
                        st.error("🔌 Cannot connect to backend. Run:\n```\npython backend.py\n```")
                    except requests.exceptions.Timeout:
                        progress_placeholder.empty()
                        st.error("⏱️ Request timed out. Try a smaller model or disable web search.")
                    except Exception as e:
                        progress_placeholder.empty()
                        st.error(f"❌ Unexpected error: {str(e)}")
            else:
                st.warning("⚕️ Please describe or select at least one symptom to begin analysis.")
        else:
            st.markdown("""
            <div style="text-align:center;padding:3rem 2rem;color:#2a3f5a">
                <div style="font-size:4rem;margin-bottom:1rem;opacity:.4">🩺</div>
                <div style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:#1e3a5f;margin-bottom:.5rem">Awaiting Patient Data</div>
                <div style="font-size:.85rem;color:#1e3a5f;opacity:.7">
                    Complete the intake form and click<br><strong>Run Clinical Analysis</strong><br>to receive a full diagnostic assessment
                </div>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: CHAT
# ─────────────────────────────────────────────────────────────────────────────
with tab_chat:
    st.markdown("### 💬 Follow-up Medical Consultation")
    st.caption("Ask follow-up questions, clarify diagnosis details, or inquire about medications.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    chat_input = st.text_area("Your Question:",
        placeholder="e.g., What are the side effects of ibuprofen? Can I take it with my current medications?",
        height=100, key="chat_input_area")

    col_send, col_clear = st.columns([3, 1])
    with col_send:
        send_btn = st.button("📤 Send Message", type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    if send_btn and chat_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": chat_input.strip()})
        with st.spinner("🤔 Dr. MedAssist is consulting..."):
            try:
                payload = {
                    "model_name":     selected_model,
                    "model_provider": provider,
                    "messages":       [m["content"] for m in st.session_state.chat_history if m["role"] == "user"],
                    "allow_search":   allow_web_search,
                    "patient_info":   None,  # FIX 5: was {}
                }
                response = requests.post(f"{API_URL}/chat", json=payload, timeout=120)
                if response.status_code == 200:
                    ai_response = response.json().get("response", "No response received.")
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                else:
                    st.error(f"Error {response.status_code}: {response.json().get('detail','Unknown error')}")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")

    if st.session_state.chat_history:
        st.divider()
        for msg in reversed(st.session_state.chat_history):
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="background:rgba(0,150,255,.08);border:1px solid rgba(0,150,255,.15);
                     border-radius:12px;padding:.9rem 1.1rem;margin:.5rem 0;font-size:.9rem;color:#b0c4d8">
                    <strong style="color:#4db8ff;font-size:.75rem;text-transform:uppercase;letter-spacing:.1em">You</strong><br><br>
                    {msg['content']}
                </div>""", unsafe_allow_html=True)
            else:
                with st.container():
                    st.markdown("**🩺 Dr. MedAssist AI**")
                    st.markdown(msg["content"])
                    st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: PATIENT MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────
with tab_patients:
    st.markdown("### 👤 Patient Management")
    st.caption("Register patients and view their consultation history.")

    pt_action = st.radio("Action:", ["➕ Register New Patient", "📋 View All Patients", "🔍 Search Patient"], horizontal=True)

    if "➕" in pt_action:
        st.markdown("#### Register New Patient")
        with st.form("register_patient_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                first_name    = st.text_input("First Name *", placeholder="John")
                email_pt      = st.text_input("Email", placeholder="john@example.com")
                age_pt        = st.number_input("Age", min_value=0, max_value=120, value=None, step=1)
                weight_pt     = st.number_input("Weight (kg)", min_value=0.0, max_value=500.0, value=None, step=0.5)
                blood_type_pt = st.selectbox("Blood Type", ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"])
                smoking_pt    = st.selectbox("Smoking Status", ["", "Non-smoker", "Ex-smoker", "Light smoker", "Heavy smoker"])
            with col2:
                last_name     = st.text_input("Last Name *", placeholder="Doe")
                phone_pt      = st.text_input("Phone", placeholder="+91 98765 43210")
                gender_pt     = st.selectbox("Gender", ["", "Male", "Female", "Other"])
                height_pt     = st.number_input("Height (cm)", min_value=0.0, max_value=300.0, value=None, step=0.5)
                dob_pt        = st.text_input("Date of Birth (YYYY-MM-DD)", placeholder="1990-01-15")
                alcohol_pt    = st.selectbox("Alcohol Use", ["", "None", "Occasional", "Moderate", "Heavy"])

            med_hist_pt   = st.text_area("Medical History / Chronic Conditions", placeholder="e.g., Diabetes, Hypertension...", height=70)
            curr_meds_pt  = st.text_area("Current Medications", placeholder="e.g., Metformin 500mg...", height=70)
            allergies_f   = st.text_area("⚠️ Known Allergies", placeholder="e.g., Penicillin, NSAIDs...", height=60)
            fam_hist_pt   = st.text_area("Family History", placeholder="e.g., Father — Heart disease...", height=60)

            submitted = st.form_submit_button("✅ Register Patient", type="primary", use_container_width=True)
            if submitted:
                if not first_name.strip() or not last_name.strip():
                    st.error("⚠️ First Name and Last Name are required.")
                else:
                    payload = {"first_name": first_name.strip(), "last_name": last_name.strip()}
                    if email_pt:      payload["email"]               = email_pt
                    if phone_pt:      payload["phone"]               = phone_pt
                    if age_pt:        payload["age"]                 = age_pt
                    if gender_pt:     payload["gender"]              = gender_pt
                    if weight_pt:     payload["weight"]              = weight_pt
                    if height_pt:     payload["height"]              = height_pt
                    if blood_type_pt: payload["blood_type"]          = blood_type_pt
                    if dob_pt:        payload["date_of_birth"]       = dob_pt
                    if smoking_pt:    payload["smoking_status"]      = smoking_pt
                    if alcohol_pt:    payload["alcohol_use"]         = alcohol_pt
                    if med_hist_pt:   payload["medical_history"]     = med_hist_pt
                    if curr_meds_pt:  payload["current_medications"] = curr_meds_pt
                    if allergies_f:   payload["allergies"]           = allergies_f
                    if fam_hist_pt:   payload["family_history"]      = fam_hist_pt
                    try:
                        resp = requests.post(f"{API_URL}/patients", json=payload, timeout=10)
                        if resp.status_code == 201:
                            pt = resp.json()["patient"]
                            st.success(f"✅ Patient registered! ID: **#{pt['id']}** — {pt['first_name']} {pt['last_name']}")
                            st.info("💡 Select this patient in the sidebar, then run a diagnosis to save it to the database.")
                        else:
                            st.error(f"❌ Error: {resp.json().get('detail','Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")

    elif "📋" in pt_action:
        st.markdown("#### All Registered Patients")
        if st.button("🔄 Refresh List"):
            st.rerun()
        try:
            resp = requests.get(f"{API_URL}/patients", timeout=10)
            if resp.status_code == 200:
                data     = resp.json()
                patients = data.get("patients", [])
                st.markdown(f"**Total: {data.get('total', 0)} patient(s)**")
                if not patients:
                    st.info("No patients registered yet.")
                else:
                    for p in patients:
                        bmi_txt = f" · BMI {p['bmi']} ({p['bmi_category']})" if p.get("bmi") else ""
                        with st.expander(
                            f"#{p['id']} — {p['first_name']} {p['last_name']} | "
                            f"Age: {p.get('age','—')} | {p.get('gender','—')}{bmi_txt} | "
                            f"Consultations: {p.get('total_consultations',0)}"
                        ):
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown(f"**Email:** {p.get('email') or '—'}")
                                st.markdown(f"**Phone:** {p.get('phone') or '—'}")
                                st.markdown(f"**DOB:** {p.get('date_of_birth') or '—'}")
                                st.markdown(f"**Blood Type:** {p.get('blood_type') or '—'}")
                                st.markdown(f"**Weight:** {str(p.get('weight') or '—')} kg")
                                st.markdown(f"**Height:** {str(p.get('height') or '—')} cm")
                            with c2:
                                st.markdown(f"**Medical History:** {p.get('medical_history') or '—'}")
                                st.markdown(f"**Medications:** {p.get('current_medications') or '—'}")
                                st.markdown(f"**Allergies:** {p.get('allergies') or '—'}")
                                st.markdown(f"**Family History:** {p.get('family_history') or '—'}")
                                st.markdown(f"**Smoking:** {p.get('smoking_status') or '—'}")
                                st.markdown(f"**Alcohol:** {p.get('alcohol_use') or '—'}")

                            st.markdown("---")
                            b1, b2 = st.columns([3, 1])
                            with b1:
                                if st.button(f"📂 Load Consultations", key=f"c_{p['id']}"):
                                    cr = requests.get(f"{API_URL}/patients/{p['id']}/consultations", timeout=10)
                                    if cr.status_code == 200:
                                        cdata = cr.json()
                                        cons  = cdata.get("consultations", [])
                                        if not cons:
                                            st.info("No consultations yet for this patient.")
                                        else:
                                            st.markdown(f"**{cdata.get('total_consultations',0)} consultation(s):**")
                                            for c in cons:
                                                syms = c.get("symptoms", [])
                                                sym_names = [s.get("symptom_name", s) if isinstance(s, dict) else s for s in syms]
                                                st.markdown(
                                                    f"**#{c['id']}** — {(c.get('consultation_date') or '')[:10]} "
                                                    f"| Severity: {c.get('severity','—')} "
                                                    f"| Duration: {c.get('duration_of_symptoms','—')} "
                                                    f"| Model: {c.get('model_used','—')}"
                                                )
                                                if sym_names:
                                                    st.markdown(f"**Symptoms:** {', '.join(sym_names)}")
                                                with st.expander(f"📋 Full Diagnosis — #{c['id']}"):
                                                    st.markdown(c.get("ai_diagnosis") or "No diagnosis recorded.")
                            with b2:
                                if st.button(f"🗑️ Deactivate", key=f"d_{p['id']}", type="secondary"):
                                    dr = requests.delete(f"{API_URL}/patients/{p['id']}", timeout=10)
                                    if dr.status_code == 200:
                                        st.warning(f"Patient #{p['id']} deactivated.")
                                        st.rerun()
                                    else:
                                        st.error("Failed to deactivate.")
            else:
                st.error(f"❌ Could not load patients: {resp.status_code}")
        except Exception as e:
            st.error(f"❌ Connection error: {e}")

    elif "🔍" in pt_action:
        st.markdown("#### Search Patient")
        q = st.text_input("Search by name, email, or phone:", placeholder="e.g., John or john@example.com")
        if q.strip():
            try:
                resp = requests.get(f"{API_URL}/patients/search", params={"q": q}, timeout=10)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if not results:
                        st.info("No patients found.")
                    else:
                        st.markdown(f"Found **{len(results)}** result(s):")
                        for p in results:
                            st.markdown(
                                f"**#{p['id']} — {p['first_name']} {p['last_name']}**"
                                f" | Email: {p.get('email') or '—'}"
                                f" | Phone: {p.get('phone') or '—'}"
                                f" | Age: {p.get('age') or '—'}"
                                f" | Consultations: {p.get('total_consultations',0)}"
                            )
                else:
                    st.error(f"Search error: {resp.status_code}")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# ─── Emergency Info ───────────────────────────────────────────────────────────
st.markdown("""
<div class="alert-emergency">
    <h4>🚨 Seek Immediate Emergency Care If You Experience:</h4>
    <ul>
        <li>Chest pain, pressure, or tightness · Suspected heart attack or stroke</li>
        <li>Sudden difficulty breathing or shortness of breath at rest</li>
        <li>Severe headache with neck stiffness, fever, and photophobia (possible meningitis)</li>
        <li>Facial drooping, arm weakness, speech difficulty (FAST stroke signs)</li>
        <li>Severe allergic reaction: throat swelling, difficulty swallowing</li>
        <li>Uncontrolled bleeding · Loss of consciousness · Suspected poisoning</li>
        <li>Blood in vomit, urine, or stool with dizziness</li>
    </ul>
    <strong>🆘 Emergency: Call 112 (India) · 911 (US) · 999 (UK) · or your local emergency number</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;padding:1.5rem 0 .5rem;color:#2a3f5a;font-size:.8rem;letter-spacing:.03em">
    Dr. MedAssist AI v4.0 &nbsp;·&nbsp; Built with LangGraph &amp; Streamlit &nbsp;·&nbsp;
    Powered by Groq &amp; OpenAI LLMs &nbsp;·&nbsp;
    <em style="color:#1e3a5f">Educational purposes only — not a substitute for professional medical advice</em>
</div>
""", unsafe_allow_html=True)
