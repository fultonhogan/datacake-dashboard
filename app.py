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

@st.cache_data
def load_data():
    try:
        # Ensure URL starts with http/https
        if not SHEET_CSV_URL.startswith(('http://', 'https://')):
            st.error(f"Invalid URL format: {SHEET_CSV_URL}")
            st.stop()
        return pd.read_csv(SHEET_CSV_URL)
    except Exception as e:
        st.error(f"Failed to load data from: {SHEET_CSV_URL}")
        st.error(f"Error: {str(e)}")
        raise

df = load_data()

st.title("📈 Datacake Historical Data")
st.line_chart(df.set_index("datetime"))
