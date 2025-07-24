import streamlit as st


st.set_page_config(page_title="ESC Dashboard", layout="wide")

st.title("ESC Dashboard")
st.markdown("""Her finnes verktøy relatert til oppgave Recharge ESC team utfører""")

col1,col2,col3 = st.columns(3)

with col1:
    st.link_button("Data plotting kW","https://emc-dashboard.streamlit.app/~/+/plotting_utilization", use_container_width=True)
with col2:
    st.button("Link 2", use_container_width=True)
with col3:
    st.button("Link 3", use_container_width=True)
