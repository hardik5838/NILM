import streamlit as st
import pandas as pd
from scipy import stats 

def run_analysis():
    if 'my_data' not in st.session_state:
        st.error("No data found.")
        return
    df = st.session_state['my_data']
    
    # 1. Feature Engineering
    df['month'] = df['time'].dt.month
    df['hour'] = df['time'].dt.hour
    df['is_weekend'] = df['time'].dt.dayofweek >= 5

    # 2. Monthly Stats & R-Values
    monthly_stats = []
    for month in range(1, 13):
        m_data = df[df['month'] == month]
        if not m_data.empty:
            # Calculate R-value (Correlation)
            slope, intercept, r_value, p_value, std_err = stats.linregress(m_data['Temp'], m_data['kWh'])
            
            monthly_stats.append({
                'Month': month,
                'Avg_Energy': m_data['energy consumption'].mean(),
                'R_Value': r_value
            })
    
    # 3. Weekend vs Weekday Profiles
    curves = df.groupby(['is_weekend', 'hour'])['energy consumption'].mean().unstack(level=0) 
    return pd.DataFrame(monthly_stats), curves
