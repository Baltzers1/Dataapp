# plotting by using ChargEye data

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

st.title("Power Data Analyzer")
st.write("Last opp flere Excel-filer, og få ut plott og summerte data!")

# 1. Filopplasting
uploaded_files = st.file_uploader("Last opp én eller flere Excel-filer", type="xlsx", accept_multiple_files=True)

def kombiner_excel_filer(uploaded_files):
    if not uploaded_files:
        st.warning("Ingen filer lastet opp.")
        return pd.DataFrame()
    kombinert_df = pd.DataFrame()
    for uploaded_file in uploaded_files:
        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            kombinert_df = pd.concat([kombinert_df, df], ignore_index=True)
        except Exception as e:
            st.error(f"Feil ved lesing av {uploaded_file.name}: {e}")
            return pd.DataFrame()
    return kombinert_df

def rens_data_for_plotting(df):
    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
    renset_df = df.fillna(0)
    return renset_df

def filter_summary_data(df):
    if 'Power [kW]' not in df.columns:
        st.error("Kolonnen 'Power [kW]' finnes ikke i dataene.")
        return pd.DataFrame()
    filtrert_df = df[df['Power [kW]'] != 0]
    return filtrert_df


def plot_power_data(data):
    dato_tids_kolonne = 'Timestamp'
    y_data_kolonne = 'Power [kW]'

    if dato_tids_kolonne not in data.columns or y_data_kolonne not in data.columns:
        st.error(f"Nødvendige kolonner ('{dato_tids_kolonne}' og '{y_data_kolonne}') finnes ikke i dataen.")
        return

    try:
        data[dato_tids_kolonne] = pd.to_datetime(data[dato_tids_kolonne], format='%d.%m.%Y %H:%M')
    except Exception as e:
        st.error(f"Feil ved konvertering av '{dato_tids_kolonne}': {e}")
        return

    data['Time'] = data[dato_tids_kolonne].dt.strftime('%H:%M')
    data['Date'] = data[dato_tids_kolonne].dt.date
    data = data.drop_duplicates(subset=['Time', 'Date'])
    data = data[data['Time'].str.match(r'^\d{2}:[0-5]0$')]

    pivot_table = data.pivot(index='Time', columns='Date', values=y_data_kolonne)

    effektfaktor = 0.8648
    pivot_table_med_tap = pivot_table / effektfaktor

    gjennomsnitt_med_tap = pivot_table_med_tap.mean(axis=1)
    gjennomsnitt_med_tap = np.maximum(gjennomsnitt_med_tap, 0)
    max_med_tap = pivot_table_med_tap.max(axis=1)

    fig = go.Figure()

    # Punktgraf for hver dag
    for column in pivot_table.columns:
        fig.add_trace(go.Scatter(
            x=pivot_table.index,
            y=pivot_table[column],
            mode='markers',
            name=str(column),
            marker=dict(size=4),
            opacity=0.5,
            showlegend=False,
            hovertemplate='%{x}<br>%{y:.0f} kW<extra></extra>'
        ))

    # Linje for gjennomsnitt
    fig.add_trace(go.Scatter(
        x=gjennomsnitt_med_tap.index,
        y=gjennomsnitt_med_tap.values,
        mode='lines',
        name='Average power',
        line=dict(width=3, color='red'),
        hovertemplate='%{x}<br>%{y:.0f} kW<extra></extra>'
    ))

    # Linje for maks
    fig.add_trace(go.Scatter(
        x=max_med_tap.index,
        y=max_med_tap.values,
        mode='lines',
        name='Max Total Power',
        line=dict(width=2, dash='dash', color='blue'),
        hovertemplate='%{x}<br>%{y:.0f} kW<extra></extra>'
    ))

    # Oppsett
    fig.update_layout(
        title="Power with loss over 24h",
        xaxis_title="Time of day (hh:mm)",
        yaxis_title="Power [kW]",
        xaxis=dict(tickmode='array', tickvals=pivot_table.index[::6], tickangle=45),
        yaxis=dict(rangemode="tozero", tickformat=".0f"),
        legend=dict(x=0, y=1),
        margin=dict(l=40, r=40, t=60, b=80),
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

# MAIN LOGIKK
if uploaded_files:
    st.success(f"Du har lastet opp {len(uploaded_files)} filer.")
    kombinert_df = kombiner_excel_filer(uploaded_files)
    if not kombinert_df.empty:
        plot_data_df = rens_data_for_plotting(kombinert_df.copy())
        summary_df = filter_summary_data(kombinert_df.copy())

        st.subheader("Plot")
        plot_power_data(plot_data_df)

        st.subheader("Last ned sammedragsfil (Summary)")
        towrite = io.BytesIO()
        summary_df.to_excel(towrite, index=False)
        towrite.seek(0)
        st.download_button(
            label="Last ned Summary.xlsx",
            data=towrite,
            file_name="Summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("Preview av summary")
        st.dataframe(summary_df.head(30))
    else:
        st.warning("Ingen data kunne kombineres fra filene.")
else:
    st.info("Vennligst last opp én eller flere Excel-filer for å komme i gang.")
