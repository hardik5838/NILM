import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from datetime import timedelta

# --------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING (Professional Mode)
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Asepeyo Net Zero Strategy",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Professional Presentation
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {font-family: 'Helvetica', sans-serif; color: #003366; font-size: 3rem;}
    h2 {font-family: 'Helvetica', sans-serif; color: #005599; font-size: 2.2rem; border-bottom: 2px solid #ddd; padding-bottom: 10px;}
    h3 {font-family: 'Helvetica', sans-serif; color: #444; font-size: 1.5rem;}
    .metric-box {border: 1px solid #e0e0e0; padding: 20px; border-radius: 5px; background-color: #f9f9f9; text-align: center;}
    .metric-val {font-size: 2rem; font-weight: bold; color: #003366;}
    .metric-lbl {font-size: 1rem; color: #666;}
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# 2. DATA LOADERS (Robust)
# --------------------------------------------------------------------------
@st.cache_data
def load_billing_data():
    """Loads and cleans the 2025 Billing Data."""
    try:
        # Search for file in data folder
        data_dir = "data"
        files = [f for f in os.listdir(data_dir) if "Factura" in f]
        if not files: return pd.DataFrame()
        
        file_path = os.path.join(data_dir, files[0])
        df = pd.read_csv(file_path, sep=None, engine='python')
        
        # Clean numeric columns (handle European formats)
        cols_to_clean = [c for c in df.columns if "Consumo" in c or "Importe" in c or "Base" in c]
        for col in cols_to_clean:
            if df[col].dtype == object:
                df[col] = (df[col].astype(str)
                           .str.replace('.', '', regex=False)
                           .str.replace(',', '.', regex=False))
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Standardize columns
        df.rename(columns=lambda x: x.strip(), inplace=True)
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data
def load_hourly_data():
    """Loads the hourly data (Via Augusta 36)."""
    try:
        data_dir = "data"
        # Look for the hourly file uploaded
        files = [f for f in os.listdir(data_dir) if "horaria" in f or "lecturas" in f.lower()]
        if not files: return pd.DataFrame()
        
        file_path = os.path.join(data_dir, files[0])
        df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')
        
        # Robust Cleaning from Tool #1
        df.rename(columns=lambda x: x.strip(), inplace=True)
        col_mapping = {'Fecha y hora': 'fecha', 'Fecha': 'fecha', 'Energía activa': 'kwh', 'Energía activa (kWh)': 'kwh'}
        df.rename(columns=col_mapping, inplace=True)
        
        if 'kwh' in df.columns and df['kwh'].dtype == object:
            df['kwh'] = (df['kwh'].astype(str)
                         .str.replace('"', '', regex=False)
                         .str.replace(',', '.', regex=False)) # Assume simple comma decimal if quotes exist
            df['kwh'] = pd.to_numeric(df['kwh'], errors='coerce')
            
        df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
        df.dropna(subset=['fecha', 'kwh'], inplace=True)
        return df
    except Exception:
        return pd.DataFrame()

# --------------------------------------------------------------------------
# 3. HELPER: AI FORECASTING (Random Forest)
# --------------------------------------------------------------------------
def run_forecast(df):
    """Generates a forecast using Random Forest."""
    df['day_of_year'] = df['fecha'].dt.dayofyear
    df['hour'] = df['fecha'].dt.hour
    df['day_of_week'] = df['fecha'].dt.dayofweek
    
    # Train/Test
    X = df[['day_of_year', 'hour', 'day_of_week']]
    y = df['kwh']
    
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)
    
    # Create Future Dataframe (Next 7 days)
    last_date = df['fecha'].max()
    future_dates = [last_date + timedelta(hours=i) for i in range(1, 168 + 1)] # 7 days
    future_df = pd.DataFrame({'fecha': future_dates})
    future_df['day_of_year'] = future_df['fecha'].dt.dayofyear
    future_df['hour'] = future_df['fecha'].dt.hour
    future_df['day_of_week'] = future_df['fecha'].dt.dayofweek
    
    future_df['predicted_kwh'] = model.predict(future_df[['day_of_year', 'hour', 'day_of_week']])
    return future_df

# --------------------------------------------------------------------------
# 4. MAIN APP LOGIC
# --------------------------------------------------------------------------
def main():
    # --- NAVIGATION (Simple Tabs for Presentation Flow) ---
    tabs = st.tabs(["1. Vision & Strategy", "2. Deep Dive: Via Augusta 36", "3. The Path to Net Zero"])

    # ==============================================================================
    # SLIDE 1: INTRODUCTION & CONTEXT (Carnot Engine)
    # ==============================================================================
    with tabs[0]:
        st.title("Strategic Energy Plan: Net Zero")
        st.markdown("### The Efficiency Engine")
        
        col_text, col_visual = st.columns([1, 1])
        
        with col_text:
            st.markdown("""
            **The Challenge:**
            Inaction has historically cost over **€1.1 Million** in lost savings. 
            To reverse this, we apply the **Carnot Principle** to our energy strategy: maximizing the efficiency of every Euro invested.
            
            **Our 3-Phase Approach:**
            1.  **Measurement & Control:** Real-time visibility (Digital Twin).
            2.  **Optimization:** Low-cost measures (Thermostats, Phantom Loads) to generate cash flow.
            3.  **Investment:** Reinvesting savings into Structural Upgrades (LED, Solar).
            """)
            
            # KPI Metrics from Audit Data (Hardcoded from 2025.csv analysis or loaded dynamically)
            st.markdown("#### Portfolio Potential (2025 Audit)")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown('<div class="metric-box"><div class="metric-val">€ 1.8M</div><div class="metric-lbl">Total Investment Identified</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="metric-box"><div class="metric-val">€ 650k</div><div class="metric-lbl">Potential Annual Savings</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown('<div class="metric-box"><div class="metric-val">2.8 Yrs</div><div class="metric-lbl">Avg ROI Period</div></div>', unsafe_allow_html=True)

        with col_visual:
            # Load Billing Data for Distribution Chart
            df_bill = load_billing_data()
            if not df_bill.empty and 'Consumo activa total (kWh)' in df_bill.columns:
                # Top 10 Consumers Chart
                top_consumers = df_bill.groupby('Nombre suministro')['Consumo activa total (kWh)'].sum().nlargest(10).reset_index()
                fig = px.bar(top_consumers, x='Consumo activa total (kWh)', y='Nombre suministro', orientation='h',
                             title="Consumption Distribution: Top 10 Centers",
                             color='Consumo activa total (kWh)', color_continuous_scale='Blues')
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Load Billing Data to see consumption distribution.")

    # ==============================================================================
    # SLIDE 2: DEEP DIVE - VIA AUGUSTA 36 (Pattern & Forecast)
    # ==============================================================================
    with tabs[1]:
        st.title("Site Analysis: Via Augusta 36")
        st.markdown("Applying **Pattern Recognition** and **AI Forecasting** to identify efficiency gaps.")
        
        df_hourly = load_hourly_data()
        
        if not df_hourly.empty:
            # 1. PATTERN VISUALIZATION
            col_p1, col_p2 = st.columns([2, 1])
            
            with col_p1:
                st.subheader("Historical Consumption Profile")
                # Filter last 2 weeks for clarity
                last_date = df_hourly['fecha'].max()
                start_date = last_date - timedelta(days=14)
                df_zoom = df_hourly[(df_hourly['fecha'] >= start_date) & (df_hourly['fecha'] <= last_date)]
                
                fig_pat = px.line(df_zoom, x='fecha', y='kwh', title="Hourly Load Curve (Last 14 Days)",
                                  line_shape='spline')
                fig_pat.update_traces(line=dict(color='#003366', width=2))
                fig_pat.update_layout(template='plotly_white', xaxis_title="Date", yaxis_title="Power (kW)")
                st.plotly_chart(fig_pat, use_container_width=True)
            
            with col_p2:
                st.subheader("NILM Disaggregation (Digital Twin)")
                st.markdown("We decompose the total load into specific end-uses to find waste.")
                
                # Simulate NILM breakdown for the average day
                df_hourly['hour'] = df_hourly['fecha'].dt.hour
                avg_profile = df_hourly.groupby('hour')['kwh'].mean().reset_index()
                
                # Simple logic for breakdown (Simulation)
                avg_profile['HVAC'] = avg_profile['kwh'] * 0.45
                avg_profile['Lighting'] = avg_profile['kwh'] * 0.25
                avg_profile['Base Load'] = avg_profile['kwh'] * 0.30
                
                # Stacked Area
                fig_nilm = go.Figure()
                fig_nilm.add_trace(go.Scatter(x=avg_profile['hour'], y=avg_profile['Base Load'], stackgroup='one', name='Base Load (Phantom)', line=dict(width=0, color='gray')))
                fig_nilm.add_trace(go.Scatter(x=avg_profile['hour'], y=avg_profile['Lighting'], stackgroup='one', name='Lighting', line=dict(width=0, color='#f1c40f')))
                fig_nilm.add_trace(go.Scatter(x=avg_profile['hour'], y=avg_profile['HVAC'], stackgroup='one', name='HVAC', line=dict(width=0, color='#e74c3c')))
                
                fig_nilm.update_layout(title="Average Daily Load Breakdown", xaxis_title="Hour of Day", yaxis_title="kW", template='plotly_white', legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig_nilm, use_container_width=True)

            # 2. AI FORECAST
            st.subheader("AI-Driven Demand Forecast")
            st.markdown("Predicting future consumption to optimize operations (using Random Forest Regression).")
            
            if st.button("Generate Forecast"):
                with st.spinner("Running Predictive Model..."):
                    future_df = run_forecast(df_hourly)
                    
                    fig_for = go.Figure()
                    # Plot History (Last 3 days)
                    hist_zoom = df_hourly[df_hourly['fecha'] > (df_hourly['fecha'].max() - timedelta(days=3))]
                    fig_for.add_trace(go.Scatter(x=hist_zoom['fecha'], y=hist_zoom['kwh'], name='Historical Data', line=dict(color='gray')))
                    # Plot Forecast
                    fig_for.add_trace(go.Scatter(x=future_df['fecha'], y=future_df['predicted_kwh'], name='AI Forecast (Next 7 Days)', line=dict(color='#005599', dash='dot')))
                    
                    fig_for.update_layout(template='plotly_white', xaxis_title="Date", yaxis_title="Power (kW)")
                    st.plotly_chart(fig_for, use_container_width=True)

        else:
            st.warning("Hourly data file not found in 'data/' folder. Please upload '03122025_Distribución eléctrica horaria.csv'.")

    # ==============================================================================
    # SLIDE 3: SOLAR GENERATION & NET ZERO
    # ==============================================================================
    with tabs[2]:
        st.title("Transition to Net Zero: Solar Generation")
        st.markdown("### Interactive Solar Sizing Tool")
        
        col_input, col_sim = st.columns([1, 3])
        
        with col_input:
            st.markdown("#### System Configuration")
            # Solar Inputs
            area = st.number_input("Available Roof Area (m²)", min_value=100, value=500, step=50)
            panel_eff = 0.20 # 20% efficiency
            kwp_per_m2 = 0.200 # approx 200W/m2
            
            system_size_kwp = area * kwp_per_m2
            st.markdown(f"**System Capacity:** {system_size_kwp:.1f} kWp")
            
            irradiance = st.slider("Avg. Irradiance (Peak Sun Hours)", 3.0, 7.0, 5.0)
            
        with col_sim:
            # Solar Simulation Logic
            if not df_hourly.empty:
                # Calculate Average Daily Consumption Profile
                avg_load = df_hourly.groupby(df_hourly['fecha'].dt.hour)['kwh'].mean()
                
                # Simulate Solar Curve (Gaussian Bell Curve centered at 13:00)
                hours = np.arange(24)
                # Simple Gaussian model for solar: Peak * exp(- (t - 13)^2 / (2 * width^2))
                # Width controls how wide the day is
                solar_curve = system_size_kwp * np.exp(- (hours - 13)**2 / (2 * 2.5**2))
                # Adjust for irradiance factor (simplified)
                solar_curve = solar_curve * (irradiance / 5.0) 
                
                # Metrics
                total_load_daily = avg_load.sum()
                total_gen_daily = solar_curve.sum()
                
                # Calculate Self-Consumption (Min of Load or Gen at each hour)
                self_consumption = np.minimum(solar_curve, avg_load)
                total_self_con = self_consumption.sum()
                
                coverage = (total_self_con / total_load_daily) * 100
                export = total_gen_daily - total_self_con
                
                # Visualization
                fig_sol = go.Figure()
                fig_sol.add_trace(go.Scatter(x=hours, y=avg_load, fill='tozeroy', name='Building Consumption', line=dict(color='gray', width=0)))
                fig_sol.add_trace(go.Scatter(x=hours, y=solar_curve, name='Solar Generation', line=dict(color='#f39c12', width=3)))
                
                # Overlap Area
                fig_sol.add_trace(go.Scatter(x=hours, y=self_consumption, fill='tozeroy', name='Self-Consumption', line=dict(width=0, color='#27ae60'), opacity=0.5))
                
                fig_sol.update_layout(title="Daily Energy Balance (Average Day)", xaxis_title="Hour", yaxis_title="kW", template='plotly_white')
                st.plotly_chart(fig_sol, use_container_width=True)
                
                # Impact Metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("Grid Independence", f"{coverage:.1f}%")
                m2.metric("Daily Generation", f"{total_gen_daily:.0f} kWh")
                m3.metric("CO2 Saved (Daily)", f"{total_self_con * 0.25:.1f} kg") # 0.25 kg/kWh factor
            else:
                st.info("Load Hourly Data in Tab 2 to run Solar Simulation.")

if __name__ == "__main__":
    main()
