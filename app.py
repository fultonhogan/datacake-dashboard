import streamlit as st
import pandas as pd

st.set_page_config(page_title="Datacake Dashboard", layout="wide")

# ---- AUTH ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

password = st.text_input("Password", type="password")

if st.button("Login"):
    if password == st.secrets["APP_PASSWORD"]:
        st.session_state.logged_in = True

if not st.session_state.logged_in:
    st.stop()

# ---- DATA ----
SHEET_CSV_URL = st.secrets["SHEET_CSV_URL"]
print(f"SHEET_CSV_URL: {SHEET_CSV_URL}") 

@st.cache_data
def load_data():
    return pd.read_csv(SHEET_CSV_URL)

df = load_data()

st.title("📈 Datacake Historical Data")
st.line_chart(df.set_index("timestamp"))
