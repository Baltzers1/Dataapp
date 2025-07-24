
import streamlit as st
import os
import tempfile
from analysis import run_analysis

st.set_page_config(page_title="Batterisimulering – Peak Shaving", )
st.title("BESS Simulator for Peak Shaving")

# === Inputvalg ===
st.header("1. Upload Excel-files")
uploaded_files = st.file_uploader("Chose one or more .xlsx-files", type="xlsx", accept_multiple_files=True)

st.header("2. Configure the simulation")
profile = st.selectbox("Chose profile", ["Small", "Medium", "Large"], index=1)
peak_fraction = st.slider("Chose peak-fractor (%)", min_value=10, max_value=100, value=60, step=5) / 100.0
manual_peak = st.number_input("OPTIONAL: Input peak-limit (kW)", min_value=0.0, value=0.0, step=10.0)
save_figs = st.checkbox("Save the SoC + Heatmap figures?", value=True)

if st.button("🏃🏾‍♀️‍➡️ Run simulation") and uploaded_files:
    with st.spinner("Simulating..."):

        with tempfile.TemporaryDirectory() as temp_dir:
            # Lagre filer midlertidig
            for file in uploaded_files:
                with open(os.path.join(temp_dir, file.name), "wb") as f:
                    f.write(file.getbuffer())

            output_path = os.path.join(temp_dir, "simresults.xlsx")

            try:
                result = run_analysis(
                    folder_path=temp_dir,
                    output_path=output_path,
                    peak_fraction=peak_fraction,
                    profile=profile,
                    save_figures=save_figs,
                    manual_peak_kW=manual_peak if manual_peak > 0 else None
                )

                st.success("Simulation is completed ✅")

                # === Resultatvisning ===
                st.subheader("📊 Results")
                st.markdown(f"**Max measured effect:** {result['max_peak_kW']} kW")
                st.markdown(f"**Peak-limit:** {result['used_peak_limit_kW']} kW")

                if result['optimal_config']:
                    st.markdown("**Optimal solution:**")
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
                        label="📥 Extract results (Excel)",
                        data=f,
                        file_name="simuleringsresultat.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            except Exception as e:
                st.error(f"An unexpected error occured: {e}")

else:
    st.info("Upload at least on file and hit the 'Run simulation' button to start.")