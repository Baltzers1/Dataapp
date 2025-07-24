import streamlit as st
import math

st.title("3-phase kVA ⇄ Ampere Calculator")

# ----------------------------
# Del 1: kVA-utregning
# ----------------------------
st.header("From Voltage & Amps to kVA")

volt = st.number_input("Line-to-line Voltage (V)", min_value=0.0, step=10.0, value=400.0, key="volt1")
ampere = st.number_input("Current (A)", min_value=0.0, step=1.0, value=1000.0, key="amp1")

if volt > 0 and ampere > 0:
    kva = (math.sqrt(3) * ampere * volt) / 1000
    st.success(f"Apparent Power: **{kva:.2f} kVA**")

    st.markdown("#### Calculation:")
    st.latex(r"S = \frac{\sqrt{3} \cdot I \cdot V_{L-L}}{1000}")
    st.latex(rf"S = \frac{{\sqrt{{3}} \cdot {ampere:.0f} \cdot {volt:.0f}}}{{1000}} = {kva:.2f}\ \mathrm{{kVA}}")

# ----------------------------
#  Del 2: Amps-utregning
# ----------------------------
st.header("From kVA & Voltage to Amps")

kva2 = st.number_input("Apparent power (kVA)", min_value=0.0, step=1.0, value=850.0, key="kva2")
voltage2 = st.number_input("Line-to-line voltage (V)", min_value=0.0, step=10.0, value=400.0, key="volt2")

if kva2 > 0 and voltage2 > 0:
    amps = (kva2 * 1000) / (math.sqrt(3) * voltage2)
    st.success(f"Current: **{amps:.2f} A**")

    st.markdown("####  Calculation:")
    st.latex(r"I = \frac{S \cdot 1000}{\sqrt{3} \cdot V_{L-L}}")
    st.latex(rf"I = \frac{{{kva2:.2f} \cdot 1000}}{{\sqrt{{3}} \cdot {voltage2:.0f}}} = {amps:.2f}\ \mathrm{{A}}")

else:
    st.info("Please enter both kVA and voltage.")
