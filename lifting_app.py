import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
import datetime
import math

st.set_page_config(page_title="ProLifting OS - Elite", layout="wide", page_icon="🥇")

# ==========================================
# 1. DATENBANK & PARSER-LOGIK
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

def parse_log_metrics(log_string):
    tonnage = 0
    nl = 0
    max_weight = 0
    blocks = str(log_string).split(',')
    for block in blocks:
        parts = block.strip().split('/')
        if len(parts) >= 3:
            try:
                w = float(parts[0].replace('kg', '').strip())
                r = int(parts[1].strip())
                s = int(parts[2].strip())
                tonnage += w * r * s
                nl += r * s
                if w > max_weight: max_weight = w
            except: pass
    return tonnage, nl, max_weight

def calc_sinclair(total, bw, gender):
    if gender == "Männlich": A, B = 0.7519, 175.5
    else: A, B = 0.7834, 153.6
    if bw > B: return total
    res = 10 ** (A * (math.log10(bw / B) ** 2))
    return round(total * res, 2)

# ==========================================
# 2. ÜBUNGEN NACH BVDG / IAT (RTK)
# ==========================================
EXERCISE_CATALOG = {
    "WK & WK-nahe Übungen (Reißen)": ["Reißen (Snatch)", "Standreißen", "Hangreißen", "Reißkniebeuge"],
    "WK & WK-nahe Übungen (Stoßen)": ["Stoßen (Clean & Jerk)", "Standumsetzen", "Ausstoßen", "Schwungdrücken"],
    "ZUB - Kniebeugen": ["Kniebeuge hinten", "Kniebeuge vorn", "Kniebeuge mit Stopp"],
    "ZUB - Züge": ["Zug eng (Clean Pull)", "Zug breit (Snatch Pull)", "Kreuzheben"],
    "ATH - Athletik & Rumpf": ["Kraftdrücken (Strict Press)", "Plank / Unterarmstütz", "Rumpfaufrichten (Hyperextensions)", "Bauchpresse"]
}
ALL_EXERCISES = [ex for sublist in EXERCISE_CATALOG.values() for ex in sublist]

RECOMMENDED_TEMPLATES = {
    3: {"Tag 1 (Reißen & Beuge)": ["Reißen (Snatch)", "Kniebeuge hinten", "Zug breit (Snatch Pull)"], 
        "Tag 2 (Stand-Varianten)": ["Standumsetzen", "Schwungdrücken", "Kniebeuge vorn (Leicht)"], 
        "Tag 3 (Klassisch Schwer)": ["Stoßen (Clean & Jerk)", "Reißkniebeuge", "Zug eng (Clean Pull)"]},
    4: {"Tag 1 (Schwer Beugen)": ["Kniebeuge hinten", "Reißen (Snatch)", "Zug breit (Snatch Pull)"], 
        "Tag 2 (Schwer Umsetzen)": ["Stoßen (Clean & Jerk)", "Zug eng (Clean Pull)", "Schwungdrücken"], 
        "Tag 3 (Technik/Stand)": ["Standreißen", "Standumsetzen", "Reißkniebeuge"], 
        "Tag 4 (Wettkampfnah)": ["Reißen (Snatch)", "Stoßen (Clean & Jerk)", "Kniebeuge vorn"]},
    5: {"Tag 1 (Technik Reißen)": ["Reißen (Snatch)", "Kniebeuge hinten", "Zug breit (Snatch Pull)"], 
        "Tag 2 (Technik Stoßen)": ["Stoßen (Clean & Jerk)", "Zug eng (Clean Pull)", "Kraftdrücken (Strict Press)"], 
        "Tag 3 (Stand/Entlastung)": ["Standreißen", "Standumsetzen", "Schwungdrücken"], 
        "Tag 4 (Schwer Beugen)": ["Kniebeuge vorn", "Ausstoßen", "Zug breit (Snatch Pull)"], 
        "Tag 5 (Max/Klassiker)": ["Reißen (Snatch)", "Stoßen (Clean & Jerk)", "Kniebeuge hinten"]}
}

def get_rm_for_exercise(ex_choice, athlete_data):
    choice = ex_choice.lower()
    if "standreißen" in choice: return athlete_data.get("power_snatch", athlete_data["snatch"] * 0.82)
    if "standumsetzen" in choice: return athlete_data.get("power_clean", athlete_data["cj"] * 0.82)
    if "ausstoßen" in choice: return athlete_data.get("jerk", athlete_data["cj"] * 1.05)
    if "zug" in choice or "kreuzheben" in choice: return athlete_data.get("deadlift", athlete_data["squat"] * 1.1)
    if "kniebeuge vorn" in choice: return athlete_data.get("front_squat", athlete_data["squat"] * 0.85)
    if "kniebeuge hinten" in choice: return athlete_data["squat"]
    if "drücken" in choice: return athlete_data.get("push_press", athlete_data["cj"] * 0.8)
    if "reiß" in choice: return athlete_data["snatch"]
    return athlete_data["cj"]

def get_progressive_sets(phase, ex_name, rm):
    if ex_name in EXERCISE_CATALOG["ATH - Athletik & Rumpf"]: return "3 Sätze x 10-15 Wdh"
    mod = 0.85 if "(Leicht)" in ex_name or "Stand" in ex_name else 1.0
    rm = rm * mod
    
    if "VP1" in phase:
        w1, w2, w3 = round(rm*0.70), round(rm*0.75), round(rm*0.80)
        return f"{w1}kg/4/2 , {w2}kg/3/2 , {w3}kg/3/1"
    elif "VP2" in phase:
        w1, w2, w3 = round(rm*0.80), round(rm*0.85), round(rm*0.90)
        return f"{w1}kg/3/1 , {w2}kg/2/2 , {w3}kg/2/2"
    else: 
        w1, w2, w3 = round(rm*0.85), round(rm*0.90), round(rm*0.95)
        return f"{w1}kg/2/1 , {w2}kg/1/1 , {w3}kg/1/2"

# ==========================================
# 3. SIDEBAR & PROFIL
# ==========================================
st.sidebar.title("🥇 ProLifting OS")
athlete_names = list(db.keys())
selected_athlete = st.sidebar.selectbox("Sportler wählen", ["-- Neuer Sportler --"] + athlete_names)

if selected_athlete == "-- Neuer Sportler --":
    st.sidebar.subheader("Neuen Sportler anlegen")
    new_name = st.sidebar.text_input("Name")
    new_gender = st.sidebar.radio("Geschlecht", ["Männlich", "Weiblich"])
    new_bw = st.sidebar.number_input("Körpergewicht (kg)", 40.0, 150.0, 80.0)
    
    st.sidebar.markdown("**Aktuelle Bestwerte**")
    new_snatch = st.sidebar.number_input("Reißen (Snatch)", 20, 250, 80)
    new_cj = st.sidebar.number_input("Stoßen (C&J)", 20, 300, 100)
    
    st.sidebar.markdown("**🎯 Deine Ziele**")
    goal_snatch = st.sidebar.number_input("Ziel: Reißen", 20, 300, new_snatch + 5)
    goal_cj = st.sidebar.number_input("Ziel: Stoßen", 20, 350, new_cj + 5)
    
    st.sidebar.caption("Die App errechnet Kniebeugen, Züge und Stand-Werte automatisch im Hintergrund. Du kannst sie später im Profil manuell anpassen!")
    
    if st.sidebar.button("Sportler Speichern"):
        if new_name:
            db[new_name] = {
                "gender": new_gender, "bw": new_bw, 
                "snatch": new_snatch, "cj": new_cj, 
                "goal_snatch": goal_snatch, "goal_cj": goal_cj,
                # AUTO CALCULATE BASE STRENGTH based on current C&J / Snatch
                "squat": int(new_cj / 0.78), 
                "front_squat": int(new_cj / 0.85), 
                "deadlift": int(new_cj * 1.25),
                "power_snatch": int(new_snatch * 0.82), 
                "power_clean": int(new_cj * 0.82), 
                "jerk": int(new_cj * 1.05), 
                "push_press": int(new_cj * 0.8),
                "saved_plans": {}, "logbook": []
            }
            save_data(db)
            st.sidebar.success(f"{new_name} gespeichert! Seite neu laden...")
            st.rerun()
else:
    athlete_data = db[selected_athlete]
    # Fallback für alte Daten (verhindert Abstürze)
    athlete_data.setdefault("logbook", [])
    athlete_data.setdefault("saved_plans", {})
    athlete_data.setdefault("goal_snatch", athlete_data["snatch"] + 5)
    athlete_data.setdefault("goal_cj", athlete_data["cj"] + 5)
    athlete_data.setdefault("squat", int(athlete_data["cj"] / 0.78))
    athlete_data.setdefault("front_squat", int(athlete_data["cj"] / 0.85))
    athlete_data.setdefault("push_press", int(athlete_data["cj"] * 0.8))
    athlete_data.setdefault("deadlift", int(athlete_data["cj"] * 1.25))
    athlete_data.setdefault("power_snatch", int(athlete_data["snatch"] * 0.82))
    athlete_data.setdefault("power_clean", int(athlete_data["cj"] * 0.82))
    athlete_data.setdefault("jerk", int(athlete_data["cj"] * 1.05))
        
    st.sidebar.success(f"Eingeloggt: {selected_athlete}")
    with st.sidebar.expander("Profil, Ziele & 1RMs anpassen"):
        bw = st.number_input("Gewicht", value=float(athlete_data["bw"]))
        
        st.markdown("**🎯 Ziele**")
        g_s = st.number_input("Ziel: Reißen", value=int(athlete_data["goal_snatch"]))
        g_c = st.number_input("Ziel: Stoßen", value=int(athlete_data["goal_cj"]))
        
        st.markdown("**Aktuelle 1RMs** (Wurden automatisch errechnet, passe sie an, wenn du willst!)")
        s_rm = st.number_input("Reißen", value=int(athlete_data["snatch"]))
        c_rm = st.number_input("Stoßen", value=int(athlete_data["cj"]))
        sq_rm = st.number_input("KB hinten", value=int(athlete_data["squat"]))
        fsq_rm = st.number_input("KB vorn", value=int(athlete_data["front_squat"]))
        dl_rm = st.number_input("Kreuzheben/Züge", value=int(athlete_data["deadlift"]))
        ps_rm = st.number_input("Standreißen", value=int(athlete_data["power_snatch"]))
        pc_rm = st.number_input("Standumsetzen", value=int(athlete_data["power_clean"]))
        j_rm = st.number_input("Ausstoßen (Blöcke)", value=int(athlete_data["jerk"]))
        pp_rm = st.number_input("Schwungdrücken", value=int(athlete_data["push_press"]))
        
        if st.button("Werte Update"):
            db[selected_athlete].update({
                "bw": bw, "snatch": s_rm, "cj": c_rm, "squat": sq_rm, 
                "goal_snatch": g_s, "goal_cj": g_c,
                "front_squat": fsq_rm, "deadlift": dl_rm,
                "power_snatch": ps_rm, "power_clean": pc_rm, "jerk": j_rm, "push_press": pp_rm
            })
            save_data(db)
            st.rerun()

# ==========================================
# 4. HAUPT-APP
# ==========================================
if selected_athlete != "-- Neuer Sportler --":
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Planer", "🏋️‍♂️ Live-Workout", "🎯 Ziele & Analytics", "🏆 Tools"])

    # --- TAB 1: TRAININGSPLAN GENERATOR ---
    with tab1:
        st.header("Plan Generator")
        st.info(f"**Dein aktuelles Ziel:** {athlete_data['goal_snatch']} kg Reißen | {athlete_data['goal_cj']} kg Stoßen. Der Plan errechnet sich aus deinen *aktuellen* Bestwerten, um dich dorthin aufzubauen!")
        
        c1, c2 = st.columns(2)
        prep_weeks = c1.slider("Zykluslänge (Wochen)", 4, 16, 12)
        current_week = c2.slider("Aktuelle Woche", 1, prep_weeks, 1)
        
        if current_week <= prep_weeks * 0.4: phase = "VP1 (Vorbereitungsperiode 1) - Volumen & Technik"
        elif current_week <= prep_weeks * 0.8: phase = "VP2 (Vorbereitungsperiode 2) - Kraftausprägung"
        else: phase = "WP (Wettkampfperiode) - Peaking"

        plan_mode = st.radio("Erstellungsmethode:", ["RTK Musterplan laden", "Gespeicherten Plan laden", "Komplett selbst erstellen"], horizontal=True)

        current_plan_structure = {}

        if plan_mode == "RTK Musterplan laden":
            days_per_week = st.selectbox("Trainingstage/Woche", [3, 4, 5], index=1)
            current_plan_structure = RECOMMENDED_TEMPLATES[days_per_week]
            
        elif plan_mode == "Gespeicherten Plan laden":
            saved_plans = list(athlete_data.get("saved_plans", {}).keys())
            if not saved_plans: st.warning("Keine Pläne gespeichert.")
            else: current_plan_structure = athlete_data["saved_plans"][st.selectbox("Wähle einen Plan", saved_plans)]
                
        elif plan_mode == "Komplett selbst erstellen":
            custom_days = st.slider("Wie viele Trainingstage?", 1, 6, 4)
            for i in range(custom_days):
                day_name = f"Trainingstag {i+1}"
                num_ex = st.number_input(f"Anzahl Übungen {day_name}", 1, 8, 4, key=f"num_{i}")
                current_plan_structure[day_name] = [{"übung": ALL_EXERCISES[0], "vorgabe": ""}] * num_ex

        st.divider()
        st.markdown("### Dein interaktiver Plan")
        final_plan_to_save = {}
        
        for day, exercises in current_plan_structure.items():
            with st.expander(f"📅 {day}", expanded=True):
                day_plan_to_save = []
                for i, item in enumerate(exercises):
                    if isinstance(item, dict):
                        default_ex, saved_vorgabe = item.get("übung", ALL_EXERCISES[0]), item.get("vorgabe", "")
                    else:
                        default_ex, saved_vorgabe = item, ""
                        
                    idx = ALL_EXERCISES.index(default_ex) if default_ex in ALL_EXERCISES else 0
                    c_ex, c_rep = st.columns([1, 2])
                    
                    with c_ex: ex_choice = st.selectbox(f"Übung {i+1}", ALL_EXERCISES, index=idx, key=f"ex_{day}_{i}")
                    
                    rm_ref = get_rm_for_exercise(ex_choice, athlete_data)
                    recommendation = get_progressive_sets(phase, ex_choice, rm_ref)
                    display_val = saved_vorgabe if (plan_mode == "Gespeicherten Plan laden" and saved_vorgabe and ex_choice == default_ex) else recommendation

                    with c_rep: user_vorgabe = st.text_input(f"Vorgabe", value=display_val, key=f"vg_{day}_{i}")
                    day_plan_to_save.append({"übung": ex_choice, "vorgabe": user_vorgabe})
                
                final_plan_to_save[day] = day_plan_to_save
                
        st.divider()
        save_name = st.text_input("Name für den Plan", placeholder="z.B. 'Mein RTK Zyklus 1'")
        if st.button("Individuellen Plan speichern"):
            if save_name:
                athlete_data["saved_plans"][save_name] = final_plan_to_save
                db[selected_athlete] = athlete_data
                save_data(db)
                st.success("Plan gespeichert!")
                st.rerun()

    # --- TAB 2: LIVE-WORKOUT & LOGBUCH ---
    with tab2:
        st.header("🏋️‍♂️ Live-Workout")
        saved_plans = list(athlete_data.get("saved_plans", {}).keys())
        
        if not saved_plans:
            st.warning("Bitte erstelle und speichere zuerst einen Trainingsplan im ersten Tab!")
        else:
            col_p, col_d = st.columns(2)
            selected_plan = col_p.selectbox("Welchen Plan trainierst du?", saved_plans)
            days_in_plan = list(athlete_data["saved_plans"][selected_plan].keys())
            selected_day = col_d.selectbox("Welcher Tag ist heute?", days_in_plan)
            workout_date = st.date_input("Datum", datetime.date.today())
            exercises_today = athlete_data["saved_plans"][selected_plan][selected_day]
            
            st.divider()
            
            with st.form("live_workout_form"):
                results_to_log = []
                st.subheader(f"Dein Workout: {selected_day}")
                
                for i, ex in enumerate(exercises_today):
                    ex_name = ex.get("übung", "Unbekannt")
                    ex_vorgabe = ex.get("vorgabe", "")
                    st.markdown(f"**{i+1}. {ex_name}**")
                    c1, c2 = st.columns([1, 2])
                    is_done = c1.checkbox(f"Erledigt", value=True, key=f"done_{i}")
                    actual_result = c2.text_input("Geleistetes Gewicht/Wdh/Sätze (Bei Abweichung ändern!)", value=ex_vorgabe, key=f"actual_{i}")
                    results_to_log.append({"name": ex_name, "done": is_done, "result": actual_result})
                    st.write("---")
                
                log_notes = st.text_input("Notizen zur heutigen Einheit (Optional)", placeholder="Technik war stabil...")
                if st.form_submit_button("✅ Gesamtes Workout ins Logbuch speichern"):
                    logged_count = 0
                    for item in results_to_log:
                        if item["done"] and item["result"]:
                            tonnage, nl, max_w = parse_log_metrics(item["result"])
                            new_entry = {
                                "Datum": str(workout_date), "Übung": item["name"], 
                                "Leistung": item["result"], "Max Gewicht": max_w, 
                                "NL": nl, "Tonnage": tonnage, "Notiz": log_notes
                            }
                            athlete_data["logbook"].append(new_entry)
                            logged_count += 1
                    db[selected_athlete] = athlete_data
                    save_data(db)
                    st.success(f"Bäm! {logged_count} Übungen erfolgreich im Logbuch gespeichert.")
                    st.rerun()

        st.divider()
        with st.expander("📖 Historie (Dein klassisches Logbuch ansehen)"):
            if athlete_data["logbook"]:
                df_log = pd.DataFrame(athlete_data["logbook"]).iloc[::-1]
                st.dataframe(df_log, use_container_width=True)
            else:
                st.info("Noch keine Einträge vorhanden.")

    # --- TAB 3: ZIELE & ANALYTICS ---
    with tab3:
        st.header("🎯 Deine Ziel-Analyse (Was du brauchst)")
        goal_s = athlete_data.get("goal_snatch", athlete_data["snatch"] + 5)
        goal_cj = athlete_data.get("goal_cj", athlete_data["cj"] + 5)
        
        st.write(f"Um dein Ziel von **{goal_s} kg Reißen** und **{goal_cj} kg Stoßen** sicher zu bewältigen, benötigst du laut sportwissenschaftlichen RTK-Standards ungefähr folgende Basis-Kraftwerte:")
        
        # Berechnung anhand der Ziele
        req_sq = int(goal_cj / 0.78)
        req_fsq = int(goal_cj / 0.85)
        req_dl = int(goal_cj * 1.25)
        req_ps = int(goal_s * 0.82)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Kniebeuge hinten", f"{req_sq} kg", f"Dein aktuelles 1RM: {athlete_data['squat']} kg", delta_color="off")
        c2.metric("Kniebeuge vorn", f"{req_fsq} kg", f"Dein aktuelles 1RM: {athlete_data['front_squat']} kg", delta_color="off")
        c3.metric("Züge/Kreuzheben", f"{req_dl} kg", f"Dein aktuelles 1RM: {athlete_data['deadlift']} kg", delta_color="off")
        c4.metric("Standreißen", f"{req_ps} kg", f"Dein aktuelles 1RM: {athlete_data['power_snatch']} kg", delta_color="off")
        
        st.divider()
        st.header("🧬 Schwachstellen-Diagnostik (Aktueller Stand)")
        s_val = athlete_data["snatch"]
        cj_val = athlete_data["cj"]
        sq_val = athlete_data["squat"]
        fsq_val = athlete_data["front_squat"]
        
        ratio_s_cj = round((s_val / cj_val) * 100, 1) if cj_val > 0 else 0
        ratio_cj_sq = round((cj_val / sq_val) * 100, 1) if sq_val > 0 else 0
        ratio_fsq_sq = round((fsq_val / sq_val) * 100, 1) if sq_val > 0 else 0
        
        d1, d2, d3 = st.columns(3)
        d1.metric("Reißen zu Stoßen", f"{ratio_s_cj}%", "Ideal: 78% - 82%", delta_color="off")
        if ratio_s_cj < 78: d1.caption("🔴 Dein Reißen ist im Verhältnis zu schwach. Fokus auf Technik!")
        elif ratio_s_cj > 83: d1.caption("🟡 Reißen stark! Dir fehlt Beinkraft für das schwere Umsetzen.")
        else: d1.caption("🟢 Perfektes Gleichgewicht.")
        
        d2.metric("Stoßen zu KB Hinten", f"{ratio_cj_sq}%", "Ideal: 75% - 80%", delta_color="off")
        if ratio_cj_sq < 75: d2.caption("🔴 Du bringst deine Beinkraft nicht auf die Hantel. Fokus auf Umsetzen und Züge!")
        else: d2.caption("🟢 Exzellente Effizienz.")

        d3.metric("KB Vorn zu KB Hinten", f"{ratio_fsq_sq}%", "Ideal: 85% - 90%", delta_color="off")
        if ratio_fsq_sq < 85: d3.caption("🔴 Rumpf/Quads sind deine Schwachstelle.")
        else: d3.caption("🟢 Sehr gute Aufrichtung und Quad-Dominanz.")

        st.divider()
        st.header("📈 Trainings-Analytics")
        if not athlete_data["logbook"]:
            st.warning("Trage Daten im Live-Workout ein, um Graphen zu sehen!")
        else:
            df = pd.DataFrame(athlete_data["logbook"])
            df['Datum'] = pd.to_datetime(df['Datum'])
            df = df.sort_values(by="Datum")
            
            c1, c2, c3 = st.columns(3)
            total_tonnage = df.get('Tonnage', pd.Series([0])).sum()
            total_nl = df.get('NL', pd.Series([0])).sum()
            k_wert = round(total_tonnage / total_nl, 1) if total_nl > 0 else 0
            
            c1.metric("Gesamt Tonnage", f"{int(total_tonnage):,} kg")
            c2.metric("Total NL", int(total_nl))
            c3.metric("K-Wert (Ø Hantellast)", f"{k_wert} kg")
            
            st.subheader("Kraftentwicklung")
            exercises_to_plot = ["Reißen (Snatch)", "Stoßen (Clean & Jerk)", "Kniebeuge hinten"]
            chart_data = pd.DataFrame(index=df['Datum'].unique())
            
            has_data = False
            for ex in exercises_to_plot:
                ex_data = df[df['Übung'] == ex]
                if not ex_data.empty:
                    daily_max = ex_data.groupby('Datum')['Max Gewicht'].max()
                    chart_data[ex] = daily_max
                    has_data = True
            
            if has_data:
                chart_data = chart_data.ffill() 
                st.line_chart(chart_data)

    # --- TAB 4: WETTKAMPF & TOOLS ---
    with tab4:
        st.header("🏆 Wettkampf-Manager & Tools")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔥 Warm-Up Calculator")
            opener_snatch = st.number_input("Dein 1. Versuch (Opener)", min_value=20, max_value=300, value=int(athlete_data["snatch"]*0.95))
            st.markdown(f"""
            **Empfohlenes Aufwärmen für {opener_snatch} kg:**
            * Stange (20kg) x 2 Sätze x 5 Wdh
            * **{round(opener_snatch * 0.4 / 2.5) * 2.5} kg** x 3 Wdh
            * **{round(opener_snatch * 0.6 / 2.5) * 2.5} kg** x 2 Wdh
            * **{round(opener_snatch * 0.8 / 2.5) * 2.5} kg** x 1 Wdh
            * **{round(opener_snatch * 0.9 / 2.5) * 2.5} kg** x 1 Wdh
            * **{round(opener_snatch * 0.95 / 2.5) * 2.5} kg** x 1 Wdh
            """)
        with c2:
            st.subheader("🥇 Sinclair Rechner")
            total = athlete_data["snatch"] + athlete_data["cj"]
            sinclair = calc_sinclair(total, athlete_data["bw"], athlete_data["gender"])
            st.metric("Aktuelles Total", f"{total} kg")
            st.metric("Sinclair Score", f"{sinclair} Punkte")
            
        st.divider()
        components.html("""
        <div style="background:#1e1e1e; padding:15px; border-radius:10px; color:white; text-align:center;">
            <h3>ZNS-Pausen-Timer</h3><h1 id="t">02:00</h1>
            <button onclick="s(90)" style="background:#FF9800; color:white; border:none; padding:10px; border-radius:5px;">1.5 Min</button>
            <button onclick="s(120)" style="background:#4CAF50; color:white; border:none; padding:10px; border-radius:5px;">2 Min</button>
            <button onclick="s(180)" style="background:#2196F3; color:white; border:none; padding:10px; border-radius:5px;">3 Min</button>
            <script>var i; function s(d){clearInterval(i); var t=d,m,s; i=setInterval(function(){m=parseInt(t/60,10);s=parseInt(t%60,10);document.getElementById('t').textContent=(m<10?"0"+m:m)+":"+(s<10?"0"+s:s);if(--t<0)clearInterval(i);},1000);}</script>
        </div>""", height=220)

else:
    st.info("Bitte links einen Sportler anlegen oder wählen.")
