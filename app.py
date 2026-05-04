import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date

EVENT_COLORS = {
    "infection":   "#d32f2f",
    "symptom":     "#e65100",
    "vaccination": "#2e7d32",
    "medication":  "#1565c0",
    "other":       "#555555",
}
BIOMARKER_COLORS = [
    "#1565c0","#2e7d32","#d32f2f","#6a1099",
    "#e65100","#00695c","#4e342e","#37474f"
]
CATEGORIES  = ["Inflammatory","Neuro/CNS","Metabolic","Hematologic","Hormonal","Other"]
EVENT_TYPES = ["infection","symptom","vaccination","medication","other"]

st.set_page_config(page_title="BioChronika", page_icon="🧬", layout="wide")

st.markdown("""
<style>
* { font-family: Arial, sans-serif !important; }
html, body, [class*="css"] { background: #fff; color: #111; }
.main { background: #fff; }
section[data-testid="stSidebar"] { background: #fafafa !important; border-right: 1px solid #ddd; }
section[data-testid="stSidebar"] * { color: #111 !important; }
h1,h2,h3 { color: #111; font-weight: 600; }
.stButton > button { background: #222; color: #fff; border: none; border-radius: 4px; padding: 0.4rem 1rem; }
.stButton > button:hover { background: #444; color: #fff; }
.card { background: #f7f7f7; border: 1px solid #ddd; border-radius: 6px; padding: 0.9rem 1.1rem; margin-bottom: 0.6rem; }
.sec-hdr { font-size: 13px; font-weight: 600; color: #333; border-bottom: 1px solid #ddd; padding-bottom: 4px; margin-bottom: 0.6rem; }
.upload-hint { background: #fafafa; border: 1px dashed #ccc; border-radius: 6px; padding: 1rem; text-align: center; color: #999; font-size: 13px; margin-bottom: 0.6rem; }
.badge { display:inline-block; padding: 1px 7px; border-radius: 3px; font-size: 11px; font-weight: 600; margin-right: 4px; }
.b-infection   { background:#fdecea; color:#c62828; }
.b-symptom     { background:#fff3e0; color:#bf360c; }
.b-vaccination { background:#e8f5e9; color:#1b5e20; }
.b-medication  { background:#e3f2fd; color:#0d47a1; }
.b-other       { background:#f5f5f5; color:#444;    }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────────────
def init():
    if "patient" not in st.session_state:
        st.session_state.patient = {}
    if "bm" not in st.session_state:
        st.session_state.bm = pd.DataFrame(columns=[
            "date","biomarker","value","unit","categories","ref_low","ref_high","lab","notes"])
    if "ev" not in st.session_state:
        st.session_state.ev = pd.DataFrame(columns=[
            "start_date","end_date","event_type","description","notes"])
init()

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### BioChronika")
    st.caption("Biomarker & Clinical Event Overlay")
    st.markdown("---")
    page = st.radio("Navigate", ["Timeline","Data Entry","Trends & Insights"])
    st.markdown("---")
    p = st.session_state.patient
    if p:
        st.markdown(f"**{p.get('name','—')}**")
        st.caption(f"{p.get('dob','')} · {p.get('sex','')}")
    st.markdown(f"Draws: **{len(st.session_state.bm)}** &nbsp; Events: **{len(st.session_state.ev)}**",
                unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# DATA ENTRY
# ════════════════════════════════════════════════════════════════════
if page == "Data Entry":
    st.markdown("## Data Entry")

    t1, t2, t3 = st.tabs(["Patient Profile","Biomarker Values","Clinical Events"])

    with t1:
        st.markdown('<div class="sec-hdr">Patient profile</div>', unsafe_allow_html=True)
        st.markdown('<div class="upload-hint">Upload a patient CSV or fill in manually below<br><small>Columns: name, patient_id, dob, sex, diagnoses, medications, background</small></div>', unsafe_allow_html=True)
        f = st.file_uploader("Patient CSV", type="csv", key="up_pt", label_visibility="collapsed")
        if f:
            df = pd.read_csv(f)
            df.columns = [c.lower().strip().replace(" ","_") for c in df.columns]
            st.session_state.patient = {k: str(v) for k,v in df.iloc[0].to_dict().items()}
            st.success("Patient loaded!")

        p = st.session_state.patient
        with st.form("pt_form"):
            c1,c2 = st.columns(2)
            nm  = c1.text_input("Name / alias", value=p.get("name",""))
            pid = c2.text_input("Patient ID",   value=p.get("patient_id",""))
            db  = c1.text_input("Date of birth (YYYY-MM-DD)", value=p.get("dob",""))
            sex_opts = ["Female","Male","Other"]
            sx  = c2.selectbox("Sex", sex_opts,
                               index=sex_opts.index(p.get("sex","Female")) if p.get("sex") in sex_opts else 0)
            dx  = st.text_area("Major diagnoses",   value=p.get("diagnoses",""),   height=70)
            mx  = st.text_area("Active medications", value=p.get("medications",""), height=70)
            nx  = st.text_area("Background notes",  value=p.get("background",""),  height=70)
            if st.form_submit_button("Save profile"):
                st.session_state.patient = {"name":nm,"patient_id":pid,"dob":db,"sex":sx,
                                            "diagnoses":dx,"medications":mx,"background":nx}
                st.success("Saved!")

    with t2:
        st.markdown('<div class="sec-hdr">Biomarker values</div>', unsafe_allow_html=True)
        st.markdown('<div class="upload-hint">Upload a CSV<br><small>Columns: date, biomarker, value, unit, categories, ref_low, ref_high, lab, notes</small></div>', unsafe_allow_html=True)
        f2 = st.file_uploader("Biomarker CSV", type="csv", key="up_bm", label_visibility="collapsed")
        if f2:
            df2 = pd.read_csv(f2)
            df2.columns = [c.lower().strip() for c in df2.columns]
            for col in ["date","biomarker","value","unit","categories","ref_low","ref_high","lab","notes"]:
                if col not in df2.columns: df2[col] = ""
            st.session_state.bm = pd.concat([st.session_state.bm, df2], ignore_index=True)
            st.success(f"Loaded {len(df2)} entries!")

        with st.expander("Add single entry"):
            with st.form("bm_form"):
                c1,c2,c3 = st.columns(3)
                bd = c1.date_input("Date", value=date.today())
                bn = c2.text_input("Biomarker name")
                bv = c3.number_input("Value", step=0.01)
                c1b,c2b,c3b = st.columns(3)
                bu = c1b.text_input("Unit")
                bc = c2b.multiselect("Categories", CATEGORIES)
                bl = c3b.text_input("Lab (optional)")
                c1c,c2c,c3c = st.columns(3)
                rl = c1c.number_input("Ref low",  value=0.0, step=0.01)
                rh = c2c.number_input("Ref high", value=0.0, step=0.01)
                bn2 = c3c.text_input("Notes")
                if st.form_submit_button("Add"):
                    row = pd.DataFrame([{"date":str(bd),"biomarker":bn,"value":bv,"unit":bu,
                                         "categories":", ".join(bc),"ref_low":rl,"ref_high":rh,
                                         "lab":bl,"notes":bn2}])
                    st.session_state.bm = pd.concat([st.session_state.bm, row], ignore_index=True)
                    st.success("Added!")

        if not st.session_state.bm.empty:
            st.caption(f"{len(st.session_state.bm)} entries")
            disp = st.session_state.bm.copy()
            disp["value"] = disp["value"].astype(str)
            st.dataframe(disp, use_container_width=True)
            if st.button("Clear biomarker data"):
                st.session_state.bm = pd.DataFrame(columns=["date","biomarker","value","unit","categories","ref_low","ref_high","lab","notes"])
                st.rerun()

    with t3:
        st.markdown('<div class="sec-hdr">Clinical events</div>', unsafe_allow_html=True)
        st.markdown('<div class="upload-hint">Upload a CSV<br><small>Columns: start_date, end_date, event_type, description, notes</small></div>', unsafe_allow_html=True)
        f3 = st.file_uploader("Events CSV", type="csv", key="up_ev", label_visibility="collapsed")
        if f3:
            df3 = pd.read_csv(f3)
            df3.columns = [c.lower().strip() for c in df3.columns]
            for col in ["start_date","end_date","event_type","description","notes"]:
                if col not in df3.columns: df3[col] = ""
            st.session_state.ev = pd.concat([st.session_state.ev, df3], ignore_index=True)
            st.success(f"Loaded {len(df3)} events!")

        with st.expander("Add single event"):
            with st.form("ev_form"):
                c1,c2 = st.columns(2)
                es = c1.date_input("Start date", value=date.today())
                ee = c2.date_input("End date (if known)", value=date.today())
                c3,c4 = st.columns(2)
                et = c3.selectbox("Event type", EVENT_TYPES)
                ed = c4.text_input("Description")
                en = st.text_input("Notes (optional)")
                has_end = st.checkbox("Has known end date")
                if st.form_submit_button("Add"):
                    row = pd.DataFrame([{"start_date":str(es),
                                         "end_date":str(ee) if has_end else "",
                                         "event_type":et,"description":ed,"notes":en}])
                    st.session_state.ev = pd.concat([st.session_state.ev, row], ignore_index=True)
                    st.success("Added!")

        if not st.session_state.ev.empty:
            st.caption(f"{len(st.session_state.ev)} events")
            st.dataframe(st.session_state.ev, use_container_width=True)
            if st.button("Clear event data"):
                st.session_state.ev = pd.DataFrame(columns=["start_date","end_date","event_type","description","notes"])
                st.rerun()

# ════════════════════════════════════════════════════════════════════
# TIMELINE
# ════════════════════════════════════════════════════════════════════
elif page == "Timeline":
    st.markdown("## Timeline")

    bm = st.session_state.bm
    ev = st.session_state.ev
    pt = st.session_state.patient

    if bm.empty:
        st.markdown('<div class="upload-hint">No data yet — go to Data Entry to upload biomarker values and clinical events.</div>', unsafe_allow_html=True)
    else:
        if pt:
            st.markdown(f"""
            <div class="card">
              <strong style="font-size:17px;">{pt.get('name','—')}</strong>
              <span style="color:#888;font-size:13px;margin-left:12px;">
                DOB: {pt.get('dob','—')} &nbsp;·&nbsp; Sex: {pt.get('sex','—')} &nbsp;·&nbsp; ID: {pt.get('patient_id','—')}
              </span><br>
              {"<span style='font-size:13px;'>Dx: " + pt.get('diagnoses','') + "</span><br>" if pt.get('diagnoses') else ""}
              {"<span style='font-size:13px;color:#666;'>Meds: " + pt.get('medications','') + "</span>" if pt.get('medications') else ""}
            </div>
            """, unsafe_allow_html=True)

        fc1, fc2 = st.columns(2)
        all_cats = sorted(set(
            c.strip() for cats in bm["categories"].dropna()
            for c in str(cats).split(",") if c.strip()
        ))
        sel_cats   = fc1.multiselect("Filter by biomarker category", all_cats, default=all_cats)
        sel_etypes = fc2.multiselect("Filter events by type", EVENT_TYPES, default=EVENT_TYPES)

        bm2 = bm.copy()
        bm2["date"]  = pd.to_datetime(bm2["date"], errors="coerce")
        bm2["value"] = pd.to_numeric(bm2["value"], errors="coerce")
        bm2 = bm2.dropna(subset=["date","value"])
        if sel_cats:
            bm2 = bm2[bm2["categories"].apply(lambda x: any(c in str(x) for c in sel_cats))]

        ev2 = ev[ev["event_type"].isin(sel_etypes)].copy() if not ev.empty else ev.copy()

        for unit in bm2["unit"].unique():
            udf     = bm2[bm2["unit"] == unit]
            markers = udf["biomarker"].unique()
            st.markdown(f'<div class="sec-hdr">Unit: {unit}</div>', unsafe_allow_html=True)
            fig = go.Figure()

            for j, marker in enumerate(markers):
                mdf   = udf[udf["biomarker"] == marker].sort_values("date")
                color = BIOMARKER_COLORS[j % len(BIOMARKER_COLORS)]
                rl_s  = pd.to_numeric(mdf["ref_low"],  errors="coerce").dropna()
                rh_s  = pd.to_numeric(mdf["ref_high"], errors="coerce").dropna()
                ref_low  = float(rl_s.iloc[0]) if not rl_s.empty else None
                ref_high = float(rh_s.iloc[0]) if not rh_s.empty else None

                if ref_low is not None and ref_high is not None and ref_high > 0:
                    fig.add_hrect(y0=ref_low, y1=ref_high,
                                  fillcolor="#f0f0f0", opacity=0.5, layer="below", line_width=0)

                dot_colors, hover = [], []
                for _, row in mdf.iterrows():
                    v   = row["value"]
                    oor = (ref_low is not None and ref_high is not None
                           and ref_high > 0 and (v < ref_low or v > ref_high))
                    dot_colors.append("#c0392b" if oor else color)
                    h = (f"<b>{marker}</b><br>"
                         f"Date: {row['date'].strftime('%b %d, %Y')}<br>"
                         f"Value: {v} {unit}")
                    if ref_low is not None and ref_high and ref_high > 0:
                        h += f"<br>Ref: {ref_low}–{ref_high}"
                    if oor:
                        h += "<br><b style='color:#c0392b'>Out of range</b>"
                    if str(row.get("notes","")) not in ["","nan"]:
                        h += f"<br>{row['notes']}"
                    hover.append(h)

                fig.add_trace(go.Scatter(
                    x=mdf["date"], y=mdf["value"],
                    mode="lines+markers", name=marker,
                    line=dict(color=color, width=2),
                    marker=dict(color=dot_colors, size=8, line=dict(width=1, color="white")),
                    hovertemplate="%{customdata}<extra></extra>",
                    customdata=hover
                ))

            if not ev2.empty:
                for _, er in ev2.iterrows():
                    ec      = EVENT_COLORS.get(er["event_type"], "#888")
                    es_str  = str(er["start_date"])[:10]
                    end_raw = str(er.get("end_date","")).strip()
                    has_end = end_raw not in ["","nan","None"]
                    desc    = str(er.get("description",""))

                    if has_end:
                        fig.add_shape(type="rect",
                                      x0=es_str, x1=end_raw[:10], y0=0, y1=1,
                                      xref="x", yref="paper",
                                      fillcolor=ec, opacity=0.10, layer="below",
                                      line=dict(color=ec, width=1))
                    else:
                        fig.add_shape(type="line",
                                      x0=es_str, x1=es_str, y0=0, y1=1,
                                      xref="x", yref="paper",
                                      line=dict(color=ec, width=1.5, dash="dash"))
                    fig.add_annotation(x=es_str, y=0.98,
                                       xref="x", yref="paper",
                                       text=desc, showarrow=False,
                                       font=dict(size=10, color=ec),
                                       xanchor="left", yanchor="top",
                                       bgcolor="rgba(255,255,255,0.8)")

            fig.update_layout(
                height=300, margin=dict(l=0,r=0,t=30,b=0),
                paper_bgcolor="white", plot_bgcolor="white",
                font=dict(family="-apple-system,sans-serif", color="#1a1a1a"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                xaxis=dict(showgrid=True, gridcolor="#f0f0f0", zeroline=False),
                yaxis=dict(showgrid=True, gridcolor="#f0f0f0", zeroline=False, title=unit)
            )
            st.plotly_chart(fig, use_container_width=True)

        if not ev2.empty:
            st.markdown('<div class="sec-hdr" style="margin-top:1rem;">Clinical events</div>', unsafe_allow_html=True)
            for _, row in ev2.iterrows():
                ec      = EVENT_COLORS.get(row["event_type"], "#888")
                end_raw = str(row.get("end_date","")).strip()
                has_end = end_raw not in ["","nan","None"]
                ds      = str(row["start_date"])[:10]
                if has_end:
                    ds += f" → {end_raw[:10]}"
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
                  <span style="width:10px;height:10px;border-radius:2px;background:{ec};display:inline-block;"></span>
                  <span class="badge b-{row['event_type']}">{row['event_type']}</span>
                  <span style="font-size:13px;">{row['description']}</span>
                  <span style="font-size:12px;color:#aaa;">{ds}</span>
                </div>
                """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# TRENDS & INSIGHTS
# ════════════════════════════════════════════════════════════════════
elif page == "Trends & Insights":
    st.markdown("## Trends & Insights")
    st.caption("Pattern exploration — no AI, purely query-based.")

    bm = st.session_state.bm.copy()
    ev = st.session_state.ev.copy()

    if bm.empty:
        st.markdown('<div class="upload-hint">No data yet — go to Data Entry first.</div>', unsafe_allow_html=True)
    else:
        bm["date"]     = pd.to_datetime(bm["date"],     errors="coerce")
        bm["value"]    = pd.to_numeric(bm["value"],     errors="coerce")
        bm["ref_low"]  = pd.to_numeric(bm["ref_low"],   errors="coerce")
        bm["ref_high"] = pd.to_numeric(bm["ref_high"],  errors="coerce")
        bm = bm.dropna(subset=["date","value"])

        t1, t2, t3 = st.tabs(["Out of range during event","% change between dates","Before / after event"])

        with t1:
            if ev.empty:
                st.info("No clinical events entered yet.")
            else:
                ev_t1 = ev.copy()
                ev_t1["start_date"] = pd.to_datetime(ev_t1["start_date"], errors="coerce")
                ev_t1["end_date"]   = pd.to_datetime(ev_t1["end_date"],   errors="coerce")
                ev_t1 = ev_t1.dropna(subset=["start_date"])

                labels = [f"{r['description']} ({r['start_date'].strftime('%Y-%m-%d')})" for _,r in ev_t1.iterrows()]
                sel = st.selectbox("Select clinical event", labels)
                er  = ev_t1.iloc[labels.index(sel)]
                es  = er["start_date"]
                ee  = er["end_date"] if pd.notna(er["end_date"]) else es

                window = bm[(bm["date"] >= es) & (bm["date"] <= ee)]
                oor = window[
                    ((window["ref_low"].notna())  & (window["value"] < window["ref_low"])) |
                    ((window["ref_high"].notna()) & (window["ref_high"] > 0) & (window["value"] > window["ref_high"]))
                ]

                st.markdown(f"""
                <div class="card">
                  <span class="badge b-{er['event_type']}">{er['event_type']}</span>
                  <strong>{er['description']}</strong>
                  <span style="font-size:12px;color:#aaa;margin-left:8px;">{es.strftime('%Y-%m-%d')} — {ee.strftime('%Y-%m-%d')}</span>
                </div>
                """, unsafe_allow_html=True)

                if oor.empty:
                    st.success("No out-of-range values during this event.")
                else:
                    st.markdown(f"<div style='color:#c0392b;font-weight:600;margin-bottom:8px;'>⚠ {len(oor)} out-of-range result(s)</div>", unsafe_allow_html=True)
                    disp = oor[["date","biomarker","value","unit","ref_low","ref_high","notes"]].copy()
                    disp["date"]      = disp["date"].dt.strftime("%Y-%m-%d")
                    disp["ref range"] = disp.apply(lambda r: f"{r['ref_low']}–{r['ref_high']}" if pd.notna(r["ref_low"]) else "—", axis=1)
                    disp["direction"] = oor.apply(lambda r: "↑ High" if (pd.notna(r["ref_high"]) and r["ref_high"]>0 and r["value"]>r["ref_high"]) else "↓ Low", axis=1)
                    st.dataframe(disp[["date","biomarker","value","unit","ref range","direction","notes"]], use_container_width=True)

        with t2:
            all_markers = sorted(bm["biomarker"].dropna().unique().tolist())
            if not all_markers:
                st.info("No biomarker data.")
            else:
                sel_m = st.selectbox("Select biomarker", all_markers)
                mdf   = bm[bm["biomarker"] == sel_m].sort_values("date").dropna(subset=["date"])

                pct_thresh = st.number_input("Flag changes greater than (%)", value=20, step=5)

                if mdf.empty:
                    st.info("No data for this biomarker.")
                else:
                    min_d = mdf["date"].min().date()
                    max_d = mdf["date"].max().date()
                    c1,c2 = st.columns(2)
                    date1 = c1.date_input("From date", value=min_d, min_value=min_d, max_value=max_d)
                    date2 = c2.date_input("To date",   value=max_d, min_value=min_d, max_value=max_d)

                    d1 = pd.Timestamp(date1)
                    d2 = pd.Timestamp(date2)
                    v1_rows = mdf[mdf["date"] <= d1]
                    v2_rows = mdf[mdf["date"] >= d2]

                    if v1_rows.empty or v2_rows.empty:
                        st.info("No draws found near the selected dates.")
                    else:
                        v1r = v1_rows.iloc[-1]
                        v2r = v2_rows.iloc[0]
                        v1, v2 = float(v1r["value"]), float(v2r["value"])
                        pct = ((v2 - v1) / v1 * 100) if v1 != 0 else 0
                        days_before = (d1 - v1r["date"]).days
                        days_after  = (v2r["date"] - d2).days
                        unit = str(v1r.get("unit",""))
                        pct_color = "#c0392b" if abs(pct) >= pct_thresh else "#27ae60"

                        ca,cb,cc = st.columns(3)
                        ca.markdown(f'<div class="card"><div style="font-size:11px;color:#888;text-transform:uppercase;margin-bottom:4px;">Value at start</div><div style="font-size:22px;font-weight:600;">{v1} {unit}</div><div style="font-size:11px;color:#aaa;">{v1r["date"].strftime("%b %d, %Y")}{f" ({days_before}d before)" if days_before>0 else ""}</div></div>', unsafe_allow_html=True)
                        cb.markdown(f'<div class="card"><div style="font-size:11px;color:#888;text-transform:uppercase;margin-bottom:4px;">Value at end</div><div style="font-size:22px;font-weight:600;">{v2} {unit}</div><div style="font-size:11px;color:#aaa;">{v2r["date"].strftime("%b %d, %Y")}{f" ({days_after}d after)" if days_after>0 else ""}</div></div>', unsafe_allow_html=True)
                        cc.markdown(f'<div class="card"><div style="font-size:11px;color:#888;text-transform:uppercase;margin-bottom:4px;">% change</div><div style="font-size:22px;font-weight:600;color:{pct_color};">{pct:+.1f}%</div><div style="font-size:11px;color:#aaa;">threshold: ±{pct_thresh}%</div></div>', unsafe_allow_html=True)

        with t3:
            if ev.empty:
                st.info("No clinical events entered yet.")
            else:
                ev_t3 = ev.copy()
                ev_t3["start_date"] = pd.to_datetime(ev_t3["start_date"], errors="coerce")
                ev_t3 = ev_t3.dropna(subset=["start_date"])

                labels3 = [f"{r['description']} ({r['start_date'].strftime('%Y-%m-%d')})" for _,r in ev_t3.iterrows()]
                sel3    = st.selectbox("Select event", labels3, key="ba_ev")
                edate3  = ev_t3.iloc[labels3.index(sel3)]["start_date"]

                all_m3  = sorted(bm["biomarker"].dropna().unique().tolist())
                sel_m3  = st.selectbox("Biomarker", all_m3, key="ba_bm")
                mdf3    = bm[bm["biomarker"] == sel_m3].sort_values("date")
                before  = mdf3[mdf3["date"] < edate3].tail(3)
                after   = mdf3[mdf3["date"] >= edate3].head(3)

                c1,c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Before** — {sel3}")
                    if before.empty:
                        st.info("No draws before this event.")
                    else:
                        d = before[["date","value","unit","notes"]].copy()
                        d["date"] = d["date"].dt.strftime("%Y-%m-%d")
                        d["days before"] = before["date"].apply(lambda x: (edate3-x).days)
                        st.dataframe(d, use_container_width=True)
                with c2:
                    st.markdown(f"**After** — {sel3}")
                    if after.empty:
                        st.info("No draws after this event.")
                    else:
                        d = after[["date","value","unit","notes"]].copy()
                        d["date"] = d["date"].dt.strftime("%Y-%m-%d")
                        d["days after"] = after["date"].apply(lambda x: (x-edate3).days)
                        st.dataframe(d, use_container_width=True)
