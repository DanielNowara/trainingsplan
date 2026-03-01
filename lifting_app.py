import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
import datetime

st.set_page_config(page_title="ProLifting Coach OS", layout="wide", page_icon="🏋️‍♂️")

# ==========================================
# 1. DATENBANK & SPEICHER-LOGIK
# ==========================================
DATA_FILE = "athletes.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

db = load_data()

# ==========================================
# 2. ÜBUNGEN & WISSENSCHAFTLICHE MUSTERPLÄNE
# ==========================================
EXERCISE_CATALOG = {
    "Reißen (Snatch)": ["Snatch", "Power Snatch", "Hang Snatch", "Snatch Balance", "Block Snatch", "Deficit Snatch"],
    "Stoßen (Clean & Jerk)": ["Clean & Jerk", "Power Clean", "Split Jerk", "Power Jerk", "Hang Clean", "Block Clean"],
    "Beugen (Squats)": ["Back Squat", "Front Squat", "Pause Squat", "Overhead Squat"],
    "Zug (Pulls)": ["Snatch Pull", "Clean Pull", "Snatch Deadlift", "Clean Deadlift"],
    "Zubehör (Accessory)": ["Push Press", "Strict Press", "Plank", "Hyperextensions", "GHD Raises", "Pull-ups", "Dips"]
}
ALL_EXERCISES = [ex for sublist in EXERCISE_CATALOG.values() for ex in sublist]

# Wissenschaftlich fundierte Templates (Undulating Periodization)
RECOMMENDED_TEMPLATES = {
    2: {"Tag 1 (Schwer)": ["Snatch", "Back Squat", "Snatch Pull", "Plank"], 
        "Tag 2 (Schwer)": ["Clean & Jerk", "Front Squat", "Clean Pull", "Push Press"]},
    
    3: {"Tag 1 (Fokus Snatch/Squat)": ["Snatch", "Back Squat", "Snatch Pull", "Hyperextensions"], 
        "Tag 2 (Leicht/Speed)": ["Power Clean", "Power Jerk", "Front Squat (Leicht)", "Plank"], 
        "Tag 3 (Fokus C&J/Max)": ["Clean & Jerk", "Front Squat", "Clean Pull", "Push Press"]},
    
    4: {"Tag 1 (Schwer Beugen)": ["Back Squat", "Snatch", "Snatch Pull", "Plank"], 
        "Tag 2 (Schwer Heben)": ["Clean & Jerk", "Clean Pull", "Push Press", "GHD Raises"], 
        "Tag 3 (Erholung/Power)": ["Power Snatch", "Power Clean", "Overhead Squat", "Pull-ups"], 
        "Tag 4 (Wettkampf-Simulation)": ["Snatch", "Clean & Jerk", "Front Squat", "Hyperextensions"]},
    
    5: {"Tag 1 (Fokus Snatch)": ["Snatch", "Back Squat", "Snatch Pull", "Plank"], 
        "Tag 2 (Fokus C&J)": ["Clean & Jerk", "Clean Pull", "Strict Press", "Dips"], 
        "Tag 3 (Erholung/Power)": ["Power Snatch", "Power Clean", "Push Press", "Pull-ups"], 
        "Tag 4 (Schwer Beugen)": ["Front Squat", "Snatch Balance", "Snatch Pull", "GHD Raises"], 
        "Tag 5 (Max Out Tag)": ["Snatch", "Clean & Jerk", "Back Squat", "Hyperextensions"]},
    
    6: {"Tag 1 (Volumen)": ["Back Squat", "Snatch", "Snatch Pull", "Plank"], 
        "Tag 2 (Technik C&J)": ["Clean & Jerk", "Front Squat", "Clean Pull", "GHD Raises"], 
        "Tag 3 (Leicht/Power)": ["Power Snatch", "Push Press", "Overhead Squat", "Pull-ups"], 
        "Tag 4 (Schwer Beugen)": ["Front Squat", "Power Clean", "Strict Press", "Plank"], 
        "Tag 5 (Technik Snatch)": ["Hang Snatch", "Hang Clean", "Snatch Pull", "Dips"], 
        "Tag 6 (Max Out Tag)": ["Snatch", "Clean & Jerk", "Back Squat", "Hyperextensions"]}
}

def get_rm_for_exercise(ex_choice, athlete_data):
    if "Front Squat" in ex_choice: return athlete_data.get("front_squat", athlete_data["squat"] * 0.85)
    if "Squat" in ex_choice: return athlete_data["squat"]
    if "Push Press" in ex_choice or "Strict Press" in ex_choice or "Jerk" in ex_choice: return athlete_data.get("push_press", athlete_data["cj"] * 0.8)
    if "Snatch" in ex_choice: return athlete_data["snatch"]
    return athlete_data["cj"]

def get_progressive_sets(phase, ex_name, rm):
    """Generiert aufsteigende Sätze im Format Gewicht/Wdh/Sätze"""
    if ex_name in EXERCISE_CATALOG["Zubehör (Accessory)"]:
        return "3 Sätze x 8-12 Wdh @ RPE 8"

    # Ist es eine "Leichte" Variante?
    mod = 0.85 if "(Leicht)" in ex_name else 1.0
    rm = rm * mod

    if "Aufbauphase" in phase:
        w1, w2, w3 = round(rm*0.65), round(rm*0.70), round(rm*0.75)
        return f"{w1}kg/5/1 , {w2}kg/4/1 , {w3}kg/4/2"
    elif "Kraft" in phase:
        w1, w2, w3 = round(rm*0.75), round(rm*0.80), round(rm*0.85)
        return f"{w1}kg/3/1 , {w2}kg/3/1 , {w3}kg/2/3"
    else: # Peaking
        w1, w2, w3 = round(rm*0.80), round(rm*0.85), round(rm*0.90)
        return f"{w1}kg/2/1 , {w2}kg/1/1 , {w3}kg/1/2"

# ==========================================
# 3. SIDEBAR & PROFIL
# ==========================================
st.sidebar.title("🏋️‍♂️ ProLifting OS")
athlete_names = list(db.keys())
selected_athlete = st.sidebar.selectbox("Sportler wählen", ["-- Neuer Sportler --"] + athlete_names)

if selected_athlete == "-- Neuer Sportler --":
    st.sidebar.subheader("Neuen Sportler anlegen")
    new_name = st.sidebar.text_input("Name")
    new_gender = st.sidebar.radio("Geschlecht", ["Männlich", "Weiblich"])
    new_bw = st.sidebar.number_input("Körpergewicht (kg)", 40.0, 150.0, 80.0)
    
    st.sidebar.markdown("**Aktuelle Bestwerte (1RM)**")
    new_snatch = st.sidebar.number_input("Snatch", 20, 250, 80)
    new_cj = st.sidebar.number_input("Clean & Jerk", 20, 300, 100)
    new_squat = st.sidebar.number_input("Back Squat", 20, 400, 120)
    new_fsquat = st.sidebar.number_input("Front Squat", 20, 350, 105)
    new_ppress = st.sidebar.number_input("Push Press", 20, 200, 80)
    
    if st.sidebar.button("Sportler Speichern"):
        if new_name:
            db[new_name] = {
                "gender": new_gender, "bw": new_bw, 
                "snatch": new_snatch, "cj": new_cj, 
                "squat": new_squat, "front_squat": new_fsquat, "push_press": new_ppress,
                "saved_plans": {}, "logbook": []
            }
            save_data(db)
            st.sidebar.success(f"{new_name} gespeichert! Seite neu laden...")
            st.rerun()
else:
    athlete_data = db[selected_athlete]
    athlete_data.setdefault("logbook", []) # Fallback für alte Profile
        
    st.sidebar.success(f"Eingeloggt: {selected_athlete}")
    with st.sidebar.expander("Profil anpassen"):
        bw = st.number_input("Gewicht", value=float(athlete_data["bw"]))
        s_rm = st.number_input("Snatch", value=int(athlete_data["snatch"]))
        c_rm = st.number_input("C&J", value=int(athlete_data["cj"]))
        sq_rm = st.number_input("Back Squat", value=int(athlete_data["squat"]))
        fsq_rm = st.number_input("Front Squat", value=int(athlete_data.get("front_squat", sq_rm*0.85)))
        pp_rm = st.number_input("Push Press", value=int(athlete_data.get("push_press", c_rm*0.8)))
        
        if st.button("Werte Update"):
            db[selected_athlete].update({
                "bw": bw, "snatch": s_rm, "cj": c_rm, "squat": sq_rm, 
                "front_squat": fsq_rm, "push_press": pp_rm
            })
            save_data(db)
            st.rerun()

# ==========================================
# 4. HAUPT-APP
# ==========================================
if selected_athlete != "-- Neuer Sportler --":
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Trainingsplan", "📖 Logbuch & History", "📊 Readiness", "⏱️ Tools"])

    # --- TAB 1: TRAININGSPLAN GENERATOR ---
    with tab1:
        st.header("Plan Generator (Wave Loading)")
        
        c1, c2 = st.columns(2)
        prep_weeks = c1.slider("Vorbereitung gesamt (Wochen)", 4, 16, 8)
        current_week = c2.slider("Aktuelle Woche", 1, prep_weeks, 1)
        
        if current_week <= prep_weeks // 3: phase = "Aufbauphase (Volumen, Hypertrophie)"
        elif current_week <= (2 * prep_weeks) // 3: phase = "Kraft-Phase (Schwere Pulls & Beugen)"
        else: phase = "Peaking (Wettkampfvorbereitung)"
            
        st.success(f"**Aktuelle Phase:** {phase} | Steigende Intensität innerhalb der Übung")

        plan_mode = st.radio("Erstellungsmethode:", ["Wissenschaftlicher Musterplan", "Gespeicherten Plan laden"], horizontal=True)

        current_plan_structure = {}

        if plan_mode == "Wissenschaftlicher Musterplan":
            days_per_week = st.selectbox("Trainingstage/Woche", [2, 3, 4, 5, 6], index=2)
            current_plan_structure = RECOMMENDED_TEMPLATES[days_per_week]
        else:
            saved_plans = list(athlete_data.get("saved_plans", {}).keys())
            if not saved_plans: st.warning("Du hast noch keine Pläne gespeichert.")
            else: current_plan_structure = athlete_data["saved_plans"][st.selectbox("Wähle einen Plan", saved_plans)]

        st.divider()
        
        for day, exercises in current_plan_structure.items():
            with st.expander(f"📅 {day}", expanded=True):
                day_data = []
                for ex_choice in exercises:
                    # RM holen & Progression berechnen
                    rm_ref = get_rm_for_exercise(ex_choice, athlete_data)
                    progression_string = get_progressive_sets(phase, ex_choice, rm_ref)
                    
                    day_data.append({"Übung": ex_choice, "Progression (Gewicht / Wdh / Sätze)": progression_string})
                
                st.table(pd.DataFrame(day_data))

    # --- TAB 2: LOGBUCH & HISTORY ---
    with tab2:
        st.header("📖 Trainings-Logbuch")
        st.write("Trage hier ein, was du heute im Gym tatsächlich bewegt hast.")
        
        with st.form("log_form"):
            col1, col2, col3 = st.columns(3)
            log_date = col1.date_input("Datum", datetime.date.today())
            log_ex = col2.selectbox("Übung", ALL_EXERCISES)
            log_result = col3.text_input("Geschafft (z.B. 100/3/2)", placeholder="Gewicht / Wdh / Sätze")
            log_notes = st.text_input("Notizen (Tagesform, Technik...)", placeholder="Fühlte sich schwer an im Lockout...")
            
            if st.form_submit_button("Ins Logbuch eintragen"):
                if log_result:
                    new_entry = {
                        "Datum": str(log_date), "Übung": log_ex, 
                        "Leistung": log_result, "Notiz": log_notes
                    }
                    athlete_data["logbook"].append(new_entry)
                    db[selected_athlete] = athlete_data
                    save_data(db)
                    st.success("Erfolgreich gespeichert!")
                    st.rerun()
                else:
                    st.error("Bitte eine Leistung eintragen.")
                    
        st.divider()
        st.subheader("Deine letzten Einheiten")
        if athlete_data["logbook"]:
            # DataFrame umdrehen, damit das Neueste oben steht
            df_log = pd.DataFrame(athlete_data["logbook"]).iloc[::-1]
            st.dataframe(df_log, use_container_width=True)
        else:
            st.info("Noch keine Einträge vorhanden.")

    # --- TAB 3: READINESS ---
    with tab3:
        st.header("Tagesform")
        st.info("Check-in für deine tägliche Readiness.")
        sleep = st.slider("Schlafqualität", 1, 10, 7)
        stress = st.slider("Stress (1-10)", 1, 10, 4)
        soreness = st.slider("Muskelkater (1-10)", 1, 10, 3)

    # --- TAB 4: TOOLS ---
    with tab4:
        components.html("""
        <div style="background:#1e1e1e; padding:15px; border-radius:10px; color:white; text-align:center;">
            <h3>Pausen-Timer</h3><h1 id="t">02:00</h1>
            <button onclick="s(90)" style="background:#FF9800; color:white; border:none; padding:10px; border-radius:5px;">1.5 Min</button>
            <button onclick="s(120)" style="background:#4CAF50; color:white; border:none; padding:10px; border-radius:5px;">2 Min</button>
            <button onclick="s(180)" style="background:#2196F3; color:white; border:none; padding:10px; border-radius:5px;">3 Min</button>
            <script>var i; function s(d){clearInterval(i); var t=d,m,s; i=setInterval(function(){m=parseInt(t/60,10);s=parseInt(t%60,10);document.getElementById('t').textContent=(m<10?"0"+m:m)+":"+(s<10?"0"+s:s);if(--t<0)clearInterval(i);},1000);}</script>
        </div>""", height=200)

else:
    st.info("Bitte links einen Sportler anlegen oder wählen.")
