import streamlit as st
import pandapower as pp
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Gracia DSM Validation Dashboard", layout="wide")
st.title("⚡ Gracia Public Building DSM & Grid Validation (The Oasis Project)")
st.markdown("Validating load-shifting and peak-clipping capabilities of public infrastructure using Grey-Box flexibility.")

# --- SIDEBAR PARAMETERS ---
st.sidebar.header("⚙️ Optimization Parameters")
st.sidebar.markdown("Adjust the flexibility of the building's subsystems to simulate the Oasis algorithm.")

# Sliders for load reduction (simulating the Oasis Optimization Module)
hvac_reduction = st.sidebar.slider("HVAC Load Reduction (%)", 0, 100, 20) / 100.0
vent_reduction = st.sidebar.slider("Ventilation Load Reduction (%)", 0, 100, 10) / 100.0
light_reduction = st.sidebar.slider("Lighting Load Reduction (%)", 0, 100, 30) / 100.0

st.sidebar.header("📊 Grid & Tariff Settings")
transformer_capacity_kva = st.sidebar.number_input("Transformer Capacity (kVA)", value=250)
contracted_power_kw = st.sidebar.number_input("Contracted Power P1 (kW)", value=330.0)

# Tariffs
price_p1 = st.sidebar.number_input("P1 Peak Price (€/kWh)", value=0.35)
price_int = st.sidebar.number_input("Intermediate Price (€/kWh)", value=0.25)
price_p6 = st.sidebar.number_input("P6 Valley Price (€/kWh)", value=0.15)

# --- DATA SIMULATION ---
# Simulating a 24-hour profile based on the Oasis Project pilot (Via Augusta, 36)
hours = np.arange(24)

# Synthetic baseline components (in kW)
base_load = np.full(24, 30.0)
lighting_load = np.array([5, 5, 5, 5, 5, 10, 30, 40, 45, 45, 45, 45, 45, 40, 40, 35, 30, 20, 15, 10, 5, 5, 5, 5])
ventilation_load = np.array([5, 5, 5, 5, 5, 10, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 10, 5, 5, 5, 5, 5, 5])
hvac_load = np.array([0, 0, 0, 0, 0, 20, 60, 80, 90, 100, 110, 110, 100, 90, 80, 60, 40, 20, 10, 0, 0, 0, 0, 0])

total_baseline_kw = base_load + lighting_load + ventilation_load + hvac_load

# Apply Flexibility (Oasis Optimization)
# For this simulation, we heavily target the P1 hours (10:00 - 14:00) for maximum reduction
optimized_hvac = np.where((hours >= 10) & (hours <= 14), hvac_load * (1 - hvac_reduction), hvac_load)
optimized_vent = np.where((hours >= 10) & (hours <= 14), ventilation_load * (1 - vent_reduction), ventilation_load)
optimized_light = np.where((hours >= 10) & (hours <= 14), lighting_load * (1 - light_reduction), lighting_load)

# Simulating the P6 (Night) Pre-cooling "charge" (increasing load slightly at night)
optimized_hvac = np.where((hours >= 2) & (hours <= 6), optimized_hvac + 15, optimized_hvac)

total_optimized_kw = base_load + optimized_light + optimized_vent + optimized_hvac

# Tariff mapping (Simplified 3.0TD: P6=0-8h, P1=10-14h, Int=Rest)
def get_price(h):
    if 0 <= h < 8: return price_p6
    elif 10 <= h <= 14: return price_p1
    else: return price_int

prices = np.array([get_price(h) for h in hours])
baseline_cost = np.sum(total_baseline_kw * prices)
optimized_cost = np.sum(total_optimized_kw * prices)

# --- PANDAPOWER GRID SIMULATION ---
def run_grid_simulation(load_profile_kw):
    net = pp.create_empty_network()
    
    # Create buses
    b_ext = pp.create_bus(net, vn_kv=20., name="External Grid Bus")
    b_lv = pp.create_bus(net, vn_kv=0.4, name="Building LV Bus")
    
    # Create external grid
    pp.create_ext_grid(net, bus=b_ext)
    
    # Create transformer based on user input (250 kVA)
    # Using standard parameters, adjusting sn_mva
    pp.create_transformer_from_parameters(net, hv_bus=b_ext, lv_bus=b_lv, sn_mva=transformer_capacity_kva/1000.0, 
                                          vn_hv_kv=20., vn_lv_kv=0.4, vkr_percent=1.0, vk_percent=4.0, 
                                          pfe_kw=1.0, i0_percent=0.1, name="Gracia Local Trafo")
    
    # Create load (placeholder to be updated in the loop)
    load_idx = pp.create_load(net, bus=b_lv, p_mw=0, q_mvar=0, name="Via Augusta 36")
    
    trafo_loading = []
    
    for p_kw in load_profile_kw:
        # Update load (assuming 0.95 power factor)
        p_mw = p_kw / 1000.0
        q_mvar = p_mw * np.tan(np.arccos(0.95))
        net.load.at[load_idx, 'p_mw'] = p_mw
        net.load.at[load_idx, 'q_mvar'] = q_mvar
        
        # Run power flow
        try:
            pp.runpp(net)
            loading_percent = net.res_trafo.loading_percent.iloc[0]
        except:
            loading_percent = 100.0 # Default to max if non-convergent
            
        trafo_loading.append(loading_percent)
        
    return trafo_loading

baseline_trafo_loading = run_grid_simulation(total_baseline_kw)
optimized_trafo_loading = run_grid_simulation(total_optimized_kw)

# Count violations
base_violations = sum(1 for load in baseline_trafo_loading if load > 100)
opt_violations = sum(1 for load in optimized_trafo_loading if load > 100)

# --- DASHBOARD RENDER ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Max Peak (Baseline)", f"{max(total_baseline_kw):.1f} kW")
col2.metric("Max Peak (Optimized)", f"{max(total_optimized_kw):.1f} kW", f"{max(total_optimized_kw)-max(total_baseline_kw):.1f} kW")
col3.metric("Daily Cost (Baseline)", f"€{baseline_cost:.2f}")
col4.metric("Daily Cost (Optimized)", f"€{optimized_cost:.2f}", f"€{optimized_cost-baseline_cost:.2f}")

st.markdown("---")

# Chart 1: Load Profile Comparison
st.subheader("📈 Load Profile: Static vs. Grid-Interactive (GEB)")
fig_load = go.Figure()
fig_load.add_trace(go.Scatter(x=hours, y=total_baseline_kw, mode='lines', name='Baseline Load', line=dict(color='red', dash='dash')))
fig_load.add_trace(go.Scatter(x=hours, y=total_optimized_kw, mode='lines', name='Optimized Load (Oasis)', fill='tozeroy', line=dict(color='green')))
fig_load.add_shape(type="rect", x0=10, y0=0, x1=14, y1=max(total_baseline_kw)+20, fillcolor="orange", opacity=0.2, layer="below", line_width=0)
fig_load.add_annotation(x=12, y=max(total_baseline_kw)+10, text="High Cost Tariff (P1)", showarrow=False)

fig_load.update_layout(xaxis_title="Hour of Day", yaxis_title="Power Demand (kW)", height=400, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig_load, use_container_width=True)

# Chart 2: Transformer Stress Validation
st.subheader("🔋 Transformer Thermal Stress (250 kVA Limit)")
col_a, col_b = st.columns([3, 1])

with col_a:
    fig_trafo = go.Figure()
    fig_trafo.add_trace(go.Bar(x=hours, y=baseline_trafo_loading, name="Baseline Loading %", marker_color='indianred'))
    fig_trafo.add_trace(go.Bar(x=hours, y=optimized_trafo_loading, name="Optimized Loading %", marker_color='lightseagreen'))
    fig_trafo.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Transformer Capacity Limit (100%)")
    fig_trafo.update_layout(barmode='group', xaxis_title="Hour of Day", yaxis_title="Transformer Loading (%)", height=400, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig_trafo, use_container_width=True)

with col_b:
    st.markdown("### Peak Violations")
    st.metric("Violations (Baseline)", base_violations)
    st.metric("Violations (Optimized)", opt_violations, delta=opt_violations-base_violations, delta_color="inverse")
    
    st.markdown("""
    **Analysis:** By applying Grey-Box load shifting (pre-cooling during P6 and shedding during P1), we actively reduce the localized thermal stress on the 250 kVA distribution transformer.
    """)
