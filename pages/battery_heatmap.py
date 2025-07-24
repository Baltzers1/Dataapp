
import streamlit as st
import os
import tempfile
import shutil
import pandas as pd
from analysis import run_analysis

st.set_page_config(page_title="Batterisimulering – Peak Shaving", layout="wide")
st.title("🔋 Batterisystem Simulering for Peak Shaving")

# === Inputvalg ===
st.header("1. Last opp Excel-filer")
uploaded_files = st.file_uploader("Velg én eller flere .xlsx-filer", type="xlsx", accept_multiple_files=True)

st.header("2. Konfigurer simulering")
profile = st.selectbox("Velg profil", ["Small", "Medium", "Large"], index=1)
peak_fraction = st.slider("Velg peak-fraction (%)", min_value=10, max_value=100, value=60, step=5) / 100.0
manual_peak = st.number_input("Evt. manuell peak-grense (kW)", min_value=0.0, value=0.0, step=10.0)
save_figs = st.checkbox("Lagre figurer (SoC + Heatmap)?", value=True)

if st.button("🚀 Start simulering") and uploaded_files:
    with st.spinner("Simulerer..."):

        with tempfile.TemporaryDirectory() as temp_dir:
            # Lagre filer midlertidig
            for file in uploaded_files:
                with open(os.path.join(temp_dir, file.name), "wb") as f:
                    f.write(file.getbuffer())

            output_path = os.path.join(temp_dir, "simuleringsresultat.xlsx")

            try:
                result = run_analysis(
                    folder_path=temp_dir,
                    output_path=output_path,
                    peak_fraction=peak_fraction,
                    profile=profile,
                    save_figures=save_figs,
                    manual_peak_kW=manual_peak if manual_peak > 0 else None
                )

                st.success("Simuleringen er fullført ✅")

                # === Resultatvisning ===
                st.subheader("📊 Resultater")
                st.markdown(f"**Maks målt effekt:** {result['max_peak_kW']} kW")
                st.markdown(f"**Brukt peak-grense:** {result['used_peak_limit_kW']} kW")

                if result['optimal_config']:
                    st.markdown("**Optimal løsning:**")
                    st.json(result['optimal_config'])

                    if save_figs:
                        soc_path = os.path.join(temp_dir, "soc_plot.png")
                        if os.path.exists(soc_path):
                            st.image(soc_path, caption="State of Charge (SoC)")

                if save_figs:
                    heatmap_path = os.path.join(temp_dir, "heatmap.png")
                    if os.path.exists(heatmap_path):
                        st.image(heatmap_path, caption="Heatmap – Peak shaving evaluering")

                # === Last ned Excel-resultater ===
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 Last ned resultatfil (Excel)",
                        data=f,
                        file_name="simuleringsresultat.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            except Exception as e:
                st.error(f"Noe gikk galt under simuleringen: {e}")

else:
    st.info("Last opp minst én fil og trykk på 'Start simulering' for å kjøre.")