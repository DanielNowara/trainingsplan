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
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

db = load_data()

# ==========================================
# 2. KATALOGE, LOGIK & MUSTERPLÄNE
# ==========================================
EXERCISE_CATALOG = {
    "Reißen (Snatch)": ["Snatch", "Power Snatch", "Hang Snatch", "Snatch Balance", "Muscle Snatch", "Block Snatch", "Tall Snatch", "Deficit Snatch"],
    "Stoßen (Clean & Jerk)": ["Clean & Jerk", "Power Clean", "Split Jerk", "Power Jerk", "Hang Clean", "Block Clean", "Jerk from Rack"],
    "Beugen (Squats)": ["Back Squat", "Front Squat", "Pause Squat", "Box Squat", "Overhead Squat", "Bulgarian Split Squats"],
    "Zug (Pulls)": ["Snatch Pull", "Clean Pull", "Snatch Deadlift", "Clean Deadlift", "Deficit Pulls", "Hang Pulls"],
    "Zubehör (Accessory)": ["Push Press", "Strict Press", "Plank", "Hyperextensions", "GHD Raises", "Pendlay Rows", "Pull-ups", "Dips", "Core-Rotation"]
}
ALL_EXERCISES = [ex for sublist in EXERCISE_CATALOG.values() for ex in sublist]

INJURY_SWAPS = {
    "Knie": {"Back Squat": "Box Squat", "Front Squat": "Pause Squat", "Clean & Jerk": "Power Clean & Power Jerk"},
    "Schulter": {"Snatch": "Clean Pull", "Push Press": "Strict Press", "Split Jerk": "Jerk Drives"},
    "Unterer Rücken": {"Back Squat": "Front Squat", "Snatch Pull": "Hang Snatch Pull", "Snatch Deadlift": "Hyperextensions"}
}

MOBILITY_DRILLS = {
    "Knie": "Couch Stretch (2 Min/Seite), Banded TKEs (3x15).",
    "Schulter": "Banded Face Pulls (3x15), Thoracic Extensions auf der Rolle.",
    "Unterer Rücken": "Cat-Cow (20x), 90/90 Hip Stretch, Bird-Dog."
}

# Musterpläne (Immer 3-4 Übungen pro Tag)
RECOMMENDED_TEMPLATES = {
    2: {"Tag 1": ["Snatch", "Back Squat", "Snatch Pull", "Plank"], 
        "Tag 2": ["Clean & Jerk", "Front Squat", "Clean Pull", "Push Press"]},
    
    3: {"Tag 1": ["Snatch", "Back Squat", "Snatch Pull", "Hyperextensions"], 
        "Tag 2": ["Power Clean", "Power Jerk", "Front Squat", "Plank"], 
        "Tag 3": ["Clean & Jerk", "Overhead Squat", "Clean Pull", "Push Press"]},
    
    4: {"Tag 1": ["Snatch", "Back Squat", "Snatch Pull", "Plank"], 
        "Tag 2": ["Clean & Jerk", "Front Squat", "Clean Pull", "GHD Raises"], 
        "Tag 3": ["Power Snatch", "Power Clean", "Push Press", "Pull-ups"], 
        "Tag 4": ["Snatch", "Clean & Jerk", "Back Squat", "Hyperextensions"]},
    
    5: {"Tag 1": ["Snatch", "Back Squat", "Snatch Pull", "Plank"], 
        "Tag 2": ["Clean & Jerk", "Front Squat", "Clean Pull", "Dips"], 
        "Tag 3": ["Power Snatch", "Push Press", "Overhead Squat", "Pull-ups"], 
        "Tag 4": ["Power Clean", "Front Squat", "Strict Press", "GHD Raises"], 
        "Tag 5": ["Snatch", "Clean & Jerk", "Back Squat", "Hyperextensions"]},
    
    6: {"Tag 1": ["Snatch", "Back Squat", "Snatch Pull", "Plank"], 
        "Tag 2": ["Clean & Jerk", "Front Squat", "Clean Pull", "GHD Raises"], 
        "Tag 3": ["Power Snatch", "Push Press", "Overhead Squat", "Pull-ups"], 
        "Tag 4": ["Power Clean", "Front Squat", "Strict Press", "Core-Rotation"], 
        "Tag 5": ["Hang Snatch", "Hang Clean", "Snatch Pull", "Dips"], 
        "Tag 6": ["Snatch", "Clean & Jerk", "Back Squat", "Hyperextensions"]}
}

def get_sets_reps(phase, ex_name):
    is_tech = ex_name in EXERCISE_CATALOG["Reißen (Snatch)"] or ex_name in EXERCISE_CATALOG["Stoßen (Clean & Jerk)"]
    is_strength = ex_name in EXERCISE_CATALOG["Beugen (Squats)"] or ex_name in EXERCISE_CATALOG["Zug (Pulls)"]
    
    if "Aufbauphase" in phase:
        if is_tech: return "4 x 4-5" # Im Aufbau auch Technik mit etwas mehr Wdh
        if is_strength: return "4 x 6-8"
        return "3 x 10-12"
    elif "Kraft" in phase:
        if is_tech: return "5 x 2-3"
        if is_strength: return "5 x 3-5"
        return "3 x 8"
    else: # Peaking
        if is_tech: return "5 x 1-2"
        if is_strength: return "3 x 2-3"
        return "3 x 5"

def get_rm_for_exercise(ex_choice, athlete_data):
    # Detaillierte Zuweisung der neuen 1RMs
    if "Front Squat" in ex_choice: 
        return athlete_data.get("front_squat", athlete_data["squat"] * 0.85)
    if "Squat" in ex_choice: 
        return athlete_data["squat"]
    if "Push Press" in ex_choice or "Strict Press" in ex_choice or "Jerk" in ex_choice: 
        return athlete_data.get("push_press", athlete_data["cj"] * 0.8)
    if "Snatch" in ex_choice: 
        return athlete_data["snatch"]
    return athlete_data["cj"]

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
    
    st.sidebar.markdown("**Aktuelle Bestwerte (1RM)**")
    new_snatch = st.sidebar.number_input("Snatch", 20, 250, 80)
    new_cj = st.sidebar.number_input("Clean & Jerk", 20, 300, 100)
    new_squat = st.sidebar.number_input("Back Squat", 20, 400, 120)
    new_fsquat = st.sidebar.number_input("Front Squat", 20, 350, 105)
    new_ppress = st.sidebar.number_input("Push Press", 20, 200, 80)
    
    st.sidebar.markdown("**🎯 Deine Zielstellung**")
    goal_snatch = st.sidebar.number_input("Ziel: Snatch", new_snatch, 300, new_snatch + 5)
    goal_cj = st.sidebar.number_input("Ziel: Clean & Jerk", new_cj, 350, new_cj + 5)

    if st.sidebar.button("Sportler Speichern"):
        if new_name:
            db[new_name] = {
                "gender": new_gender, "bw": new_bw, 
                "snatch": new_snatch, "cj": new_cj, 
                "squat": new_squat, "front_squat": new_fsquat, "push_press": new_ppress,
                "goal_snatch": goal_snatch, "goal_cj": goal_cj,
                "saved_plans": {}
            }
            save_data(db)
            st.sidebar.success(f"{new_name} gespeichert! Seite neu laden...")
            st.rerun()
else:
    athlete_data = db[selected_athlete]
    # Fallback für alte Profile ohne die neuen Felder
    athlete_data.setdefault("front_squat", int(athlete_data["squat"] * 0.85))
    athlete_data.setdefault("push_press", int(athlete_data["cj"] * 0.8))
    athlete_data.setdefault("goal_snatch", athlete_data["snatch"] + 5)
    athlete_data.setdefault("goal_cj", athlete_data["cj"] + 5)
    athlete_data.setdefault("saved_plans", {})
        
    st.sidebar.success(f"Eingeloggt: {selected_athlete}")
    with st.sidebar.expander("Profil & Ziele anpassen"):
        bw = st.number_input("Gewicht", value=float(athlete_data["bw"]))
        s_rm = st.number_input("Snatch", value=int(athlete_data["snatch"]))
        c_rm = st.number_input("C&J", value=int(athlete_data["cj"]))
        sq_rm = st.number_input("Back Squat", value=int(athlete_data["squat"]))
        fsq_rm = st.number_input("Front Squat", value=int(athlete_data["front_squat"]))
        pp_rm = st.number_input("Push Press", value=int(athlete_data["push_press"]))
        st.markdown("**Ziele**")
        g_s = st.number_input("Ziel Snatch", value=int(athlete_data["goal_snatch"]))
        g_c = st.number_input("Ziel C&J", value=int(athlete_data["goal_cj"]))
        
        if st.button("Werte Update"):
            db[selected_athlete].update({
                "bw": bw, "snatch": s_rm, "cj": c_rm, "squat": sq_rm, 
                "front_squat": fsq_rm, "push_press": pp_rm,
                "goal_snatch": g_s, "goal_cj": g_c
            })
            save_data(db)
            st.rerun()

# ==========================================
# 4. HAUPT-APP
# ==========================================
if selected_athlete != "-- Neuer Sportler --":
    tab1, tab2, tab3 = st.tabs(["📝 Trainingsplan Generator", "📊 Readiness & Status", "⏱️ Workout Timer"])

    # --- TAB 1: TRAININGSPLAN GENERATOR ---
    with tab1:
        st.header("Plan Generator & Speicher")
        
        # Motivation & Ziele anzeigen
        st.info(f"🎯 **Dein Ziel:** Snatch {athlete_data['goal_snatch']} kg (Aktuell: {athlete_data['snatch']} kg) | Clean & Jerk {athlete_data['goal_cj']} kg (Aktuell: {athlete_data['cj']} kg)")
        
        c1, c2, c3 = st.columns(3)
        prep_weeks = c1.slider("Vorbereitung gesamt (Wochen)", 4, 16, 8)
        current_week = c2.slider("Aktuelle Woche", 1, prep_weeks, 1)
        
        # Phasen Logik - Immer mit Aufbauphase starten!
        if current_week <= prep_weeks // 3: 
            phase, base_int = "Aufbauphase (Volumen, Hypertrophie, Basis)", 0.68
        elif current_week <= (2 * prep_weeks) // 3: 
            phase, base_int = "Kraft-Phase (Schwere Pulls & Beugen)", 0.82
        else: 
            phase, base_int = "Peaking (Wettkampfvorbereitung)", 0.92
            
        # Optionaler Readiness Check für den Plan (aus Tab 2 abgeleitet, hier fix auf 1.0 wenn nicht gesetzt)
        final_int = base_int * 1.0 

        st.success(f"**Aktuelle Phase:** {phase} | **Basis-Intensität:** {int(final_int*100)}% vom 1RM")

        plan_mode = st.radio("Wie möchtest du deinen Plan erstellen?", 
                             ["Empfohlener Musterplan", "Gespeicherten Plan laden", "Komplett selbst erstellen"], 
                             horizontal=True)

        current_plan_structure = {}

        if plan_mode == "Empfohlener Musterplan":
            days_per_week = st.selectbox("Trainingstage/Woche", [2, 3, 4, 5, 6], index=1)
            current_plan_structure = RECOMMENDED_TEMPLATES[days_per_week]

        elif plan_mode == "Gespeicherten Plan laden":
            saved_plans = list(athlete_data.get("saved_plans", {}).keys())
            if not saved_plans:
                st.warning("Du hast noch keine Pläne gespeichert.")
            else:
                selected_plan_name = st.selectbox("Wähle einen Plan", saved_plans)
                current_plan_structure = athlete_data["saved_plans"][selected_plan_name]

        elif plan_mode == "Komplett selbst erstellen":
            custom_days = st.slider("Wie viele Tage?", 1, 7, 3)
            for i in range(custom_days):
                day_name = f"Tag {i+1}"
                num_ex = st.number_input(f"Übungen für {day_name} (Mindestens 3 empfohlen)", 1, 8, 4, key=f"num_{i}")
                current_plan_structure[day_name] = [ALL_EXERCISES[0]] * num_ex

        st.divider()
        st.subheader("Dein aktueller Plan (Wird berechnet)")
        
        final_plan_to_save = {}
        
        for day, exercises in current_plan_structure.items():
            with st.expander(f"📅 {day}", expanded=True):
                day_data = []
                final_exercises = []
                
                for i, ex_name in enumerate(exercises):
                    if plan_mode == "Komplett selbst erstellen":
                        ex_choice = st.selectbox(f"Übung {i+1}", ALL_EXERCISES, index=ALL_EXERCISES.index(ex_name), key=f"sel_{day}_{i}")
                    else:
                        ex_choice = ex_name
                    
                    final_exercises.append(ex_choice)
                    
                    # Berechnung Kilos mit neuer 1RM Logik
                    rm_ref = get_rm_for_exercise(ex_choice, athlete_data)
                    calc_w = round(rm_ref * final_int, 1)
                    
                    if ex_choice in EXERCISE_CATALOG["Zubehör (Accessory)"]:
                        calc_w = "Körpergewicht / RPE 8"
                    else:
                        calc_w = f"{calc_w} kg"
                        
                    sets_reps = get_sets_reps(phase, ex_choice)
                    day_data.append({"Übung": ex_choice, "Sätze x Wdh": sets_reps, "Ziel-Gewicht": calc_w})
                
                final_plan_to_save[day] = final_exercises
                st.table(pd.DataFrame(day_data))
                
        st.divider()
        save_name = st.text_input("Name für den Plan zum Speichern (z.B. 'Off-Season 5 Tage')")
        if st.button("Diesen Plan im Profil speichern"):
            if save_name:
                athlete_data["saved_plans"][save_name] = final_plan_to_save
                db[selected_athlete] = athlete_data
                save_data(db)
                st.success(f"Plan '{save_name}' wurde dauerhaft gespeichert!")
                st.rerun()

    # --- TAB 2: READINESS & STATUS ---
    with tab2:
        st.header(f"Status & Gesundheit: {selected_athlete}")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Tagesform (Readiness)")
            sleep = st.slider("Schlafqualität", 1, 10, 7)
            stress = st.slider("Stress (1-10)", 1, 10, 4)
            soreness = st.slider("Muskelkater (1-10)", 1, 10, 3)
            readiness_score = sleep - (stress * 0.5) - (soreness * 0.5)
            if readiness_score >= 5: st.success("Du bist fit! Intensität kann leicht gepusht werden.")
            elif readiness_score < 1: st.error("Hohe Ermüdung. Erwäge heute 10% Gewicht zu droppen.")
            else: st.info("Normale Tagesform.")
            
        with col2:
            st.subheader("Beschwerden & Prehab")
            injuries = st.multiselect("Hast du aktuelle Beschwerden?", ["Knie", "Schulter", "Unterer Rücken"])
            for inj in injuries: 
                st.warning(f"Empfohlenes Warm-Up für {inj}: {MOBILITY_DRILLS[inj]}")

    # --- TAB 3: WORKOUT TIMER ---
    with tab3:
        components.html("""
        <div style="background:#1e1e1e; padding:15px; border-radius:10px; color:white; text-align:center;">
            <h3>Pausen-Timer</h3><h1 id="t">02:00</h1>
            <button onclick="s(90)" style="background:#FF9800; color:white; border:none; padding:10px; border-radius:5px;">1.5 Min</button>
            <button onclick="s(120)" style="background:#4CAF50; color:white; border:none; padding:10px; border-radius:5px;">2 Min</button>
            <button onclick="s(180)" style="background:#2196F3; color:white; border:none; padding:10px; border-radius:5px;">3 Min</button>
            <script>var i; function s(d){clearInterval(i); var t=d,m,s; i=setInterval(function(){m=parseInt(t/60,10);s=parseInt(t%60,10);document.getElementById('t').textContent=(m<10?"0"+m:m)+":"+(s<10?"0"+s:s);if(--t<0)clearInterval(i);},1000);}</script>
        </div>""", height=200)

else:
    st.info("Bitte links in der Sidebar einen Sportler anlegen oder wählen, um zu starten.")
