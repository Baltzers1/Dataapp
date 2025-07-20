import streamlit as st
import random
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Elbil Ladesimulator", layout="centered")
st.title("🔌 Elbil Ladesimulator")

# Initier lagring av biler i session state
if 'biler' not in st.session_state:
    st.session_state.biler = []

# Bruker velger antall biler å legge til
antall = st.slider("Velg antall biler å legge til:", 1, 12, 1)

if st.button("➕ Legg til biler"):
    for _ in range(antall):
        soc = random.randint(10, 90)  # State of Charge (%)
        battery_capacity = 80  # kWh - standard elbil
        needed_energy = battery_capacity * (100 - soc) / 100  # kWh som må lades
        effekt = random.randint(1, 400)  # kW ladeeffekt
        ladetid = needed_energy / effekt  # Timer

        st.session_state.biler.append({
            "SoC (%)": soc,
            "Behov (kWh)": round(needed_energy, 1),
            "Effekt (kW)": effekt,
            "Estimert ladetid (t)": round(ladetid, 2)
        })

# Vis bilene i tabell
if st.session_state.biler:
    df = pd.DataFrame(st.session_state.biler)
    st.subheader("📋 Biler i simulering")
    st.dataframe(df)

    # Vis total effekt
    total_effekt = sum(b["Effekt (kW)"] for b in st.session_state.biler)
    st.subheader(f"⚡ Total samtidig effektuttak: {total_effekt} kW")

    # Plot ladeeffekt per bil
    st.subheader("🔧 Effekt per bil")
    fig, ax = plt.subplots()
    ax.bar([f'Bil {i+1}' for i in range(len(df))], df["Effekt (kW)"])
    ax.set_ylabel("Effekt (kW)")
    ax.set_xlabel("Biler")
    ax.set_title("Ladeeffekt per bil")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Reset-knapp
if st.button("🔄 Nullstill simulering"):
    st.session_state.biler = []
    st.rerun()
