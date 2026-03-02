import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Function to load data
@st.cache
def load_data():
    data = pd.read_csv('data.csv')
    return data

# Function to plot energy consumption
def plot_energy_consumption(data):
    plt.figure(figsize=(10, 5))
    sns.lineplot(x='Datetime', y='Energy_Consumption', data=data)
    plt.title('Energy Consumption Over Time')
    plt.xlabel('Time')
    plt.ylabel('Energy Consumption (kWh)')
    st.pyplot() 

# Main function
def main():
    st.title('Dashboard Energético')
    data = load_data()

    # Sidebar for selections
    page = st.sidebar.selectbox('Choose a page:', ['Home', 'Simulación NILM (Avanzado)', 'About'])

    if page == 'Home':
        st.write('Welcome to the Dashboard Energético')
        st.write('This dashboard provides an overview of energy consumption.')
        plot_energy_consumption(data)
    elif page == 'Simulación NILM (Avanzado)':
        st.write('Advanced NILM simulation will be implemented here')
    elif page == 'About':
        st.write('This dashboard is designed to help users understand energy consumption patterns.')

if __name__ == '__main__':
    main()