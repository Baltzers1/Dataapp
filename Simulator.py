import streamlit as st
import random

st.set_page_config(page_title="Elbilvelger", layout="centered")
st.title("Klikk ➕ for å legge til bil, ➖ for å fjerne")

NUM_SPOTS = 8

# Initier state
if "biler" not in st.session_state:
    st.session_state.biler = [None] * NUM_SPOTS

# Litt stil for emoji og tekst
st.markdown("""
    <style>
    .emoji {
        font-size: 60px;
        text-align: center;
        margin: 0.5em 0;
    }
    .info {
        text-align: center;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# Horisontale kolonner – én per bil
cols = st.columns(NUM_SPOTS)

for i in range(NUM_SPOTS):
    with cols[i]:
        bil = st.session_state.biler[i]

        # Bruk indre kolonner for å sentrere knapp
        left, center, right = st.columns([1, 2, 1])
        with center:
            if bil:
                if st.button("➖", key=f"remove_{i}"):
                    st.session_state.biler[i] = None
                    st.rerun()
            else:
                if st.button("➕", key=f"add_{i}"):
                    st.session_state.biler[i] = {
                        "SoC": random.randint(10, 90),
                        "Effekt": random.randint(1, 400)
                    }
                    st.rerun()

        # Emoji
        st.markdown(f"<div class='emoji'>{'🚗' if bil else '⬜'}</div>", unsafe_allow_html=True)

        # Info
        if bil:
            st.markdown(f"<div class='info'><strong>SoC:</strong> {bil['SoC']}%<br><strong>kW:</strong> {bil['Effekt']}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='info'>Ingen bil</div>", unsafe_allow_html=True)

# Nullstill-knapp
st.markdown("---")
if st.button("🔄 Nullstill alle"):
    st.session_state.biler = [None] * NUM_SPOTS
    st.rerun()


st.markdown("---") #linje

#Total output på bilene
total_kw_output = sum(bil["Effekt"] for bil in st.session_state.biler if bil)
st.header(f"⚡ Total output-effekt: {total_kw_output} kW")

# Velg energitap
virkningsgrad = st.slider("Velg virkningsgrad (effektivitet)", min_value=0.80, max_value=1.00, value=0.8648, step=0.0001)
# Beregn input
total_kw_input = int(total_kw_output / virkningsgrad)
# Vis resultatene
st.header(f"🔌 Total input-effekt: {total_kw_input} kW")

st.markdown("---") #linje

st.markdown("---") #linje

st.subheader("🧪 Monte Carlo-simulering av samtidighet")

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
