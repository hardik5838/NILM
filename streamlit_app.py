import streamlit as st
import pandas as pd
import numpy as np

# Data loading function
@st.cache
def load_data():
    # replace 'data.csv' with your actual data file
    df = pd.read_csv('data.csv') 
    return df

# Sidebar configuration
st.sidebar.title('Dashboard Energético Asepeyo')
page = st.sidebar.selectbox('Select Page:', ['Home', 'Data Visualization', 'NILM Simulation'])

# Load data
data = load_data()

# Main dashboard logic
if page == 'Home':
    st.title('Welcome to the Dashboard Energético Asepeyo')
    st.write('This is the home page of the dashboard.')

elif page == 'Data Visualization':
    st.title('Data Visualization')
    st.write('Here you can visualize your data.')
    st.line_chart(data['target_column'])  # replace 'target_column' with the actual column name

elif page == 'NILM Simulation':
    st.title('NILM Simulation')
    st.write('This is the NILM simulation page.')
    # Add your NILM simulation code logic here
    st.write('NILM simulation details will go here.')

# Add any additional logic and features you'd like to include in the dashboard.