# app.py
import os
import random
from datetime import datetime, date, time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Ladeøkter – Ampere vs Tid", layout="wide")

st.title("Ladeøkter (Ampere vs tid på døgnet)")
st.caption("Last opp én eller flere CSV/XLSX-filer og velg dato for å plotte.")

# --- SIDEBAR: opplasting og valg ---
with st.sidebar:
    st.header("Innstillinger")
    files = st.file_uploader(
        "Velg én eller flere filer",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
    )
    st.markdown("**Valg av dato**")

# Relevante kolonner
KOLONNER = [
    "start time", "end time", "charged energy (kwh)", "peak power (kw)",
    "average power (kw)", "soc start (%)", "soc stop (%)", "peak amp (a)",
    "average amp (a)"
]

def _read_any(file):
    # Les CSV eller Excel basert på filnavn/innhold
    name = file.name.lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(file)
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            return pd.read_excel(file)
        else:
            # Fallback: prøv Excel først, deretter CSV
            try:
                file.seek(0)
                return pd.read_excel(file)
            except Exception:
                file.seek(0)
                return pd.read_csv(file)
    finally:
        # Sørg for at stream-posisjon er på start for evt. ny lesing
        try:
            file.seek(0)
        except Exception:
            pass

def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
                  .str.lower()
                  .str.replace(r"[^\x00-\x7F]+", "", regex=True)
    )
    return df

def _concat_valid(dfs):
    valids = []
    msgs = []
    for i, df in enumerate(dfs, start=1):
        df = _clean_columns(df)
        missing = [k for k in KOLONNER if k not in df.columns]
        if missing:
            msgs.append(f"❌ Fil {i}: mangler kolonner: {missing}")
            continue
        valids.append(df[KOLONNER].copy())
        msgs.append(f"✅ Fil {i}: {len(df)} rader OK")
    return (pd.concat(valids, ignore_index=True) if valids else None), msgs

if not files:
    st.info("👆 Last opp CSV/XLSX-filer for å komme i gang.")
    st.stop()

raw_dfs = []
for f in files:
    try:
        raw_dfs.append(_read_any(f))
    except Exception as e:
        st.error(f"💥 Feil ved lesing av **{f.name}**: {e}")

df, status_msgs = _concat_valid(raw_dfs)
with st.expander("Importlogg"):
    for m in status_msgs:
        st.write(m)

if df is None or df.empty:
    st.error("🚫 Ingen gyldige filer/kolonner ble funnet.")
    st.stop()

# Konverter typer
df["start time"] = pd.to_datetime(df["start time"], errors="coerce")
df["end time"] = pd.to_datetime(df["end time"], errors="coerce")
for col in ["average amp (a)", "peak amp (a)"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Rens
df = df.dropna(subset=["start time", "end time", "average amp (a)", "peak amp (a)"])
if df.empty:
    st.error("🚫 Alle rader hadde mangler etter rensing.")
    st.stop()

# Tilgjengelige datoer
available_dates = sorted(pd.Series(df["start time"].dt.date.unique()).dropna())
if not available_dates:
    st.error("🚫 Fant ingen datoer i dataene.")
    st.stop()

# Dato-widget: bruker tilgjengelige datoer som gyldige valg
col1, col2 = st.columns([1,1])
with col1:
    min_d, max_d = available_dates[0], available_dates[-1]
    st.write(f"Tilgjengelig datoperiode: **{min_d.strftime('%d.%m.%Y')} – {max_d.strftime('%d.%m.%Y')}**")

with col2:
    default_date = random.choice(available_dates)
    chosen_date = st.date_input(
        "Velg dato (fra tilgjengelige):",
        value=default_date,
        min_value=min_d,
        max_value=max_d,
        format="DD.MM.YYYY",
    )

# Filtrer valgt dato
df_dag = df[df["start time"].dt.date == chosen_date]
if df_dag.empty:
    st.warning(f"🚫 Ingen ladeøkter funnet for {chosen_date.strftime('%d.%m.%Y')}. Velg en annen dato.")
    st.stop()

# Konverter klokkeslett til fast dato (for x-akse)
def to_epoch_day_clock(ts: pd.Timestamp) -> datetime:
    return datetime(1970, 1, 1, ts.hour, ts.minute, ts.second)

df_dag = df_dag.copy()
df_dag["start_clock"] = df_dag["start time"].apply(to_epoch_day_clock)
df_dag["end_clock"] = df_dag["end time"].apply(to_epoch_day_clock)

# ---- PLOTT ----
fig = go.Figure()

for _, row in df_dag.iterrows():
    x0 = row["start_clock"]
    x1 = row["end_clock"]
    y0 = row["average amp (a)"]
    y1 = row["peak amp (a)"]

    hover = (
        f"Start: {row['start time'].strftime('%H:%M')}<br>"
        f"Slutt: {row['end time'].strftime('%H:%M')}<br>"
        f"SoC Start: {row['soc start (%)']}%<br>"
        f"SoC Slutt: {row['soc stop (%)']}%<br>"
        f"Avg Amp: {y0:.1f} A<br>"
        f"Peak Amp: {y1:.1f} A"
    )

    fig.add_trace(go.Scatter(
        x=[x0, x1, x1, x0, x0],
        y=[y0, y0, y1, y1, y0],
        fill="toself",
        mode="lines",
        line=dict(width=0),
        fillcolor="rgba(100, 149, 237, 0.5)",
        hoverinfo="text",
        text=hover,
        showlegend=False
    ))

fig.update_layout(
    title=f"Ladeøkter for {chosen_date.strftime('%d.%m.%Y')} (Ampere vs tid på døgnet)",
    xaxis=dict(
        title="Tid på døgnet",
        type="date",
        tickformat="%H:%M",
        tickmode="linear",
        dtick=3600000,  # 1 time i ms
    ),
    yaxis=dict(title="Ampere (A)"),
    height=650,
    margin=dict(l=40, r=20, t=60, b=40),
)

st.plotly_chart(fig, use_container_width=True)

# Litt nyttig tabellvisning
with st.expander("Se data for valgt dato"):
    show_cols = [
        "start time", "end time", "soc start (%)", "soc stop (%)",
        "average amp (a)", "peak amp (a)", "charged energy (kwh)"
    ]
    st.dataframe(df_dag[show_cols].sort_values("start time").reset_index(drop=True))
