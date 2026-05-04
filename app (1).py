import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
import io

# ── Atria brand colors ──────────────────────────────────────────────
KELP    = "#405A51"
FERN    = "#607663"
RUST    = "#A25B4C"
STONE   = "#F2EEE2"
MOSS    = "#6D7D55"
DUST    = "#E7D4C6"
SAND    = "#DACCB7"
BLUSH   = "#C99287"
OFFBLK  = "#231F20"
NAVY    = "#2B3955"

EVENT_COLORS = {
    "infection":  RUST,
    "symptom":    BLUSH,
    "vaccination": MOSS,
    "medication": NAVY,
    "other":      SAND,
}

BIOMARKER_COLORS = [KELP, NAVY, MOSS, RUST, FERN, BLUSH, "#8B7355", "#5B7FA6"]

CATEGORIES = ["Inflammatory", "Neuro/CNS", "Metabolic", "Hematologic", "Hormonal", "Other"]
EVENT_TYPES = ["infection", "symptom", "vaccination", "medication", "other"]

# ── Page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="BioChronika",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS ──────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500&display=swap');

  html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    background-color: {STONE};
    color: {OFFBLK};
  }}
  .main {{ background-color: {STONE}; }}
  section[data-testid="stSidebar"] {{
    background-color: {KELP} !important;
  }}
  section[data-testid="stSidebar"] * {{
    color: {STONE} !important;
  }}
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] .stRadio label {{
    color: {STONE} !important;
    font-size: 13px;
  }}
  h1, h2, h3 {{
    font-family: 'DM Serif Display', serif;
    color: {KELP};
  }}
  .stButton > button {{
    background-color: {KELP};
    color: {STONE};
    border: none;
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    padding: 0.4rem 1.2rem;
  }}
  .stButton > button:hover {{
    background-color: {FERN};
    color: {STONE};
  }}
  .metric-card {{
    background: white;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    border: 1px solid {SAND};
    margin-bottom: 0.5rem;
  }}
  .metric-label {{
    font-size: 11px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
  }}
  .metric-value {{
    font-size: 22px;
    font-weight: 500;
    color: {OFFBLK};
  }}
  .event-badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
    margin-right: 4px;
  }}
  .tag-infection  {{ background: #f5e0dc; color: {RUST}; }}
  .tag-symptom    {{ background: #f5e4e1; color: #9e5f56; }}
  .tag-vaccination{{ background: #e4ead9; color: {MOSS}; }}
  .tag-medication {{ background: #dde2ec; color: {NAVY}; }}
  .tag-other      {{ background: #ede8e0; color: #7a6f62; }}
  .oor {{ color: {RUST}; font-weight: 600; }}
  .section-header {{
    font-family: 'DM Serif Display', serif;
    font-size: 20px;
    color: {KELP};
    border-bottom: 1px solid {SAND};
    padding-bottom: 6px;
    margin-bottom: 1rem;
  }}
  .upload-hint {{
    background: white;
    border: 1.5px dashed {SAND};
    border-radius: 10px;
    padding: 2rem;
    text-align: center;
    color: #888;
    font-size: 14px;
    margin-bottom: 1rem;
  }}
  div[data-testid="stDataFrame"] {{ border-radius: 8px; overflow: hidden; }}
  .stTabs [data-baseweb="tab-list"] {{ background: white; border-radius: 8px; padding: 4px; }}
  .stTabs [data-baseweb="tab"] {{ border-radius: 6px; }}
  .stTabs [aria-selected="true"] {{ background: {KELP}; color: {STONE} !important; }}
</style>
""", unsafe_allow_html=True)

# ── Session state ───────────────────────────────────────────────────
def init_state():
    if "patient" not in st.session_state:
        st.session_state.patient = {}
    if "biomarkers" not in st.session_state:
        st.session_state.biomarkers = pd.DataFrame(columns=[
            "date","biomarker","value","unit","categories","ref_low","ref_high","lab","notes"
        ])
    if "events" not in st.session_state:
        st.session_state.events = pd.DataFrame(columns=[
            "start_date","end_date","event_type","description","notes"
        ])

init_state()

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
        <div style='padding: 0.5rem 0 1.5rem;'>
            <div style='font-family: DM Serif Display, serif; font-size: 24px; color: {STONE};'>BioChronika</div>
            <div style='font-size: 11px; color: {SAND}; letter-spacing: 0.08em;'>BIOMARKER & CLINICAL EVENT OVERLAY</div>
        </div>
    """, unsafe_allow_html=True)

    page = st.radio("", ["Timeline", "Data Entry", "Trends & Insights"], label_visibility="collapsed")

    if st.session_state.patient:
        p = st.session_state.patient
        st.markdown("---")
        st.markdown(f"<div style='font-size:13px; opacity:0.8;'>Active patient</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:15px; font-weight:500;'>{p.get('name','—')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:11px; opacity:0.7;'>{p.get('dob','')} · {p.get('sex','')}</div>", unsafe_allow_html=True)

    bm = st.session_state.biomarkers
    ev = st.session_state.events
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("Draws", len(bm))
    c2.metric("Events", len(ev))

# ════════════════════════════════════════════════════════════════════
# PAGE: DATA ENTRY
# ════════════════════════════════════════════════════════════════════
if page == "Data Entry":
    st.markdown("## Data Entry")
    st.markdown("Upload CSV files or enter data manually below.")

    tab1, tab2, tab3 = st.tabs(["Patient Profile", "Biomarker Values", "Clinical Events"])

    # ── Patient Profile ──────────────────────────────────────────────
    with tab1:
        st.markdown('<div class="section-header">Patient profile</div>', unsafe_allow_html=True)

        st.markdown('<div class="upload-hint">Upload a patient CSV or fill in manually below</div>', unsafe_allow_html=True)
        uploaded_patient = st.file_uploader("Upload patient CSV", type="csv", key="upload_patient", label_visibility="collapsed")
        if uploaded_patient:
            df = pd.read_csv(uploaded_patient)
            row = df.iloc[0].to_dict()
            st.session_state.patient = {k.lower().replace(" ","_"): str(v) for k,v in row.items()}
            st.success("Patient profile loaded!")

        with st.form("patient_form"):
            c1, c2 = st.columns(2)
            name   = c1.text_input("Full name or alias", value=st.session_state.patient.get("name",""))
            pid    = c2.text_input("Patient ID", value=st.session_state.patient.get("patient_id",""))
            dob    = c1.text_input("Date of birth (YYYY-MM-DD)", value=st.session_state.patient.get("dob",""))
            sex    = c2.selectbox("Sex", ["Female","Male","Other/Prefer not to say"],
                                  index=["Female","Male","Other/Prefer not to say"].index(
                                      st.session_state.patient.get("sex","Female")) if st.session_state.patient.get("sex") in ["Female","Male","Other/Prefer not to say"] else 0)
            dx     = st.text_area("Major diagnoses", value=st.session_state.patient.get("diagnoses",""), height=80)
            meds   = st.text_area("Active medications", value=st.session_state.patient.get("medications",""), height=80)
            notes  = st.text_area("Background notes", value=st.session_state.patient.get("background",""), height=80)
            if st.form_submit_button("Save patient profile"):
                st.session_state.patient = {"name":name,"patient_id":pid,"dob":dob,"sex":sex,
                                            "diagnoses":dx,"medications":meds,"background":notes}
                st.success("Patient profile saved!")

    # ── Biomarker Values ─────────────────────────────────────────────
    with tab2:
        st.markdown('<div class="section-header">Biomarker values</div>', unsafe_allow_html=True)

        st.markdown('<div class="upload-hint">📂 Upload a CSV with columns: date, biomarker, value, unit, categories, ref_low, ref_high, lab, notes</div>', unsafe_allow_html=True)
        uploaded_bm = st.file_uploader("Upload biomarker CSV", type="csv", key="upload_bm", label_visibility="collapsed")
        if uploaded_bm:
            df = pd.read_csv(uploaded_bm)
            df.columns = [c.lower().strip() for c in df.columns]
            for col in ["date","biomarker","value","unit","categories","ref_low","ref_high","lab","notes"]:
                if col not in df.columns:
                    df[col] = ""
            st.session_state.biomarkers = pd.concat([st.session_state.biomarkers, df], ignore_index=True)
            st.success(f"Loaded {len(df)} biomarker entries!")

        with st.expander("Add a single biomarker entry", expanded=False):
            with st.form("bm_form"):
                c1, c2, c3 = st.columns(3)
                bdate = c1.date_input("Date of draw", value=date.today())
                bname = c2.text_input("Biomarker name (e.g. CRP, pTau-181)")
                bval  = c3.number_input("Value", step=0.01)
                c1b, c2b, c3b = st.columns(3)
                bunit = c1b.text_input("Unit (e.g. mg/L, pg/mL)")
                bcats = c2b.multiselect("Categories", CATEGORIES)
                blab  = c3b.text_input("Lab source (optional)")
                c1c, c2c, c3c = st.columns(3)
                bref_lo = c1c.number_input("Reference range low", value=0.0, step=0.01)
                bref_hi = c2c.number_input("Reference range high", value=0.0, step=0.01)
                bnotes  = c3c.text_input("Notes (optional)")
                if st.form_submit_button("Add entry"):
                    new_row = pd.DataFrame([{
                        "date": str(bdate), "biomarker": bname, "value": bval,
                        "unit": bunit, "categories": ", ".join(bcats),
                        "ref_low": bref_lo, "ref_high": bref_hi,
                        "lab": blab, "notes": bnotes
                    }])
                    st.session_state.biomarkers = pd.concat([st.session_state.biomarkers, new_row], ignore_index=True)
                    st.success("Entry added!")

        if not st.session_state.biomarkers.empty:
            st.markdown(f"**{len(st.session_state.biomarkers)} biomarker entries**")
            st.dataframe(st.session_state.biomarkers, use_container_width=True)
            if st.button("Clear all biomarker data"):
                st.session_state.biomarkers = pd.DataFrame(columns=["date","biomarker","value","unit","categories","ref_low","ref_high","lab","notes"])
                st.rerun()

    # ── Clinical Events ──────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="section-header">Clinical events</div>', unsafe_allow_html=True)

        st.markdown('<div class="upload-hint">📂 Upload a CSV with columns: start_date, end_date, event_type, description, notes</div>', unsafe_allow_html=True)
        uploaded_ev = st.file_uploader("Upload events CSV", type="csv", key="upload_ev", label_visibility="collapsed")
        if uploaded_ev:
            df = pd.read_csv(uploaded_ev)
            df.columns = [c.lower().strip() for c in df.columns]
            for col in ["start_date","end_date","event_type","description","notes"]:
                if col not in df.columns:
                    df[col] = ""
            st.session_state.events = pd.concat([st.session_state.events, df], ignore_index=True)
            st.success(f"Loaded {len(df)} clinical events!")

        with st.expander("Add a single clinical event", expanded=False):
            with st.form("ev_form"):
                c1, c2 = st.columns(2)
                estart = c1.date_input("Event start date", value=date.today())
                eend   = c2.date_input("End date (optional — leave today if unknown)", value=date.today())
                c3, c4 = st.columns(2)
                etype  = c3.selectbox("Event type", EVENT_TYPES)
                edesc  = c4.text_input("Description (e.g. COVID-19 infection)")
                enotes = st.text_input("Notes (optional)")
                has_end = st.checkbox("Event has a known end date")
                if st.form_submit_button("Add event"):
                    new_row = pd.DataFrame([{
                        "start_date": str(estart),
                        "end_date": str(eend) if has_end else "",
                        "event_type": etype,
                        "description": edesc,
                        "notes": enotes
                    }])
                    st.session_state.events = pd.concat([st.session_state.events, new_row], ignore_index=True)
                    st.success("Event added!")

        if not st.session_state.events.empty:
            st.markdown(f"**{len(st.session_state.events)} clinical events**")
            st.dataframe(st.session_state.events, use_container_width=True)
            if st.button("Clear all event data"):
                st.session_state.events = pd.DataFrame(columns=["start_date","end_date","event_type","description","notes"])
                st.rerun()

# ════════════════════════════════════════════════════════════════════
# PAGE: TIMELINE
# ════════════════════════════════════════════════════════════════════
elif page == "Timeline":
    st.markdown("## Timeline")

    bm = st.session_state.biomarkers
    ev = st.session_state.events
    pt = st.session_state.patient

    if bm.empty:
        st.markdown("""
        <div class="upload-hint">
            <div style='font-size:32px; margin-bottom:8px;'>🧬</div>
            <div style='font-size:16px; font-weight:500; margin-bottom:4px;'>No data yet</div>
            <div>Go to <strong>Data Entry</strong> to upload or enter biomarker values and clinical events.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Patient header
        if pt:
            st.markdown(f"""
            <div class="metric-card" style='margin-bottom:1rem;'>
                <div style='display:flex; justify-content:space-between; align-items:start;'>
                    <div>
                        <div style='font-family: DM Serif Display, serif; font-size:22px; color:{KELP};'>{pt.get("name","—")}</div>
                        <div style='font-size:13px; color:#888; margin-top:2px;'>
                            DOB: {pt.get("dob","—")} &nbsp;·&nbsp; Sex: {pt.get("sex","—")} &nbsp;·&nbsp; ID: {pt.get("patient_id","—")}
                        </div>
                        {"<div style='font-size:13px; margin-top:6px;'>Dx: " + pt.get("diagnoses","") + "</div>" if pt.get("diagnoses") else ""}
                        {"<div style='font-size:13px; color:#666;'>Medications: " + pt.get("medications","") + "</div>" if pt.get("medications") else ""}
                    </div>
                    <div style='text-align:right; font-size:12px; color:#888;'>
                        {len(bm)} draws &nbsp;·&nbsp; {len(ev)} events
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Filters
        fc1, fc2, fc3 = st.columns([2,2,1])
        all_cats = sorted(set(
            cat.strip()
            for cats in bm["categories"].dropna()
            for cat in str(cats).split(",")
            if cat.strip()
        ))
        sel_cats = fc1.multiselect("Filter by biomarker category", all_cats, default=all_cats)
        sel_etypes = fc2.multiselect("Filter events by type", EVENT_TYPES, default=EVENT_TYPES)

        # Filter biomarkers
        if sel_cats:
            mask = bm["categories"].apply(lambda x: any(c in str(x) for c in sel_cats))
            bm_filtered = bm[mask].copy()
        else:
            bm_filtered = bm.copy()

        bm_filtered["date"] = pd.to_datetime(bm_filtered["date"])
        bm_filtered["value"] = pd.to_numeric(bm_filtered["value"], errors="coerce")
        bm_filtered = bm_filtered.dropna(subset=["value"])

        # Filter events
        ev_filtered = ev[ev["event_type"].isin(sel_etypes)].copy() if not ev.empty else ev.copy()

        # Group by unit
        units = bm_filtered["unit"].unique()

        for i, unit in enumerate(units):
            unit_df = bm_filtered[bm_filtered["unit"] == unit]
            markers = unit_df["biomarker"].unique()

            st.markdown(f'<div class="section-header">Unit: {unit}</div>', unsafe_allow_html=True)

            fig = go.Figure()

            # Biomarker lines
            for j, marker in enumerate(markers):
                mdf = unit_df[unit_df["biomarker"] == marker].sort_values("date")
                color = BIOMARKER_COLORS[j % len(BIOMARKER_COLORS)]

                ref_low  = pd.to_numeric(mdf["ref_low"], errors="coerce").iloc[0] if not mdf.empty else None
                ref_high = pd.to_numeric(mdf["ref_high"], errors="coerce").iloc[0] if not mdf.empty else None

                # Reference range shading
                if ref_low is not None and ref_high is not None and ref_high > 0:
                    fig.add_hrect(
                        y0=ref_low, y1=ref_high,
                        fillcolor=STONE, opacity=0.4,
                        layer="below", line_width=0,
                        annotation_text=f"Ref: {ref_low}–{ref_high}",
                        annotation_position="top right",
                        annotation_font_size=10,
                        annotation_font_color="#aaa"
                    )

                # Out of range coloring
                dot_colors = []
                for _, row in mdf.iterrows():
                    v = row["value"]
                    if ref_low is not None and ref_high is not None and ref_high > 0:
                        if v < ref_low or v > ref_high:
                            dot_colors.append(RUST)
                        else:
                            dot_colors.append(color)
                    else:
                        dot_colors.append(color)

                hover = [
                    f"<b>{marker}</b><br>Date: {row['date'].strftime('%b %d, %Y')}<br>Value: {row['value']} {unit}" +
                    (f"<br>Ref: {ref_low}–{ref_high}" if ref_low is not None and ref_high and ref_high > 0 else "") +
                    (f"<br><span style='color:{RUST}'>⚠ Out of range</span>" if (ref_low is not None and ref_high and ref_high > 0 and (row['value'] < ref_low or row['value'] > ref_high)) else "") +
                    (f"<br>Notes: {row['notes']}" if str(row.get('notes','')) not in ['','nan'] else "")
                    for _, row in mdf.iterrows()
                ]

                fig.add_trace(go.Scatter(
                    x=mdf["date"], y=mdf["value"],
                    mode="lines+markers",
                    name=marker,
                    line=dict(color=color, width=2),
                    marker=dict(color=dot_colors, size=8, line=dict(width=1, color="white")),
                    hovertemplate="%{customdata}<extra></extra>",
                    customdata=hover
                ))

            # Clinical event overlays
            if not ev_filtered.empty:
                for _, ev_row in ev_filtered.iterrows():
                    ecolor = EVENT_COLORS.get(ev_row["event_type"], SAND)
                    estart = pd.to_datetime(ev_row["start_date"])
                    eend_raw = str(ev_row.get("end_date","")).strip()
                    has_end = eend_raw not in ["", "nan", "None"]

                    if has_end:
                        eend = pd.to_datetime(eend_raw)
                        fig.add_vrect(
                            x0=estart, x1=eend,
                            fillcolor=ecolor, opacity=0.12,
                            layer="below", line_width=1,
                            line_color=ecolor,
                            annotation_text=ev_row["description"],
                            annotation_position="top left",
                            annotation_font_size=10,
                            annotation_font_color=ecolor
                        )
                    else:
                        fig.add_vline(
                            x=estart,
                            line_dash="dash",
                            line_color=ecolor,
                            line_width=1.5,
                            annotation_text=ev_row["description"],
                            annotation_position="top",
                            annotation_font_size=10,
                            annotation_font_color=ecolor
                        )

            fig.update_layout(
                height=320,
                margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor="white",
                plot_bgcolor="white",
                font=dict(family="DM Sans", color=OFFBLK),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                xaxis=dict(showgrid=True, gridcolor="#f0ece4", zeroline=False),
                yaxis=dict(showgrid=True, gridcolor="#f0ece4", zeroline=False,
                           title=unit)
            )

            st.plotly_chart(fig, use_container_width=True)

        # Event legend
        if not ev_filtered.empty:
            st.markdown('<div class="section-header" style="margin-top:1rem;">Clinical events</div>', unsafe_allow_html=True)
            for _, row in ev_filtered.iterrows():
                color = EVENT_COLORS.get(row["event_type"], SAND)
                eend_raw = str(row.get("end_date","")).strip()
                has_end = eend_raw not in ["", "nan", "None"]
                date_str = row["start_date"]
                if has_end:
                    date_str += f" → {eend_raw}"
                st.markdown(f"""
                <div style='display:flex; align-items:center; gap:8px; margin-bottom:6px;'>
                    <span style='width:12px; height:12px; border-radius:2px; background:{color}; display:inline-block;'></span>
                    <span class='event-badge tag-{row["event_type"]}'>{row["event_type"]}</span>
                    <span style='font-size:13px;'>{row["description"]}</span>
                    <span style='font-size:12px; color:#aaa;'>{date_str}</span>
                </div>
                """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# PAGE: TRENDS & INSIGHTS
# ════════════════════════════════════════════════════════════════════
elif page == "Trends & Insights":
    st.markdown("## Trends & Insights")
    st.caption("Pattern exploration — no AI, purely query-based.")

    bm = st.session_state.biomarkers
    ev = st.session_state.events

    if bm.empty:
        st.markdown('<div class="upload-hint">No data yet. Go to Data Entry to add biomarker values.</div>', unsafe_allow_html=True)
    else:
        bm = bm.copy()
        bm["date"]  = pd.to_datetime(bm["date"])
        bm["value"] = pd.to_numeric(bm["value"], errors="coerce")
        bm["ref_low"]  = pd.to_numeric(bm["ref_low"], errors="coerce")
        bm["ref_high"] = pd.to_numeric(bm["ref_high"], errors="coerce")

        tab1, tab2, tab3 = st.tabs([
            "Out of range during event",
            "% change between dates",
            "Before / after event"
        ])

        # ── Out of range during event ────────────────────────────────
        with tab1:
            if ev.empty:
                st.info("No clinical events entered yet.")
            else:
                ev2 = ev.copy()
                ev2["start_date"] = pd.to_datetime(ev2["start_date"])
                ev2["end_date_parsed"] = pd.to_datetime(ev2["end_date"], errors="coerce")

                event_labels = [
                    f"{r['description']} ({r['start_date'].strftime('%Y-%m-%d')})"
                    for _, r in ev2.iterrows()
                ]
                sel_ev = st.selectbox("Select a clinical event", event_labels)
                sel_idx = event_labels.index(sel_ev)
                sel_row = ev2.iloc[sel_idx]

                estart = sel_row["start_date"]
                eend   = sel_row["end_date_parsed"] if pd.notna(sel_row["end_date_parsed"]) else estart

                window = bm[(bm["date"] >= estart) & (bm["date"] <= eend)]

                oor = window[
                    ((window["ref_low"].notna()) & (window["value"] < window["ref_low"])) |
                    ((window["ref_high"].notna()) & (window["ref_high"] > 0) & (window["value"] > window["ref_high"]))
                ]

                st.markdown(f"""
                <div style='background:white; border-radius:10px; padding:1rem; border:1px solid {SAND}; margin-bottom:1rem;'>
                    <span class='event-badge tag-{sel_row["event_type"]}'>{sel_row["event_type"]}</span>
                    <strong>{sel_row["description"]}</strong>
                    <span style='font-size:12px; color:#aaa; margin-left:8px;'>{estart.strftime("%Y-%m-%d")} — {eend.strftime("%Y-%m-%d")}</span>
                </div>
                """, unsafe_allow_html=True)

                if oor.empty:
                    st.success("No out-of-range biomarker values during this event.")
                else:
                    st.markdown(f"<div style='color:{RUST}; font-weight:600; margin-bottom:8px;'>⚠ {len(oor)} out-of-range result(s)</div>", unsafe_allow_html=True)
                    display = oor[["date","biomarker","value","unit","ref_low","ref_high","notes"]].copy()
                    display["date"] = display["date"].dt.strftime("%Y-%m-%d")
                    display["ref range"] = display.apply(lambda r: f"{r['ref_low']}–{r['ref_high']}" if pd.notna(r['ref_low']) else "—", axis=1)
                    display["direction"] = oor.apply(lambda r: "↑ High" if pd.notna(r["ref_high"]) and r["ref_high"] > 0 and r["value"] > r["ref_high"] else "↓ Low", axis=1)
                    st.dataframe(display[["date","biomarker","value","unit","ref range","direction","notes"]], use_container_width=True)

        # ── % change between dates ───────────────────────────────────
        with tab2:
            all_markers = sorted(bm["biomarker"].unique())
            sel_marker = st.selectbox("Select biomarker", all_markers)
            mdf = bm[bm["biomarker"] == sel_marker].sort_values("date")

            c1, c2, c3 = st.columns(3)
            pct_thresh = c1.number_input("Show changes greater than (%)", value=20, step=5)
            date1 = c2.date_input("From date", value=mdf["date"].min().date() if not mdf.empty else date.today())
            date2 = c3.date_input("To date", value=mdf["date"].max().date() if not mdf.empty else date.today())

            d1 = pd.Timestamp(date1)
            d2 = pd.Timestamp(date2)

            v1_rows = mdf[mdf["date"] <= d1]
            v2_rows = mdf[mdf["date"] >= d2]

            if v1_rows.empty or v2_rows.empty:
                st.info("No draws found near the selected dates.")
            else:
                v1_row = v1_rows.iloc[-1]
                v2_row = v2_rows.iloc[0]
                v1, v2 = v1_row["value"], v2_row["value"]
                pct = ((v2 - v1) / v1 * 100) if v1 != 0 else 0

                days_before = (d1 - v1_row["date"]).days
                days_after  = (v2_row["date"] - d2).days

                col1, col2, col3 = st.columns(3)
                col1.markdown(f'<div class="metric-card"><div class="metric-label">Value at start</div><div class="metric-value">{v1} {v1_row["unit"]}</div><div style="font-size:11px;color:#aaa;">{v1_row["date"].strftime("%b %d, %Y")}{f" ({days_before}d before)" if days_before > 0 else ""}</div></div>', unsafe_allow_html=True)
                col2.markdown(f'<div class="metric-card"><div class="metric-label">Value at end</div><div class="metric-value">{v2} {v2_row["unit"]}</div><div style="font-size:11px;color:#aaa;">{v2_row["date"].strftime("%b %d, %Y")}{f" ({days_after}d after)" if days_after > 0 else ""}</div></div>', unsafe_allow_html=True)
                pct_color = RUST if abs(pct) >= pct_thresh else MOSS
                col3.markdown(f'<div class="metric-card"><div class="metric-label">% change</div><div class="metric-value" style="color:{pct_color};">{pct:+.1f}%</div><div style="font-size:11px;color:#aaa;">threshold: ±{pct_thresh}%</div></div>', unsafe_allow_html=True)

        # ── Before / after event ─────────────────────────────────────
        with tab3:
            if ev.empty:
                st.info("No clinical events entered yet.")
            else:
                ev3 = ev.copy()
                ev3["start_date"] = pd.to_datetime(ev3["start_date"])
                event_labels3 = [f"{r['description']} ({r['start_date'].strftime('%Y-%m-%d')})" for _, r in ev3.iterrows()]
                sel_ev3   = st.selectbox("Select event", event_labels3, key="ba_ev")
                sel_idx3  = event_labels3.index(sel_ev3)
                edate3    = ev3.iloc[sel_idx3]["start_date"]
                window_days = st.slider("Days before/after event", 7, 90, 30)
                sel_marker3 = st.selectbox("Biomarker", sorted(bm["biomarker"].unique()), key="ba_bm")

                mdf3 = bm[bm["biomarker"] == sel_marker3].sort_values("date")
                before = mdf3[mdf3["date"] < edate3].tail(3)
                after  = mdf3[mdf3["date"] >= edate3].head(3)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Before** _{sel_ev3}_")
                    if before.empty:
                        st.info("No draws before this event.")
                    else:
                        disp = before[["date","value","unit","notes"]].copy()
                        disp["date"] = disp["date"].dt.strftime("%Y-%m-%d")
                        disp["days before event"] = before["date"].apply(lambda d: (edate3 - d).days)
                        st.dataframe(disp, use_container_width=True)

                with c2:
                    st.markdown(f"**After** _{sel_ev3}_")
                    if after.empty:
                        st.info("No draws after this event.")
                    else:
                        disp = after[["date","value","unit","notes"]].copy()
                        disp["date"] = disp["date"].dt.strftime("%Y-%m-%d")
                        disp["days after event"] = after["date"].apply(lambda d: (d - edate3).days)
                        st.dataframe(disp, use_container_width=True)
