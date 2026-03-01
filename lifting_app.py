import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
import datetime

st.set_page_config(page_title="ProLifting Coach OS (RTK)", layout="wide", page_icon="🏋️‍♂️")

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
# 2. ÜBUNGEN NACH BVDG / IAT (RTK)
# ==========================================
EXERCISE_CATALOG = {
    "WK & WK-nahe Übungen (Reißen)": ["Reißen (Snatch)", "Standreißen", "Hangreißen", "Reißkniebeuge", "Reißen aus Böcken"],
    "WK & WK-nahe Übungen (Stoßen)": ["Stoßen (Clean & Jerk)", "Standumsetzen", "Ausstoßen", "Schwungdrücken", "Hangumsetzen"],
    "ZUB - Kniebeugen": ["Kniebeuge hinten", "Kniebeuge vorn", "Kniebeuge mit Stopp"],
    "ZUB - Züge": ["Zug eng (Clean Pull)", "Zug breit (Snatch Pull)", "Kreuzheben eng", "Kreuzheben breit"],
    "ATH - Athletik & Rumpf": ["Kraftdrücken (Strict Press)", "Plank / Unterarmstütz", "Rumpfaufrichten (Hyperextensions)", "Klimmzüge", "Bauchpresse", "Kugelschocken (Med-Ball)"]
}
ALL_EXERCISES = [ex for sublist in EXERCISE_CATALOG.values() for ex in sublist]

# Musterpläne orientiert an der RTK (Immer WK -> ZUB -> ATH)
RECOMMENDED_TEMPLATES = {
    2: {"Tag 1 (Fokus Reißen)": ["Reißen (Snatch)", "Kniebeuge hinten", "Zug breit (Snatch Pull)", "Plank / Unterarmstütz"], 
        "Tag 2 (Fokus Stoßen)": ["Stoßen (Clean & Jerk)", "Kniebeuge vorn", "Zug eng (Clean Pull)", "Rumpfaufrichten (Hyperextensions)"]},
    
    3: {"Tag 1 (Reißen & Beuge)": ["Reißen (Snatch)", "Kniebeuge hinten", "Zug breit (Snatch Pull)", "Kraftdrücken (Strict Press)"], 
        "Tag 2 (Stand-Varianten)": ["Standumsetzen", "Schwungdrücken", "Kniebeuge vorn (Leicht)", "Bauchpresse"], 
        "Tag 3 (Klassisch Schwer)": ["Stoßen (Clean & Jerk)", "Reißkniebeuge", "Zug eng (Clean Pull)", "Rumpfaufrichten (Hyperextensions)"]},
    
    4: {"Tag 1 (Schwer Beugen)": ["Kniebeuge hinten", "Reißen (Snatch)", "Zug breit (Snatch Pull)", "Plank / Unterarmstütz"], 
        "Tag 2 (Schwer Umsetzen)": ["Stoßen (Clean & Jerk)", "Zug eng (Clean Pull)", "Schwungdrücken", "Klimmzüge"], 
        "Tag 3 (Technik/Stand)": ["Standreißen", "Standumsetzen", "Reißkniebeuge", "Bauchpresse"], 
        "Tag 4 (Wettkampfnah)": ["Reißen (Snatch)", "Stoßen (Clean & Jerk)", "Kniebeuge vorn", "Rumpfaufrichten (Hyperextensions)"]},
    
    5: {"Tag 1 (Technik Reißen)": ["Reißen (Snatch)", "Kniebeuge hinten", "Zug breit (Snatch Pull)", "Plank / Unterarmstütz"], 
        "Tag 2 (Technik Stoßen)": ["Stoßen (Clean & Jerk)", "Zug eng (Clean Pull)", "Kraftdrücken (Strict Press)", "Klimmzüge"], 
        "Tag 3 (Stand/Entlastung)": ["Standreißen", "Standumsetzen", "Schwungdrücken", "Bauchpresse"], 
        "Tag 4 (Schwer Beugen)": ["Kniebeuge vorn", "Ausstoßen", "Zug breit (Snatch Pull)", "Rumpfaufrichten (Hyperextensions)"], 
        "Tag 5 (Max/Klassiker)": ["Reißen (Snatch)", "Stoßen (Clean & Jerk)", "Kniebeuge hinten", "Kugelschocken (Med-Ball)"]},
    
    6: {"Tag 1 (Beuge & Reißen)": ["Kniebeuge hinten", "Reißen (Snatch)", "Zug breit (Snatch Pull)", "Plank / Unterarmstütz"], 
        "Tag 2 (Züge & Stoßen)": ["Stoßen (Clean & Jerk)", "Kniebeuge vorn", "Zug eng (Clean Pull)", "Bauchpresse"], 
        "Tag 3 (Stand-Technik)": ["Standreißen", "Schwungdrücken", "Reißkniebeuge", "Klimmzüge"], 
        "Tag 4 (Beuge & Ausstoßen)": ["Kniebeuge vorn", "Standumsetzen", "Kraftdrücken (Strict Press)", "Rumpfaufrichten (Hyperextensions)"], 
        "Tag 5 (Hang-Technik)": ["Hangreißen", "Hangumsetzen", "Zug breit (Snatch Pull)", "Plank / Unterarmstütz"], 
        "Tag 6 (Klassiker 100%)": ["Reißen (Snatch)", "Stoßen (Clean & Jerk)", "Kniebeuge hinten", "Kugelschocken (Med-Ball)"]}
}

def get_rm_for_exercise(ex_choice, athlete_data):
    if "Kniebeuge vorn" in ex_choice: return athlete_data.get("front_squat", athlete_data["squat"] * 0.85)
    if "Kniebeuge hinten" in ex_choice: return athlete_data["squat"]
    if "drücken" in ex_choice.lower() or "ausstoßen" in ex_choice.lower(): return athlete_data.get("push_press", athlete_data["cj"] * 0.8)
    if "reiß" in ex_choice.lower(): return athlete_data["snatch"]
    return athlete_data["cj"]

def get_progressive_sets(phase, ex_name, rm):
    # Athletik/Rumpf bekommt keine % Berechnung
    if ex_name in EXERCISE_CATALOG["ATH - Athletik & Rumpf"]:
        return "3 Sätze x 10-15 Wdh (Zusatzlast nach Gefühl)"

    mod = 0.85 if "(Leicht)" in ex_name or "Stand" in ex_name else 1.0
    rm = rm * mod

    # Orientiert an BVDG Intensitätszonen (Z1-Z5)
    if "VP1" in phase:
        # Zone 1-3: Viel Volumen, Technik festigen (70-80%)
        w1, w2, w3 = round(rm*0.70), round(rm*0.75), round(rm*0.80)
        return f"{w1}kg/4/2 , {w2}kg/3/2 , {w3}kg/3/1"
    elif "VP2" in phase:
        # Zone 3-4: Kraftausprägung, weniger Wdh, höhere Last (80-90%)
        w1, w2, w3 = round(rm*0.80), round(rm*0.85), round(rm*0.90)
        return f"{w1}kg/3/1 , {w2}kg/2/2 , {w3}kg/2/2"
    else: 
        # WP: Wettkampfperiode, Peaking (85-100%)
        w1, w2, w3 = round(rm*0.85), round(rm*0.90), round(rm*0.95)
        return f"{w1}kg/2/1 , {w2}kg/1/1 , {w3}kg/1/2"

# ==========================================
# 3. SIDEBAR & PROFIL
# ==========================================
st.sidebar.title("🏋️‍♂️ BVDG/RTK Coach OS")
athlete_names = list(db.keys())
selected_athlete = st.sidebar.selectbox("Sportler wählen", ["-- Neuer Sportler --"] + athlete_names)

if selected_athlete == "-- Neuer Sportler --":
    st.sidebar.subheader("Neuen Sportler anlegen")
    new_name = st.sidebar.text_input("Name")
    new_gender = st.sidebar.radio("Geschlecht", ["Männlich", "Weiblich"])
    new_bw = st.sidebar.number_input("Körpergewicht (kg)", 40.0, 150.0, 80.0)
    
    st.sidebar.markdown("**Aktuelle Bestwerte (1RM)**")
    new_snatch = st.sidebar.number_input("Reißen (Snatch)", 20, 250, 80)
    new_cj = st.sidebar.number_input("Stoßen (C&J)", 20, 300, 100)
    new_squat = st.sidebar.number_input("Kniebeuge hinten", 20, 400, 120)
    new_fsquat = st.sidebar.number_input("Kniebeuge vorn", 20, 350, 105)
    new_ppress = st.sidebar.number_input("Schwungdrücken", 20, 200, 80)
    
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
    athlete_data.setdefault("logbook", [])
    athlete_data.setdefault("saved_plans", {})
        
    st.sidebar.success(f"Eingeloggt: {selected_athlete}")
    with st.sidebar.expander("Profil anpassen"):
        bw = st.number_input("Gewicht", value=float(athlete_data["bw"]))
        s_rm = st.number_input("Reißen", value=int(athlete_data["snatch"]))
        c_rm = st.number_input("Stoßen", value=int(athlete_data["cj"]))
        sq_rm = st.number_input("KB hinten", value=int(athlete_data["squat"]))
        fsq_rm = st.number_input("KB vorn", value=int(athlete_data.get("front_squat", sq_rm*0.85)))
        pp_rm = st.number_input("Drücken", value=int(athlete_data.get("push_press", c_rm*0.8)))
        
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
    tab1, tab2, tab3 = st.tabs(["📝 RTK Trainingsplan", "📖 Logbuch", "⏱️ Tools & Readiness"])

    # --- TAB 1: TRAININGSPLAN GENERATOR ---
    with tab1:
        st.header("Plan Generator (Basierend auf RTK/BVDG)")
        
        c1, c2 = st.columns(2)
        prep_weeks = c1.slider("Zykluslänge (Wochen)", 4, 16, 12)
        current_week = c2.slider("Aktuelle Woche", 1, prep_weeks, 1)
        
        # RTK Phasen (Makrozyklus)
        if current_week <= prep_weeks * 0.4: 
            phase = "VP1 (Vorbereitungsperiode 1) - Fokus: Volumen, Technik, Basis"
        elif current_week <= prep_weeks * 0.8: 
            phase = "VP2 (Vorbereitungsperiode 2) - Fokus: Kraftausprägung, Zone 3-4"
        else: 
            phase = "WP (Wettkampfperiode) - Fokus: Peaking, ZNS-Aktivierung, Zone 5"
            
        st.success(f"**Aktuelle Trainingsetappe:** {phase}")

        plan_mode = st.radio("Erstellungsmethode:", 
                             ["RTK Musterplan laden", "Gespeicherten Plan laden", "Komplett selbst erstellen"], 
                             horizontal=True)

        current_plan_structure = {}

        if plan_mode == "RTK Musterplan laden":
            days_per_week = st.selectbox("Trainingstage/Woche", [2, 3, 4, 5, 6], index=2)
            current_plan_structure = RECOMMENDED_TEMPLATES[days_per_week]
            st.caption("ℹ️ RTK-Prinzip: Ein Tag beginnt idR mit einer WK-Übung, geht in eine spezielle ZUB (Beuge/Zug) über und endet mit Athletik (ATH).")
            
        elif plan_mode == "Gespeicherten Plan laden":
            saved_plans = list(athlete_data.get("saved_plans", {}).keys())
            if not saved_plans: 
                st.warning("Du hast noch keine Pläne gespeichert.")
            else: 
                selected_plan_name = st.selectbox("Wähle einen Plan", saved_plans)
                current_plan_structure = athlete_data["saved_plans"][selected_plan_name]
                
        elif plan_mode == "Komplett selbst erstellen":
            custom_days = st.slider("Wie viele Trainingstage?", 1, 7, 4)
            for i in range(custom_days):
                day_name = f"Trainingstag {i+1}"
                num_ex = st.number_input(f"Anzahl Übungen für {day_name}", 1, 8, 4, key=f"num_{i}")
                current_plan_structure[day_name] = [ALL_EXERCISES[0]] * num_ex

        st.divider()
        st.subheader("Dein aktueller Plan")
        
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
                    
                    rm_ref = get_rm_for_exercise(ex_choice, athlete_data)
                    progression_string = get_progressive_sets(phase, ex_choice, rm_ref)
                    
                    day_data.append({"Übung": ex_choice, "Vorgabe (Gewicht / Wdh / Sätze)": progression_string})
                
                final_plan_to_save[day] = final_exercises
                st.table(pd.DataFrame(day_data))
                
        st.divider()
        st.subheader("Plan dauerhaft speichern")
        save_name = st.text_input("Name für den Plan (z.B. 'VP1 - 4 Tage RTK')", placeholder="Plan Name eingeben...")
        if st.button("Speichern"):
            if save_name:
                athlete_data["saved_plans"][save_name] = final_plan_to_save
                db[selected_athlete] = athlete_data
                save_data(db)
                st.success("Erfolgreich gespeichert!")
                st.rerun()

    # --- TAB 2: LOGBUCH & HISTORY ---
    with tab2:
        st.header("📖 Trainings-Logbuch")
        with st.form("log_form"):
            col1, col2, col3 = st.columns(3)
            log_date = col1.date_input("Datum", datetime.date.today())
            log_ex = col2.selectbox("Übung", ALL_EXERCISES)
            log_result = col3.text_input("Geschafft (z.B. 100/3/2)", placeholder="Gewicht / Wdh / Sätze")
            log_notes = st.text_input("Notizen", placeholder="Gut getroffen / Etwas weich im Empfangen...")
            
            if st.form_submit_button("Ins Logbuch eintragen"):
                if log_result:
                    new_entry = {"Datum": str(log_date), "Übung": log_ex, "Leistung": log_result, "Notiz": log_notes}
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
            df_log = pd.DataFrame(athlete_data["logbook"]).iloc[::-1]
            st.dataframe(df_log, use_container_width=True)
        else:
            st.info("Noch keine Einträge vorhanden.")

    # --- TAB 3: READINESS & TOOLS ---
    with tab3:
        st.header("Readiness & Pausen")
        
        sleep = st.slider("Schlafqualität", 1, 10, 7)
        stress = st.slider("Stress (1-10)", 1, 10, 4)
        if (sleep - stress) < 2:
            st.warning("⚠️ Dein ZNS scheint vorbelastet. Überlege, die schweren Sätze heute um 5% zu reduzieren.")
            
        components.html("""
        <div style="background:#1e1e1e; padding:15px; border-radius:10px; color:white; text-align:center; margin-top: 20px;">
            <h3>ZNS-Pausen-Timer</h3><h1 id="t">02:00</h1>
            <button onclick="s(90)" style="background:#FF9800; color:white; border:none; padding:10px; border-radius:5px;">1.5 Min (ZUB)</button>
            <button onclick="s(120)" style="background:#4CAF50; color:white; border:none; padding:10px; border-radius:5px;">2 Min (WK)</button>
            <button onclick="s(180)" style="background:#2196F3; color:white; border:none; padding:10px; border-radius:5px;">3 Min (Max)</button>
            <script>var i; function s(d){clearInterval(i); var t=d,m,s; i=setInterval(function(){m=parseInt(t/60,10);s=parseInt(t%60,10);document.getElementById('t').textContent=(m<10?"0"+m:m)+":"+(s<10?"0"+s:s);if(--t<0)clearInterval(i);},1000);}</script>
        </div>""", height=220)

else:
    st.info("Bitte links einen Sportler anlegen oder wählen.")
