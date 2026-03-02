import streamlit as st
import pandas as pd
import numpy as np

# Load Energy Data
@st.cache
def load_energy_data():
    energy_data = pd.read_csv('data/test file Via 36 - 1.csv')
    return energy_data

# Load Weather Data
@st.cache
def load_weather_data():
    weather_data = pd.read_csv('data/weather_data.csv')
    return weather_data

# Function to Filter Data
def filter_data(energy_data, start_date, end_date):
    mask = (energy_data['timestamp'] >= start_date) & (energy_data['timestamp'] <= end_date)
    return energy_data.loc[mask]

# NILM Simulation
def run_nilm_simulation(filtered_data):
    # Implement NILM simulation logic here
    simulated_results = {'result': 'Simulation complete'}
    return simulated_results

# Streamlit App Layout
st.title("NILM Application")

# Load Data
energy_data = load_energy_data()
weather_data = load_weather_data()

# Date Filters
start_date = st.sidebar.date_input('Start date', value=pd.to_datetime('2021-01-01'))
end_date = st.sidebar.date_input('End date', value=pd.to_datetime('2021-12-31'))

# Filter Data
filtered_data = filter_data(energy_data, start_date, end_date)

# Run NILM Simulation
if st.button('Run NILM Simulation'):
    results = run_nilm_simulation(filtered_data)
    st.write(results)