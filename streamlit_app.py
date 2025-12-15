import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import io
import requests
from datetime import datetime, timedelta

# --------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Asepeyo Net Zero & Energy Digital Twin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Asepeyo Corporate Identity
st.markdown("""
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
    h1 {color: #003366; font-family: 'Helvetica', sans-serif;}
    h2 {color: #004d99; border-bottom: 2px solid #003366; padding-bottom: 10px;}
    h3 {color: #444;}
    .metric-box {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #003366;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# 2. HELPER FUNCTIONS: DATA LOADING
# --------------------------------------------------------------------------
@st.cache_data
def load_energy_data(file_input):
    """Loads and standardizes Energy Data (Real CSV)."""
    try:
        if file_input is None: return pd.DataFrame()
        
        # Determine if it's a file object or a URL/Path
        if isinstance(file_input, str):
            df = pd.read_csv(file_input, sep=None, engine='python')
        else:
            file_input.seek(0)
            df = pd.read_csv(file_input, sep=None, engine='python')

        # Standardize Columns
        df.rename(columns=lambda x: x.strip(), inplace=True)
        
        # Map common Spanish column names to standard keys
        col_map = {
            'Fecha': 'fecha', 'Date': 'fecha', 'Time': 'fecha',
            'Energía activa (kWh)': 'kwh', 'Consumo': 'kwh', 'Active Energy': 'kwh', 'Consumo activa total (kWh)': 'kwh'
        }
        df.rename(columns=col_map, inplace=True)
        
        # Clean Data
        if 'fecha' in df.columns and 'kwh' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
            
            # Clean numeric kwh (handle European formats like 1.200,50)
            if df['kwh'].dtype == object:
                df['kwh'] = (df['kwh'].astype(str)
                             .str.replace('.', '', regex=False)
                             .str.replace(',', '.', regex=False))
            df['kwh'] = pd.to_numeric(df['kwh'], errors='coerce')
            
            df.dropna(subset=['fecha', 'kwh'], inplace=True)
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_weather_data(file_input):
    """Loads Weather Data (Optional)."""
    try:
        if file_input is None: return pd.DataFrame()
        if isinstance(file_input, str):
            df = pd.read_csv(file_input)
        else:
            file_input.seek(0)
            df = pd.read_csv(file_input)
            
        # Basic cleaning for NASA Power format or standard CSV
        if 'YEAR' in df.columns and 'MO' in df.columns:
            df['fecha'] = pd.to_datetime(df[['YEAR', 'MO', 'DY', 'HR']].astype(str).agg('-'.join, axis=1), format='%Y-%m-%d-%H')
        elif 'Date' in df.columns:
            df['fecha'] = pd.to_datetime(df['Date'])
            
        # Standardize Temp column
        if 'T2M' in df.columns: df.rename(columns={'T2M': 'temperatura_c'}, inplace=True)
        if 'Temp' in df.columns: df.rename(columns={'Temp': 'temperatura_c'}, inplace=True)
        
        return df[['fecha', 'temperatura_c']] if 'fecha' in df.columns else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

@st.cache_data
def generate_static_audit_data():
    """Generates the static data for the Strategy/Measures tab."""
    measures = [
       {'Measure': 'Solar Panels (Rooftop)', 'Savings_EUR': 180376, 'Inv_EUR': 650000, 'Type': 'Generation', 'ROI': 3.6},
       {'Measure': 'BMS Upgrade (Digital Twin)', 'Savings_EUR': 75190, 'Inv_EUR': 150000, 'Type': 'Control', 'ROI': 2.0},
       {'Measure': 'LED Retrofit (Hospital)', 'Savings_EUR': 68551, 'Inv_EUR': 84415, 'Type': 'Efficiency', 'ROI': 1.2},
       {'Measure': 'HVAC Setpoint Optimization', 'Savings_EUR': 55974, 'Inv_EUR': 5000, 'Type': 'Optimization', 'ROI': 0.1},
       {'Measure': 'Air Curtains Installation', 'Savings_EUR': 36873, 'Inv_EUR': 45000, 'Type': 'Efficiency', 'ROI': 1.2},
       {'Measure': 'Phantom Load Elimination', 'Savings_EUR': 34873, 'Inv_EUR': 2500, 'Type': 'Optimization', 'ROI': 0.1}
    ]
    return pd.DataFrame(measures)

# --------------------------------------------------------------------------
# 3. HELPER FUNCTIONS: DIGITAL TWIN LOGIC
# --------------------------------------------------------------------------
def generate_load_curve(hours, start, end, max_kw, ramp_up, ramp_down, dips=None):
    if dips is None: dips = []
    curve = np.zeros(len(hours))
    for i, h in enumerate(hours):
        val = 0.0
        if start <= h < end:
            val = 1.0
            if h < (start + ramp_up) and ramp_up > 0: val = (h - start) / ramp_up
            if h >= (end - ramp_down) and ramp_down > 0: val = (end - h) / ramp_down
            for dip in dips:
                if int(h) == int(dip['hour']): val *= dip['factor']
        curve[i] = np.clip(val, 0.0, 1.0) * max_kw
    return curve

def run_twin_simulation(df_avg, config):
    df = df_avg.copy()
    hours = df['hour'].values
    
    # Components
    df['sim_base'] = np.full(len(hours), config['base_kw'])
    
    # Ventilation
    df['sim_vent'] = generate_load_curve(hours, config['vent_s'], config['vent_e'], config['vent_kw'], config['vent_ru'], config['vent_rd'])
    
    # Lighting
    light_curve = generate_load_curve(hours, config['light_s'], config['light_e'], config['light_kw'], 0.5, 0.5)
    df['sim_light'] = light_curve * config['light_fac']
    # Security Light logic
    df.loc[df['sim_light'] < (config['light_kw'] * 0.1), 'sim_light'] = config['light_kw'] * config['light_sec']
    
    # HVAC
    # Simple logic: If temp provided, use it, else flat curve
    if 'temperatura_c' in df.columns and config['hvac_mode'] == 'Weather':
        delta = (np.maximum(0, df['temperatura_c'] - config['set_c']) + np.maximum(0, config['set_h'] - df['temperatura_c']))
        raw = delta * config['therm_sens']
        sched = generate_load_curve(hours, config['therm_s'], config['therm_e'], 1.0, 1, 1)
        df['sim_therm'] = np.minimum(raw, config['therm_kw']) * sched
    else:
        df['sim_therm'] = generate_load_curve(hours, config['therm_s'], config['therm_e'], config['therm_kw'], 1, 1)

    df['sim_total'] = df['sim_base'] + df['sim_vent'] + df['sim_light'] + df['sim_therm']
    
    if 'kwh' in df.columns:
        df['diff'] = df['sim_total'] - df['kwh']
        
    return df

# --------------------------------------------------------------------------
# 4. MAIN APPLICATION
# --------------------------------------------------------------------------
def main():
    # --- SIDEBAR: DATA LOADING ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Asepeyo_logo.svg/2560px-Asepeyo_logo.svg.png", width=200)
        st.title("Data Center")
        
        st.info("Upload your consumption data (CSV) to activate the Twin Calculator and Analysis tabs.")
        
        file_energy = st.file_uploader("1. Energy Data (CSV)", type=['csv'])
        file_weather = st.file_uploader("2. Weather Data (Optional)", type=['csv'])
        
        # Load Data
        df_energy = load_energy_data(file_energy)
        df_weather = load_weather_data(file_weather)
        
        if not df_energy.empty:
            st.success(f"Loaded: {len(df_energy)} rows")
            min_date = df_energy['fecha'].min().date()
            max_date = df_energy['fecha'].max().date()
            st.caption(f"Range: {min_date} to {max_date}")
        else:
            st.warning("Using demo data for visualization.")
            # Generate dummy data if no file for demo purposes
            dates = pd.date_range(start="2024-01-01", periods=24*30, freq="h")
            df_energy = pd.DataFrame({'fecha': dates, 'kwh': np.random.uniform(20, 100, size=len(dates))})
            df_energy['hour'] = df_energy['fecha'].dt.hour
            # Add some shape
            df_energy['kwh'] += (np.sin((df_energy['hour']-6)/24 * 2 * np.pi) * 20)
            df_energy['kwh'] = df_energy['kwh'].clip(lower=10)

    # --- MAIN TABS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Consumption of the Year", 
        "🛠️ Energy Efficiency Measures", 
        "🤖 Twin Calculator (NILM)", 
        "📈 Analysis Tab", 
        "☀️ Solar Generation"
    ])

    # ==============================================================================
    # TAB 1: CONSUMPTION OF THE YEAR
    # ==============================================================================
    with tab1:
        st.header("Annual Consumption Overview")
        
        if not df_energy.empty:
            df_energy['Year'] = df_energy['fecha'].dt.year
            df_energy['Month'] = df_energy['fecha'].dt.month_name()
            df_energy['Month_Num'] = df_energy['fecha'].dt.month
            
            # Select Year
            years = sorted(df_energy['Year'].unique())
            sel_year = st.selectbox("Select Year", years, index=len(years)-1)
            df_yr = df_energy[df_energy['Year'] == sel_year]
            
            # KPIs
            total_kwh = df_yr['kwh'].sum()
            avg_kwh = df_yr['kwh'].mean()
            peak_kwh = df_yr['kwh'].max()
            est_cost = total_kwh * 0.20 # assumption
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Consumption", f"{total_kwh:,.0f} kWh")
            c2.metric("Estimated Cost", f"€ {est_cost:,.0f}")
            c3.metric("Peak Demand", f"{peak_kwh:,.1f} kW")
            c4.metric("Data Points", f"{len(df_yr)}")
            
            st.divider()
            
            # Charts
            col_chart1, col_chart2 = st.columns([2, 1])
            
            with col_chart1:
                # Monthly Aggregation
                df_monthly = df_yr.groupby(['Month_Num', 'Month'])['kwh'].sum().reset_index().sort_values('Month_Num')
                fig_mon = px.bar(df_monthly, x='Month', y='kwh', title=f"Monthly Consumption ({sel_year})", text_auto='.2s', color='kwh', color_continuous_scale='Blues')
                fig_mon.update_layout(template='plotly_white')
                st.plotly_chart(fig_mon, use_container_width=True)
                
            with col_chart2:
                # Heatmap
                df_yr['DayOfWeek'] = df_yr['fecha'].dt.day_name()
                df_yr['Hour'] = df_yr['fecha'].dt.hour
                heatmap_data = df_yr.groupby(['DayOfWeek', 'Hour'])['kwh'].mean().reset_index()
                
                # Sort days
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                fig_heat = px.density_heatmap(heatmap_data, x='Hour', y='DayOfWeek', z='kwh', 
                                              category_orders={'DayOfWeek': days_order},
                                              title="Intensity Heatmap (Avg kW)", color_continuous_scale='Viridis')
                fig_heat.update_layout(template='plotly_white')
                st.plotly_chart(fig_heat, use_container_width=True)

    # ==============================================================================
    # TAB 2: ENERGY EFFICIENCY MEASURES
    # ==============================================================================
    with tab2:
        st.header("Strategic Investment Plan")
        st.markdown("Prioritized list of energy conservation measures (ECMs) identified in the 2025 Audit.")
        
        df_measures = generate_static_audit_data()
        
        # Top Level Metrics
        total_inv = df_measures['Inv_EUR'].sum()
        total_save = df_measures['Savings_EUR'].sum()
        avg_roi = total_inv / total_save if total_save > 0 else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Investment Required", f"€ {total_inv:,.0f}")
        m2.metric("Potential Annual Savings", f"€ {total_save:,.0f}")
        m3.metric("Portfolio ROI", f"{avg_roi:.1f} Years")
        
        st.divider()
        
        c_bubble, c_table = st.columns([3, 2])
        
        with c_bubble:
            fig_bub = px.scatter(df_measures, x='Inv_EUR', y='Savings_EUR', 
                                 size='Savings_EUR', color='Type', hover_name='Measure',
                                 text='Measure', title="Investment Efficiency Frontier")
            fig_bub.update_traces(textposition='top center')
            fig_bub.add_shape(type="line", x0=0, y0=0, x1=max(df_measures['Inv_EUR']), y1=max(df_measures['Inv_EUR'])/2,
                              line=dict(color="Green", dash="dot"))
            fig_bub.update_layout(template='plotly_white', xaxis_title="Investment (€)", yaxis_title="Savings (€/yr)")
            st.plotly_chart(fig_bub, use_container_width=True)
            
        with c_table:
            st.subheader("Detailed Measures")
            st.dataframe(
                df_measures[['Measure', 'Type', 'Inv_EUR', 'Savings_EUR', 'ROI']].sort_values('ROI'),
                use_container_width=True,
                column_config={
                    "Inv_EUR": st.column_config.NumberColumn("Capex", format="€ %.0f"),
                    "Savings_EUR": st.column_config.NumberColumn("Savings", format="€ %.0f"),
                    "ROI": st.column_config.NumberColumn("Payback", format="%.1f yrs"),
                }
            )

    # ==============================================================================
    # TAB 3: TWIN CALCULATOR (NILM)
    # ==============================================================================
    with tab3:
        st.header("Digital Twin Simulator (NILM)")
        st.markdown("Calibrate the breakdown of energy use by adjusting the virtual loads below.")
        
        if df_energy.empty:
            st.warning("Please upload energy data in the sidebar to use the Twin Calculator.")
        else:
            # 1. Prepare Data (Average Day Profile)
            df_energy['hour'] = df_energy['fecha'].dt.hour
            # Filter options
            day_type = st.radio("Profile Type", ["All Days", "Weekdays Only", "Weekends Only"], horizontal=True)
            
            mask = pd.Series([True]*len(df_energy), index=df_energy.index)
            if day_type == "Weekdays Only": mask = df_energy['fecha'].dt.dayofweek < 5
            if day_type == "Weekends Only": mask = df_energy['fecha'].dt.dayofweek >= 5
            
            df_filtered = df_energy[mask]
            
            # Merge Weather if available
            if not df_weather.empty:
                df_filtered = pd.merge(df_filtered, df_weather, on='fecha', how='left')
            
            # Aggregate to 24h profile
            agg_cols = {'kwh': 'mean'}
            if 'temperatura_c' in df_filtered.columns: agg_cols['temperatura_c'] = 'mean'
            
            df_avg = df_filtered.groupby('hour').agg(agg_cols).reset_index()
            
            # 2. Controls
            with st.expander("🎛️ Simulation Controls", expanded=True):
                col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
                
                with col_ctrl1:
                    st.markdown("**1. Base & Vent**")
                    base_kw = st.number_input("Base Load (kW)", 0.0, 500.0, float(df_avg['kwh'].min()*0.8))
                    vent_kw = st.number_input("Ventilation (kW)", 0.0, 500.0, 20.0)
                    v_s, v_e = st.slider("Vent Schedule", 0, 24, (6, 20))
                    
                with col_ctrl2:
                    st.markdown("**2. Lighting**")
                    light_kw = st.number_input("Lighting Peak (kW)", 0.0, 500.0, 15.0)
                    l_s, l_e = st.slider("Light Schedule", 0, 24, (7, 21))
                    light_fac = st.slider("Usage Factor %", 0.0, 1.0, 0.8)
                    
                with col_ctrl3:
                    st.markdown("**3. HVAC / Thermal**")
                    therm_kw = st.number_input("HVAC Peak (kW)", 0.0, 1000.0, 40.0)
                    t_s, t_e = st.slider("HVAC Schedule", 0, 24, (8, 19))
                    # Weather logic
                    hvac_mode = "Standard"
                    if 'temperatura_c' in df_avg.columns:
                        hvac_mode = st.selectbox("Mode", ["Standard", "Weather"])
            
            # 3. Simulation
            config = {
                'base_kw': base_kw,
                'vent_kw': vent_kw, 'vent_s': v_s, 'vent_e': v_e, 'vent_ru': 1, 'vent_rd': 1,
                'light_kw': light_kw, 'light_s': l_s, 'light_e': l_e, 'light_fac': light_fac, 'light_sec': 0.1,
                'therm_kw': therm_kw, 'therm_s': t_s, 'therm_e': t_e, 'hvac_mode': hvac_mode,
                'set_c': 24, 'set_h': 20, 'therm_sens': 2.0
            }
            
            df_sim = run_twin_simulation(df_avg, config)
            
            # 4. Results
            st.divider()
            
            # Metrics
            real_total = df_sim['kwh'].sum()
            sim_total = df_sim['sim_total'].sum()
            accuracy = 100 - (abs(real_total - sim_total)/real_total * 100)
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Real Avg Daily Energy", f"{real_total:.0f} kWh")
            k2.metric("Simulated Energy", f"{sim_total:.0f} kWh", delta=f"{sim_total-real_total:.0f}")
            k3.metric("Model Accuracy", f"{accuracy:.1f}%")
            
            # Charts
            c_main, c_break = st.columns([2, 1])
            
            with c_main:
                fig_sim = go.Figure()
                # Stacked Simulation
                fig_sim.add_trace(go.Scatter(x=df_sim['hour'], y=df_sim['sim_base'], stackgroup='one', name='Base', line=dict(width=0, color='gray')))
                fig_sim.add_trace(go.Scatter(x=df_sim['hour'], y=df_sim['sim_vent'], stackgroup='one', name='Vent', line=dict(width=0, color='#3498db')))
                fig_sim.add_trace(go.Scatter(x=df_sim['hour'], y=df_sim['sim_light'], stackgroup='one', name='Light', line=dict(width=0, color='#f1c40f')))
                fig_sim.add_trace(go.Scatter(x=df_sim['hour'], y=df_sim['sim_therm'], stackgroup='one', name='HVAC', line=dict(width=0, color='#e74c3c')))
                # Real Line
                fig_sim.add_trace(go.Scatter(x=df_sim['hour'], y=df_sim['kwh'], mode='lines', name='REAL METER', line=dict(color='black', width=3, dash='dot')))
                
                fig_sim.update_layout(title="Load Profile Calibration", xaxis_title="Hour", yaxis_title="kW", height=400, template='plotly_white')
                st.plotly_chart(fig_sim, use_container_width=True)
                
            with c_break:
                # Donut Chart of Simulation
                sim_sums = df_sim[['sim_base', 'sim_vent', 'sim_light', 'sim_therm']].sum().reset_index()
                sim_sums.columns = ['Category', 'kWh']
                fig_pie = px.pie(sim_sums, values='kWh', names='Category', title="Estimated Breakdown", hole=0.4,
                                 color_discrete_map={'sim_base':'gray', 'sim_vent':'#3498db', 'sim_light':'#f1c40f', 'sim_therm':'#e74c3c'})
                st.plotly_chart(fig_pie, use_container_width=True)

    # ==============================================================================
    # TAB 4: ANALYSIS TAB
    # ==============================================================================
    with tab4:
        st.header("Advanced Analysis")
        
        if df_energy.empty:
            st.warning("Upload data to analyze.")
        else:
            # 1. Weather Correlation
            st.subheader("1. Weather Sensitivity (Scatter)")
            if not df_weather.empty:
                # Merge logic
                df_merged = pd.merge(df_energy, df_weather, on='fecha', how='inner')
                if not df_merged.empty:
                    fig_scat = px.scatter(df_merged, x='temperatura_c', y='kwh', opacity=0.5, 
                                          title="Energy vs Temperature", trendline="ols", trendline_color_override="red")
                    st.plotly_chart(fig_scat, use_container_width=True)
                else:
                    st.info("No matching timestamps between Energy and Weather data.")
            else:
                st.info("Upload weather data to see Temperature correlation.")
            
            # 2. Load Duration Curve
            st.subheader("2. Load Duration Curve")
            sorted_load = np.sort(df_energy['kwh'].values)[::-1]
            x_vals = np.arange(len(sorted_load)) / len(sorted_load) * 100
            
            fig_ldc = go.Figure()
            fig_ldc.add_trace(go.Scatter(x=x_vals, y=sorted_load, fill='tozeroy', name='Load Duration'))
            fig_ldc.update_layout(xaxis_title="% of Time", yaxis_title="kW", title="Duration Curve (Grid Sizing)", template='plotly_white')
            st.plotly_chart(fig_ldc, use_container_width=True)
            
            # 3. Quick Stats
            st.subheader("3. Statistical Outliers")
            q95 = df_energy['kwh'].quantile(0.95)
            outliers = df_energy[df_energy['kwh'] > q95]
            st.write(f"Found {len(outliers)} instances where load exceeded {q95:.1f} kW (Top 5%).")
            st.dataframe(outliers.sort_values('kwh', ascending=False).head(10), use_container_width=True)

    # ==============================================================================
    # TAB 5: SOLAR GENERATION
    # ==============================================================================
    with tab5:
        st.header("Solar PV Feasibility")
        st.markdown("Estimate self-consumption potential based on the uploaded load profile.")
        
        if df_energy.empty:
            st.warning("Needs consumption data to calculate self-consumption rate.")
        else:
            c_sol1, c_sol2 = st.columns([1, 2])
            
            with c_sol1:
                st.subheader("System Sizing")
                roof_area = st.number_input("Available Roof Area (m²)", 50, 5000, 400)
                panel_eff = 0.2
                rad = st.slider("Peak Sun Hours (Daily)", 3.0, 7.0, 4.5)
                
                kwp = roof_area * panel_eff # Rough approx 200W/m2
                st.markdown(f"### System Size: **{kwp:.1f} kWp**")
                
                est_gen_daily = kwp * rad
                est_gen_annual = est_gen_daily * 365
                st.metric("Est. Annual Generation", f"{est_gen_annual/1000:.1f} MWh")

            with c_sol2:
                # Simulation on Average Day
                df_avg_sol = df_energy.groupby(df_energy['fecha'].dt.hour)['kwh'].mean().reset_index()
                hours = df_avg_sol['fecha'] # 0-23
                
                # Solar Curve Generator (Gaussian)
                solar_profile = kwp * np.exp(- (hours - 13)**2 / (2 * 2.5**2))
                # Scale to total daily generation input
                # solar_profile = solar_profile / solar_profile.sum() * est_gen_daily
                
                # Calculate Overlap
                df_avg_sol['Solar'] = solar_profile
                df_avg_sol['SelfCons'] = np.minimum(df_avg_sol['kwh'], df_avg_sol['Solar'])
                df_avg_sol['Export'] = np.maximum(0, df_avg_sol['Solar'] - df_avg_sol['kwh'])
                
                # Plot
                fig_sol = go.Figure()
                fig_sol.add_trace(go.Scatter(x=hours, y=df_avg_sol['kwh'], fill='tozeroy', name='Consumption', line=dict(color='gray')))
                fig_sol.add_trace(go.Scatter(x=hours, y=df_avg_sol['Solar'], name='Solar Gen', line=dict(color='#f39c12', width=3)))
                fig_sol.add_trace(go.Scatter(x=hours, y=df_avg_sol['SelfCons'], fill='tozeroy', name='Self-Consumed', line=dict(width=0, color='#27ae60'), opacity=0.6))
                
                fig_sol.update_layout(title="Daily Energy Balance (Average Day)", xaxis_title="Hour", yaxis_title="kW", template='plotly_white')
                st.plotly_chart(fig_sol, use_container_width=True)
                
                # KPIs
                sc_rate = (df_avg_sol['SelfCons'].sum() / df_avg_sol['Solar'].sum()) * 100
                cov_rate = (df_avg_sol['SelfCons'].sum() / df_avg_sol['kwh'].sum()) * 100
                
                k_s1, k_s2 = st.columns(2)
                k_s1.metric("Self-Consumption Rate", f"{sc_rate:.1f}%", help="% of Solar used on site")
                k_s2.metric("Grid Independence", f"{cov_rate:.1f}%", help="% of Load covered by Solar")

if __name__ == "__main__":
    main()
