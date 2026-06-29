import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Dynamic Oasis Validation Dashboard", layout="wide")
st.title("⚡ The Oasis Project: Dynamic Data-Driven Dashboard")
st.markdown("Upload your Datadis CSV. The system will dynamically calculate your thesis KPIs by applying a 50% HVAC and Lighting reduction.")

# --- SIDEBAR PARAMETERS ---
st.sidebar.header("📁 Data Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload Datadis CSV", type=["csv", "xlsx"])

st.sidebar.header("⚙️ Grid & Economic Parameters")
violation_threshold = st.sidebar.number_input("Peak Violation Threshold (kW)", value=100.0, help="The kW limit that triggers a grid stress violation.")
price_p1 = st.sidebar.number_input("P1 Peak Price (€/kWh)", value=0.35)
price_int = st.sidebar.number_input("Intermediate Price (€/kWh)", value=0.25)
price_p6 = st.sidebar.number_input("P6 Valley Price (€/kWh)", value=0.15)

# --- CORE PROCESSING ---
if uploaded_file is not None:
    # 1. Load and Clean Data
    try:
        # Handling Datadis European formatting (semicolons and commas)
        df = pd.read_csv(uploaded_file, sep=';', decimal=',')
    except:
        # Fallback for standard CSVs
        df = pd.read_csv(uploaded_file)
    
    # Standardize column names (assuming standard Datadis format: Fecha, Hora, Consumo_kWh)
    # We will look for a column containing 'Consumo' or 'Energy'
    consumo_col = [col for col in df.columns if 'consumo' in col.lower() or 'kwh' in col.lower()][0]
    
    # 2. Dynamic Disaggregation (NILM Proxy) & Optimization
    # We apply the 50% reduction to HVAC and Lighting
    
    baseline_kw = df[consumo_col].values
    optimized_kw = np.zeros_like(baseline_kw)
    
    # Process day by day (assuming 24-hour chunks for simplicity in this proxy)
    for i in range(0, len(baseline_kw), 24):
        chunk = baseline_kw[i:i+24]
        if len(chunk) < 24: break
        
        # NILM Logic: Base load is the minimum of the night hours (0-5)
        daily_base = min(chunk[0:6]) 
        
        for h in range(24):
            total = chunk[h]
            active_load = max(0, total - daily_base)
            
            # Applying thesis load mix assumptions: 50% HVAC, 40% Lighting, 10% Vent during active hours
            hvac = active_load * 0.50
            lighting = active_load * 0.40
            vent = active_load * 0.10
            
            if 10 <= h <= 14: # High Tariff P1 Window
                # Apply 50% reduction rule
                opt_hvac = hvac * 0.50
                opt_lighting = lighting * 0.50
            else:
                opt_hvac = hvac
                opt_lighting = lighting
                
            optimized_kw[i+h] = daily_base + opt_hvac + opt_lighting + vent

    # Add the optimized data to the dataframe
    df['Optimized_kWh'] = optimized_kw
    
    # 3. Dynamic KPI Calculations
    max_peak_base = df[consumo_col].max()
    max_peak_opt = df['Optimized_kWh'].max()
    
    # Violations recount
    violations_base = len(df[df[consumo_col] > violation_threshold])
    violations_opt = len(df[df['Optimized_kWh'] > violation_threshold])
    
    # Battery Capacity Equivalent (Total Energy Saved = Displaced Battery Need)
    total_energy_base = df[consumo_col].sum()
    total_energy_opt = df['Optimized_kWh'].sum()
    virtual_battery_kwh = total_energy_base - total_energy_opt
    battery_reduction_pct = (virtual_battery_kwh / total_energy_base) * 100
    
    # Financials (Assuming hour index maps to 0-23 roughly)
    prices = []
    for h in range(len(df)):
        hour_of_day = h % 24
        if 0 <= hour_of_day < 8: prices.append(price_p6)
        elif 10 <= hour_of_day <= 14: prices.append(price_p1)
        else: prices.append(price_int)
        
    df['Price'] = prices
    total_cost_base = (df[consumo_col] * df['Price']).sum()
    total_cost_opt = (df['Optimized_kWh'] * df['Price']).sum()

    # --- DASHBOARD RENDER ---
    st.header("1. Dynamic Grid & Financial Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Max Peak (Baseline)", f"{max_peak_base:.1f} kW")
    col2.metric("Max Peak (Optimized)", f"{max_peak_opt:.1f} kW", f"{max_peak_opt-max_peak_base:.1f} kW")
    col3.metric("Grid Violations (Baseline)", f"{violations_base}")
    col4.metric("Grid Violations (Optimized)", f"{violations_opt}", f"{violations_opt-violations_base}")

    st.markdown("---")
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total OPEX (Baseline)", f"€{total_cost_base:,.2f}")
    col_b.metric("Total OPEX (Optimized)", f"€{total_cost_opt:,.2f}", f"€{total_cost_opt-total_cost_base:,.2f}")
    col_c.metric("Virtual Battery Created", f"{virtual_battery_kwh:,.0f} kWh", f"{battery_reduction_pct:.1f}% of Total Load")

    # Chart: Load Profile Comparison (First 7 Days)
    st.subheader("📉 Time-Series Load Curve (First 7 Days Sample)")
    sample_df = df.head(24*7).reset_index()
    
    fig_load = go.Figure()
    fig_load.add_trace(go.Scatter(x=sample_df.index, y=sample_df[consumo_col], mode='lines', name='Baseline Load', line=dict(color='red', dash='dash')))
    fig_load.add_trace(go.Scatter(x=sample_df.index, y=sample_df['Optimized_kWh'], mode='lines', name='Optimized Load', fill='tozeroy', line=dict(color='green')))
    
    fig_load.update_layout(xaxis_title="Hours", yaxis_title="Power Demand (kW)", height=400)
    st.plotly_chart(fig_load, use_container_width=True)

else:
    st.info("👈 Please upload your Datadis CSV file in the sidebar to dynamically calculate the KPIs.")
