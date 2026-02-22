import streamlit as st
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

st.set_page_config(page_title="Datacake Dashboard", layout="wide")

# ---- AUTH ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.logged_in = True
            st.rerun()
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

# Convert datetime to pandas datetime
df['datetime'] = pd.to_datetime(df['datetime'])

# Initialize session state for date range
if 'start_date' not in st.session_state:
    st.session_state.start_date = (pd.Timestamp.today() - pd.Timedelta(days=7)).date()
if 'end_date' not in st.session_state:
    st.session_state.end_date = pd.Timestamp.today().date()

# Sidebar controls
st.sidebar.header("Settings")

# Date range selector
start_date_input = st.sidebar.date_input("Start Date", value=st.session_state.start_date)
end_date_input = st.sidebar.date_input("End Date", value=st.session_state.end_date)

# Sampling period selector
sampling_period = st.sidebar.selectbox(
    "Sampling Period",
    options=["30min", "1H", "1D", "1M"],
    format_func=lambda x: {"30min": "30 minutes", "1H": "1 hour", "1D": "1 day", "1M": "1 month"}[x]
)

# Check if dates have changed
dates_changed = (start_date_input != st.session_state.start_date or 
                 end_date_input != st.session_state.end_date)

# Filter button with warning
col1, col2 = st.sidebar.columns([1, 2])
with col1:
    filter_clicked = st.button("Filter Data")
with col2:
    if dates_changed:
        st.markdown("⚠️ Update needed")

# Only update when clicked
if filter_clicked:
    st.session_state.start_date = start_date_input
    st.session_state.end_date = end_date_input
    st.rerun()

# Filter data by date range using session state values
df_filtered = df[(df['datetime'].dt.date >= st.session_state.start_date) & 
                 (df['datetime'].dt.date <= st.session_state.end_date)]

# Show statistics in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Period Statistics")

# Calculate total variation for COUNT_TIME columns
count_cols = [col for col in df_filtered.columns if col.startswith('COUNT_TIME')]
for col in count_cols:
    valid_data = df_filtered[col].dropna()
    if len(valid_data) > 0:
        total_variation = valid_data.iloc[-1] - valid_data.iloc[0]
        st.sidebar.metric(label=col, value=f"{int(total_variation)}")

# Debug: show battery stats
if 'BATTERY' in df_filtered.columns:
    battery_vals = df_filtered['BATTERY'].dropna()
    if len(battery_vals) > 0:
        st.sidebar.write(f"Battery: {battery_vals.min():.2f}V - {battery_vals.max():.2f}V")

# Resample data
df_resampled = df_filtered.set_index('datetime').resample(sampling_period).last().reset_index()

# Calculate differences (consumption) for COUNT_TIME columns
count_cols = [col for col in df_filtered.columns if col.startswith('COUNT_TIME')]
df_diff = df_resampled.copy()
for col in count_cols:
    df_diff[f'{col}_diff'] = df_resampled[col].diff().fillna(0)

st.title("📈 Datacake Historical Data")

# Create dual-axis chart using subplots
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add bar traces for consumption (differences) for COUNT_TIME columns
for col in count_cols:
    fig.add_trace(
        go.Bar(x=df_diff['datetime'], y=df_diff[f'{col}_diff'], name=f'{col} consumption'),
        secondary_y=False
    )

# Add line traces for cumulative COUNT_TIME columns
for col in count_cols:
    fig.add_trace(
        go.Scatter(x=df_resampled['datetime'], y=df_resampled[col], name=col, mode='lines', visible='legendonly'),
        secondary_y=False
    )

# Add BATTERY on secondary y-axis (filter out NaN values)
if 'BATTERY' in df_resampled.columns:
    battery_data = df_resampled[['datetime', 'BATTERY']].dropna()
    fig.add_trace(
        go.Scatter(
            x=battery_data['datetime'], 
            y=battery_data['BATTERY'], 
            name='BATTERY', 
            mode='lines+markers',
            line=dict(color='green', width=2),
            marker=dict(size=4)
        ),
        secondary_y=True
    )

# Update axes
fig.update_xaxes(title_text="Time")
fig.update_yaxes(title_text="Consumption / Count", secondary_y=False)
fig.update_yaxes(title_text="Battery (V)", secondary_y=True, showgrid=False)

fig.update_layout(
    hovermode='x unified',
    height=600,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0
    ),
    barmode='group'
)

st.plotly_chart(fig, use_container_width=True)
