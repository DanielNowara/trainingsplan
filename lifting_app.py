import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
import math

st.set_page_config(page_title="ProLifting Coach OS", layout="wide", page_icon="🏋️‍♂️")

# ==========================================
# 1. DATENBANK & SPEICHER-LOGIK
# ==========================================
DATA_FILE = "athletes.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

db = load_data()

# ==========================================
# 2. KATALOGE & LOGIK
# ==========================================
EXERCISE_CATALOG = {
    "Reißen": ["Snatch", "Power Snatch", "Hang Snatch", "Snatch Balance", "Muscle Snatch", "Block Snatch"],
    "Stoßen": ["Clean & Jerk", "Power Clean", "Split Jerk", "Power Jerk", "Hang Clean", "Clean Pull"],
    "Beugen": ["Back Squat", "Front Squat", "Pause Squat", "Box Squat", "Overhead Squat"],
    "Zubehör": ["Snatch Pull", "Clean Pull", "Push Press", "Strict Press", "Plank", "Hyperextensions"]
}
ALL_EXERCISES = [ex for sublist in EXERCISE_CATALOG.values() for ex in sublist]

INJURY_SWAPS = {
    "Knie": {"Back Squat": "Box Squat", "Front Squat": "Pause Squat", "Clean & Jerk": "Power Clean & Power Jerk"},
    "Schulter": {"Snatch": "Clean Pull", "Push Press": "Strict Press", "Split Jerk": "Jerk Drives"},
    "Unterer Rücken": {"Back Squat": "Front Squat", "Snatch Pull": "Hang Snatch Pull", "Deadlift": "Hyperextensions"}
}

MOBILITY_DRILLS = {
    "Knie": "Couch Stretch (2 Min/Seite), Banded TKEs (3x15).",
    "Schulter": "Banded Face Pulls (3x15), Thoracic Extensions auf der Rolle.",
    "Unterer Rücken": "Cat-Cow (20x), 90/90 Hip Stretch, Bird-Dog."
}

def calc_sinclair(total, bw, gender):
    if gender == "Männlich":
        A, B = 0.7519, 175.5
    else:
        A, B = 0.7834, 153.6
    if bw > B: return total
    res = 10 ** (A * (math.log10(bw / B) ** 2))
    return round(total * res, 2)

def calculate_plates(weight, bar_weight=20):
    available_plates = [25, 20, 15, 10, 5, 2.5, 1.25, 0.5]
    if weight < bar_weight: return "Stange leer"
    weight_per_side = (weight - bar_weight) / 2
    plates_to_load = []
    for plate in available_plates:
        while weight_per_side >= plate:
            plates_to_load.append(str(plate))
            weight_per_side = round(weight_per_side - plate, 2)
    return " + ".join(plates_to_load) if plates_to_load else "Stange leer"

# ==========================================
# 3. SIDEBAR: SPORTLER MANAGEMENT
# ==========================================
st.sidebar.title("🏋️‍♂️ ProLifting OS")
athlete_names = list(db.keys())
selected_athlete = st.sidebar.selectbox("Sportler wählen", ["-- Neuer Sportler --"] + athlete_names)

if selected_athlete == "-- Neuer Sportler --":
    st.sidebar.subheader("Neuen Sportler anlegen")
    new_name = st.sidebar.text_input("Name")
    new_gender = st.sidebar.radio("Geschlecht", ["Männlich", "Weiblich"])
    new_bw = st.sidebar.number_input("Körpergewicht (kg)", 40.0, 150.0, 80.0)
    new_snatch = st.sidebar.number_input("Snatch 1RM", 20, 250, 80)
    new_cj = st.sidebar.number_input("Clean & Jerk 1RM", 20, 300, 100)
    new_squat = st.sidebar.number_input("Back Squat 1RM", 20, 400, 120)
    if st.sidebar.button("Sportler Speichern"):
        if new_name:
            db[new_name] = {"gender": new_gender, "bw": new_bw, "snatch": new_snatch, "cj": new_cj, "squat": new_squat}
            save_data(db)
            st.sidebar.success(f"{new_name} gespeichert! Seite wird neu geladen...")
            st.rerun()
else:
    athlete_data = db[selected_athlete]
    st.sidebar.success(f"Eingeloggt: {selected_athlete}")
    with st.sidebar.expander("Profil / 1RM Update"):
        bw = st.number_input("Gewicht", value=float(athlete_data["bw"]))
        s_rm = st.number_input("Snatch", value=int(athlete_data["snatch"]))
        c_rm = st.number_input("C&J", value=int(athlete_data["cj"]))
        sq_rm = st.number_input("Squat", value=int(athlete_data["squat"]))
        if st.button("Update"):
            db[selected_athlete].update({"bw": bw, "snatch": s_rm, "cj": c_rm, "squat": sq_rm})
            save_data(db)
            st.rerun()

# ==========================================
# 4. HAUPT-APP
# ==========================================
if selected_athlete != "-- Neuer Sportler --":
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Readiness", "📝 Trainingsplan", "⏱️ Workout", "🏆 Tools"])

    with tab1:
        st.header(f"Status: {selected_athlete}")
        col1, col2 = st.columns(2)
        with col1:
            sleep = st.slider("Schlafqualität", 1, 10, 7)
            stress = st.slider("Stress (1-10)", 1, 10, 4)
            soreness = st.slider("Muskelkater (1-10)", 1, 10, 3)
            readiness_score = sleep - (stress * 0.5) - (soreness * 0.5)
            readiness_mod = 1.02 if readiness_score >= 5 else (0.90 if readiness_score < 1 else 1.0)
            st.metric("Readiness Faktor", f"{int(readiness_mod*100)}%")
        with col2:
            injuries = st.multiselect("Beschwerden?", ["Knie", "Schulter", "Unterer Rücken"])
            for inj in injuries: st.warning(f"Fokus {inj}: {MOBILITY_DRILLS[inj]}")

    with tab2:
        st.header("Plan Generator")
        c1, c2, c3 = st.columns(3)
        prep_weeks = c1.slider("Wochen", 4, 16, 8)
        current_week = c2.slider("Woche", 1, prep_weeks, 1)
        days_per_week = c3.selectbox("Tage/Woche", [3, 4, 5, 6], index=1)

        if current_week <= prep_weeks // 3: phase, base_int = "Hypertrophie", 0.72
        elif current_week <= (2 * prep_weeks) // 3: phase, base_int = "Kraft", 0.82
        else: phase, base_int = "Peaking", 0.92
        
        final_int = base_int * readiness_mod
        weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"][:days_per_week]
        
        for day in weekdays:
            with st.expander(f"📅 {day} konfigurieren", expanded=True):
                num_ex = st.slider(f"Übungen {day}", 1, 6, 3, key=f"n_{day}")
                day_data = []
                for i in range(num_ex):
                    # Sinnvolle Vorauswahl
                    d_idx = 0 if i == 0 else (2 if i == 1 else 3)
                    ex_choice = st.selectbox(f"Übung {i+1}", ALL_EXERCISES, index=d_idx, key=f"s_{day}_{i}")
                    # Injury Swap
                    for inj in injuries:
                        if ex_choice in INJURY_SWAPS[inj]: ex_choice = INJURY_SWAPS[inj][ex_choice]
                    
                    rm_ref = athlete_data["squat"] if "Squat" in ex_choice or "Press" in ex_choice else (athlete_data["snatch"] if "Snatch" in ex_choice else athlete_data["cj"])
                    calc_w = round(rm_ref * final_int, 1)
                    day_data.append({"Übung": ex_choice, "Last": f"{calc_w} kg", "Plates": calculate_plates(calc_w)})
                st.table(pd.DataFrame(day_data))

    with tab3:
        components.html("""
        <div style="background:#1e1e1e; padding:15px; border-radius:10px; color:white; text-align:center;">
            <h3>Pausen-Timer</h3><h1 id="t">02:00</h1>
            <button onclick="s(120)" style="background:#4CAF50; color:white; border:none; padding:10px;">2 Min</button>
            <button onclick="s(180)" style="background:#2196F3; color:white; border:none; padding:10px;">3 Min</button>
            <script>var i; function s(d){clearInterval(i); var t=d,m,s; i=setInterval(function(){m=parseInt(t/60,10);s=parseInt(t%60,10);document.getElementById('t').textContent=(m<10?"0"+m:m)+":"+(s<10?"0"+s:s);if(--t<0)clearInterval(i);},1000);}</script>
        </div>""", height=180)
        st.checkbox("Training gestartet")

    with tab4:
        st.subheader("Plate Calculator")
        tw = st.number_input("Gewicht (kg)", 20.0, 300.0, 100.0, step=2.5)
        st.success(f"Pro Seite: {calculate_plates(tw)}")
        sinclair = calc_sinclair(athlete_data["snatch"] + athlete_data["cj"], athlete_data["bw"], athlete_data["gender"])
        st.metric("Sinclair Score", sinclair)
else:
    st.info("Bitte links einen Sportler anlegen oder wählen.")