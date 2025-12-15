import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# --------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Plan Net Zero | Asepeyo",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Corporate Identity (Asepeyo Blue & Clean Layout)
st.markdown("""
    <style>
    /* Main Layout */
    .main {background-color: #f8f9fa;}
    .block-container {padding-top: 1rem; padding-bottom: 3rem;}
    
    /* Typography */
    h1 {color: #003366; font-family: 'Helvetica', sans-serif; font-weight: 700;}
    h2 {color: #004d99; font-family: 'Helvetica', sans-serif; border-bottom: 2px solid #003366; padding-bottom: 10px;}
    h3 {color: #444; font-size: 1.4rem;}
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    div[data-testid="stMetricLabel"] {color: #666; font-size: 0.9rem;}
    div[data-testid="stMetricValue"] {color: #003366; font-weight: bold; font-size: 1.8rem;}
    
    /* Custom Alert/Info Box */
    .insight-box {
        background-color: #e8f4f8;
        border-left: 5px solid #003366;
        padding: 15px;
        border-radius: 5px;
        color: #003366;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# 2. DATA GENERATION ENGINE (Mimicking PDF Data)
# --------------------------------------------------------------------------
@st.cache_data
def get_pdf_data():
    """Generates static data frames matching the PDF content."""
    
    # 1. Top Consumers (Page 4 of PDF)
    centers = {
        'Chamartín': 2500000,
        'Hospital Sevilla': 1900000,
        'Hospital Coslada': 1850000,
        'Sant Cugat': 900000,
        'Vía Augusta 36': 450000,
        'Girona': 380000,
        'Cartuja': 350000,
        'Valencia Cid': 320000
    }
    df_centers = pd.DataFrame(list(centers.items()), columns=['Center', 'kWh'])
    
    # 2. Investment Measures (Page 10/12)
    measures = [
        {'Measure': 'Solar Panels', 'Savings_EUR': 180376, 'Inv_EUR': 650000, 'Type': 'Generation'},
        {'Measure': 'Energy Mgmt System', 'Savings_EUR': 75190, 'Inv_EUR': 150000, 'Type': 'Control'},
        {'Measure': 'LED Retrofit', 'Savings_EUR': 68551, 'Inv_EUR': 84415, 'Type': 'Efficiency'},
        {'Measure': 'Setpoint Adjustment', 'Savings_EUR': 55974, 'Inv_EUR': 0, 'Type': 'Optimization'},
        {'Measure': 'Air Curtains', 'Savings_EUR': 36873, 'Inv_EUR': 45000, 'Type': 'Efficiency'},
        {'Measure': 'Phantom Load Kill', 'Savings_EUR': 34873, 'Inv_EUR': 2572, 'Type': 'Optimization'}
    ]
    df_measures = pd.DataFrame(measures)
    df_measures['ROI_Years'] = df_measures['Inv_EUR'] / df_measures['Savings_EUR']
    
    return df_centers, df_measures

def generate_dynamic_curve(base_kw, hvac_kw, light_kw, 
                          opt_base_pct, opt_hvac_pct, opt_light_pct):
    """
    Generates a 24h curve.
    Inputs are Base Load, HVAC Peak, Lighting Peak.
    Optimization sliders (0-100%) reduce these loads.
    """
    hours = np.arange(24)
    
    # --- 1. BASELINE SHAPES ---
    # Base: Constant 24h
    curve_base = np.full(24, base_kw)
    
    # HVAC: Bell curve from 8am to 8pm
    curve_hvac = hvac_kw * np.exp(- (hours - 14)**2 / (2 * 2.5**2))
    curve_hvac = np.where(curve_hvac < 0.1, 0, curve_hvac) # Cutoff
    
    # Lighting: Plateau from 7am to 9pm
    curve_light = np.zeros(24)
    mask_light = (hours >= 7) & (hours <= 21)
    curve_light[mask_light] = light_kw
    
    total_original = curve_base + curve_hvac + curve_light
    
    # --- 2. OPTIMIZATION LOGIC ---
    # Base reduction (Phantom loads)
    curve_base_opt = curve_base * (1 - opt_base_pct/100)
    
    # HVAC reduction (Setpoint adjustment + VFD)
    curve_hvac_opt = curve_hvac * (1 - opt_hvac_pct/100)
    
    # Lighting reduction (LED + Sensors)
    curve_light_opt = curve_light * (1 - opt_light_pct/100)
    
    total_optimized = curve_base_opt + curve_hvac_opt + curve_light_opt
    
    # DataFrame for plotting
    df = pd.DataFrame({
        'Hour': hours,
        'Original': total_original,
        'Optimized': total_optimized,
        'Base': curve_base_opt,
        'HVAC': curve_hvac_opt,
        'Lighting': curve_light_opt
    })
    
    return df, total_original.sum(), total_optimized.sum()

# --------------------------------------------------------------------------
# 3. MAIN APPLICATION
# --------------------------------------------------------------------------
def main():
    # Load Data
    df_centers, df_measures = get_pdf_data()
    
    # Header Section
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("PLAN NET ZERO O.")
        st.caption("Strategic Energy Efficiency & Decarbonization Roadmap")
    with c2:
        # Placeholder for Logo
        st.markdown("<h3 style='text-align: right; color: #003366;'>ASEPEYO</h3>", unsafe_allow_html=True)

    # Tabs for Narrative Structure
    tab1, tab2, tab3 = st.tabs(["1. The Imperative (Strategy)", "2. The Engine (Real-time Opt)", "3. The Roadmap (Investment)"])

    # ==============================================================================
    # TAB 1: STRATEGY & DIAGNOSIS
    # ==============================================================================
    with tab1:
        st.markdown("## 1. The Financial Imperative")
        
        # Key Metrics Row (From PDF Page 3)
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Historical Savings Lost", "€ 1.1 M", delta="- Inaction Cost", delta_color="inverse")
        col_m2.metric("Target Annual Savings", "€ 650 k", delta="+ Potential Cashflow")
        col_m3.metric("Top 5 Centers", "70%", "of Total Consumption")
        
        st.divider()
        
        col_text, col_chart = st.columns([1, 2])
        
        with col_text:
            st.markdown("""
            <div class="insight-box">
            <b>The Carnot Principle:</b><br>
            We approach energy not as a fixed cost, but as a thermodynamic engine. 
            Our goal is to maximize the work (utility) extracted from every Euro invested.
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            **Strategic Pillars:**
            1.  **Monitor:** Digital Twin foundation.
            2.  **Optimize:** Zero-cost measures for immediate cash flow.
            3.  **Generate:** Reinvest savings into Infrastructure & Solar.
            """)
            
        with col_chart:
            st.markdown("#### Consumption Distribution (Pareto)")
            fig_centers = px.bar(df_centers.sort_values('kWh', ascending=True), 
                                 x='kWh', y='Center', orientation='h',
                                 text_auto='.2s', color='kWh', color_continuous_scale='Blues')
            fig_centers.update_layout(template='plotly_white', height=350, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig_centers, use_container_width=True)

    # ==============================================================================
    # TAB 2: DYNAMIC OPTIMIZATION (THE DEMO)
    # ==============================================================================
    with tab2:
        st.markdown("## 2. Real-Time Optimization Simulator")
        st.markdown("Demonstrating the **'Plan Cero'** effect on a typical facility (e.g., Vía Augusta 36).")
        
        # --- INPUTS ---
        with st.expander("⚙️ Optimization Levers (Adjust to see impact)", expanded=True):
            c_in1, c_in2, c_in3 = st.columns(3)
            
            # Baseline Parameters (Hidden logic for typical building)
            base_load = 50 # kW
            hvac_peak = 80 # kW
            light_peak = 40 # kW
            
            with c_in1:
                st.markdown("**Phase 1: Ghost Loads**")
                st.caption("Timers, Regulators, Standby Killers")
                opt_base = st.slider("Reduction %", 0, 50, 0, help="PDF: Eliminating 22kW of standby A/C")
                
            with c_in2:
                st.markdown("**Phase 2: Thermal Control**")
                st.caption("Setpoints (21-26°C), Free Cooling")
                opt_hvac = st.slider("Efficiency Gain %", 0, 60, 0, help="PDF: Cubic law - 20% speed reduction = 50% savings")
                
            with c_in3:
                st.markdown("**Phase 3: Lighting**")
                st.caption("LED Retrofit + Sensors")
                opt_light = st.slider("Efficiency Gain %", 0, 70, 0, help="PDF: Switching to LED and demand control")

        # --- CALCULATION ---
        df_curve, kwh_orig, kwh_opt = generate_dynamic_curve(base_load, hvac_peak, light_peak, opt_base, opt_hvac, opt_light)
        
        savings_kwh = kwh_orig - kwh_opt
        savings_pct = (savings_kwh / kwh_orig) * 100
        savings_eur = savings_kwh * 0.20 * 365 # Approx annual savings assuming 0.20 eur/kwh and 365 days similar profile
        
        # --- RESULTS ---
        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Daily Energy (Original)", f"{kwh_orig:,.0f} kWh")
        m2.metric("Daily Energy (Optimized)", f"{kwh_opt:,.0f} kWh", delta=f"-{savings_pct:.1f}%")
        m3.metric("Projected Annual Savings", f"€ {savings_eur:,.0f}", delta="Cash Flow")
        m4.metric("Carbon Avoided", f"{(savings_kwh*0.25*365)/1000:.1f} tCO2", delta="Annual")

        # --- VISUALS ---
        col_main_chart, col_donut = st.columns([2, 1])
        
        with col_main_chart:
            st.markdown("#### Daily Load Curve Impact")
            fig_area = go.Figure()
            
            # Original Line
            fig_area.add_trace(go.Scatter(x=df_curve['Hour'], y=df_curve['Original'], 
                                          mode='lines', name='Baseline',
                                          line=dict(color='gray', width=2, dash='dot')))
            
            # Optimized Stack
            fig_area.add_trace(go.Scatter(x=df_curve['Hour'], y=df_curve['Base'], 
                                          stackgroup='one', name='Base Load (Opt)', line=dict(width=0, color='#3498db')))
            fig_area.add_trace(go.Scatter(x=df_curve['Hour'], y=df_curve['Lighting'], 
                                          stackgroup='one', name='Lighting (Opt)', line=dict(width=0, color='#f1c40f')))
            fig_area.add_trace(go.Scatter(x=df_curve['Hour'], y=df_curve['HVAC'], 
                                          stackgroup='one', name='HVAC (Opt)', line=dict(width=0, color='#e74c3c')))
            
            fig_area.update_layout(height=400, xaxis_title="Hour of Day", yaxis_title="Power (kW)", 
                                   template='plotly_white', hovermode="x unified", legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_area, use_container_width=True)
            
        with col_donut:
            st.markdown("#### Optimized Energy Mix")
            # Calculate mix for the optimized scenario
            mix_data = pd.DataFrame([
                {'Source': 'Base Load', 'kWh': df_curve['Base'].sum()},
                {'Source': 'Lighting', 'kWh': df_curve['Lighting'].sum()},
                {'Source': 'HVAC', 'kWh': df_curve['HVAC'].sum()}
            ])
            fig_donut = px.pie(mix_data, values='kWh', names='Source', hole=0.5, 
                               color='Source',
                               color_discrete_map={'Base Load':'#3498db', 'Lighting':'#f1c40f', 'HVAC':'#e74c3c'})
            fig_donut.update_layout(height=350, margin=dict(l=0,r=0,b=0,t=30), showlegend=False)
            fig_donut.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_donut, use_container_width=True)

    # ==============================================================================
    # TAB 3: ROADMAP & INVESTMENT
    # ==============================================================================
    with tab3:
        st.markdown("## 3. Implementation Roadmap")
        
        col_inv1, col_inv2 = st.columns([2, 1])
        
        with col_inv1:
            st.markdown("#### Measure Prioritization (ROI vs Impact)")
            
            # Scatter Plot for Measures
            fig_bubble = px.scatter(df_measures, x='Inv_EUR', y='Savings_EUR', 
                                    size='Savings_EUR', color='Type',
                                    text='Measure', hover_data=['ROI_Years'],
                                    labels={'Inv_EUR': 'Investment (€)', 'Savings_EUR': 'Annual Savings (€)'},
                                    title="Investment Efficiency Frontier")
            
            fig_bubble.update_traces(textposition='top center')
            fig_bubble.update_layout(template='plotly_white', height=500)
            # Add a reference line for 2-year ROI
            fig_bubble.add_shape(type="line", x0=0, y0=0, x1=300000, y1=150000, 
                                 line=dict(color="green", width=1, dash="dot"))
            fig_bubble.add_annotation(x=280000, y=140000, text="2-Year ROI Line", showarrow=False, font=dict(color="green"))
            
            st.plotly_chart(fig_bubble, use_container_width=True)
            
        with col_inv2:
            st.markdown("#### Solar Potential Calculator")
            st.caption("Based on Madrid/Barcelona Irradiance")
            
            roof_area = st.number_input("Available Roof Area (m²)", 100, 5000, 500)
            solar_power_kwp = roof_area * 0.20 # approx 200W/m2
            
            # Simple production calc
            daily_production = solar_power_kwp * 4.5 # 4.5 Peak Sun Hours avg
            annual_production = daily_production * 365
            annual_saving_est = annual_production * 0.15 # 0.15 eur/kwh avoided cost
            
            st.markdown(f"""
            <div style="background-color:#fff; padding:15px; border-radius:10px; border:1px solid #ddd;">
                <h2 style="text-align:center; color:#f39c12;">{solar_power_kwp:.1f} kWp</h2>
                <p style="text-align:center;">System Size</p>
                <hr>
                <div style="display:flex; justify-content:space-between;">
                    <span>Annual Gen:</span>
                    <strong>{annual_production/1000:.1f} MWh</strong>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span>Savings:</span>
                    <strong>€ {annual_saving_est:,.0f}/yr</strong>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span>Est. CAPEX:</span>
                    <strong>€ {solar_power_kwp * 800:,.0f}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("💡 Strategic Note: Solar projects not only reduce OpEx but can generate Energy Attribute Certificates (CAEs).")

        st.markdown("### Action Plan Status")
        # Simple dataframe display for the status table
        plan_data = {
            'Phase': ['1. Monitoring', '1. Monitoring', '2. Optimization', '2. Optimization', '3. Generation'],
            'Action': ['Deploy Digital Twin', 'Set KPI Dashboards', 'Thermostat Policy', 'Ghost Load Timers', 'Rooftop Solar'],
            'Status': ['Done', 'In Progress', 'Ready to Start', 'Ready to Start', 'Planning'],
            'Owner': ['DAF Equip', 'IT', 'Maintenance', 'Maintenance', 'Engineering']
        }
        st.dataframe(pd.DataFrame(plan_data), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
