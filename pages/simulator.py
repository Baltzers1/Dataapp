import streamlit as st
import random
import plotly.express as px


st.set_page_config(page_title="Elbilvelger", layout="centered")
st.title("Klikk + for å legge til bil, - for å fjerne")

NUM_SPOTS = 8

def beregn_effekt(soc: int) -> int:
    premium = random.random() < 0.08  # 8 % sjanse for premium
    if soc < 20:
        return random.randint(200, 300) if premium else random.randint(80, 150)
    elif soc < 50:
        return random.randint(150, 200) if premium else random.randint(60, 120)
    elif soc < 80:
        return random.randint(80, 150) if premium else random.randint(30, 80)
    else:
        return random.randint(30, 60) if premium else random.randint(5, 40)

# Monte Carlo-funksjon
def simulering_antall_ganger_over_grense(grense_kw: int, n: int = 10000) -> float:
    tell_over = 0
    totaler = []

    for _ in range(n):
        antall_biler = random.randint(1, 8)
        total_effekt = 0
        for _ in range(antall_biler):
            soc = random.randint(10, 90)
            effekt = beregn_effekt(soc)
            total_effekt += effekt
        totaler.append(total_effekt)
        if total_effekt > grense_kw:
            tell_over += 1

    sannsynlighet = tell_over / n
    return sannsynlighet, totaler


# Initialiser bil-liste
if "biler" not in st.session_state:
    st.session_state.biler = [None] * NUM_SPOTS

# Rader
row1 = st.columns(NUM_SPOTS)  # Knapper
row2 = st.columns(NUM_SPOTS)  # Ikoner
row3 = st.columns(NUM_SPOTS)  # SoC
row4 = st.columns(NUM_SPOTS)  # kW

for i in range(NUM_SPOTS):
    bil = st.session_state.biler[i]

    # Rad 1: Knapper
    with row1[i]:
        if bil:
            if st.button("➖", key=f"remove_{i}", use_container_width=True):
                st.session_state.biler[i] = None
                st.rerun()
        else:
            if st.button("➕", key=f"add_{i}", use_container_width=True):
                soc = random.randint(10, 90)
                effekt = beregn_effekt(soc)
                st.session_state.biler[i] = {
                    "SoC": soc,
                    "Effekt": effekt
                }
                st.rerun()

    # Rad 2: Emoji
    with row2[i]:
        st.header("🚘" if bil else " ")

    # Rad 3: SoC
    with row3[i]:
        if bil:
            st.write(f"SoC: {bil['SoC']} %")
        else:
            st.write("")

    # Rad 4: Effekt
    with row4[i]:
        if bil:
            st.write(f"{bil['Effekt']} kW")
        else:
            st.write("")

# Nullstill-knapp
if st.button("🔄 Nullstill alle"):
    st.session_state.biler = [None] * NUM_SPOTS
    st.rerun()


st.markdown("---") #linje

#Total output på bilene
total_kw_output = sum(bil["Effekt"] for bil in st.session_state.biler if bil)
st.header(f"Total output-effekt: {total_kw_output} kW")

# Velg energitap
virkningsgrad = st.slider("Velg virkningsgrad (effektivitet)", min_value=0.80, max_value=1.00, value=0.8648, step=0.0001)
# Beregn input
total_kw_input = int(total_kw_output / virkningsgrad)
# Vis resultatene
st.header(f"Total input-effekt: {total_kw_input} kW")

st.markdown("---") #linje

st.subheader("Monte Carlo-simulering av samtidighet")

grense = st.number_input("Grense for total effekt (kW)", value=800, step=50)
antall_simuleringer = st.number_input("Antall simuleringer", value=10000, step=1000)

if st.button("🔁 Kjør simulering", key="mc_knapp"):
    sannsynlighet, totaler = simulering_antall_ganger_over_grense(grense_kw=grense, n=antall_simuleringer)
    st.success(f"Sannsynlighet for å overstige {grense} kW: **{sannsynlighet:.2%}**")

    # Lag interaktivt histogram med Plotly
    fig = px.histogram(totaler, nbins=30, title="📊 Fordeling av total effekt (kW)")
    fig.update_layout(
        xaxis_title="Total effekt (kW)",
        yaxis_title="Antall simuleringer",
        bargap=0.05
        )

    # Vis i Streamlit
    st.plotly_chart(fig, use_container_width=True)