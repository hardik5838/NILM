## app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import data_utils as du  # Import our custom module

# 1. Page Configuration
st.set_page_config(
    page_title="ISO 50001 EnMS Hub",
    page_icon="♻️",
    layout="wide"
)

# 2. Load Data (Cached)
@st.cache_data
def load_all_data():
    projects_df = du.get_projects_data()
    enpi_df = du.get_enpi_data()
    nc_df = du.get_nc_data()
    seu_df = du.get_seu_list()
    return projects_df, enpi_df, nc_df, seu_df

projects_df, enpi_df, nc_df, seu_df = load_all_data()

# 3. Sidebar - ISO Clause Tracker
with st.sidebar:
    st.header("ISO 50001:2018 Tracker")
    st.info("Documentation Compliance")
    
    clauses = {
        "4. Context of Org": False,
        "5. Leadership": True,
        "6. Planning": True,
        "7. Support": False,
        "8. Operation": True,
        "9. Performance Eval": False,
        "10. Improvement": False
    }
    
    progress = 0
    for clause, status in clauses.items():
        checked = st.checkbox(clause, value=status)
        if checked:
            progress += 1
            
    st.progress(progress / len(clauses))
    st.caption(f"Compliance: {int((progress / len(clauses))*100)}%")

# 4. Main Header
st.title("🏭 ISO 50001 EnMS Project Management Hub")
st.markdown("### PDCA Cycle: Continual Improvement Dashboard")

# 5. PDCA Tabs
tab_plan, tab_do, tab_check, tab_act = st.tabs(["1. PLAN (Strategy)", "2. DO (Implementation)", "3. CHECK (Monitoring)", "4. ACT (Improvement)"])

# --- TAB 1: PLAN ---
with tab_plan:
    st.subheader("Strategic Planning & Energy Review")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### 🎯 Energy Objectives")
        st.write("- **Reduce kWh/unit by 5%** by Q4.")
        st.write("- **Electrify Fleet:** 20% conversion.")
        st.write("- **Solar PV:** Complete Feasibility Study.")
        
        st.warning("⚠️ Next Management Review: Dec 15, 2023")

    with col2:
        st.markdown("#### ⚡ Significant Energy Uses (SEUs)")
        # Display SEU table
        st.dataframe(seu_df, use_container_width=True, hide_index=True)
        
        # Simple Pie Chart for SEUs
        fig_seu = px.pie(seu_df, values='% of Total Consumption', names='SEU Name', title="SEU Breakdown")
        st.plotly_chart(fig_seu, use_container_width=True)

# --- TAB 2: DO ---
with tab_do:
    st.subheader("Project Implementation & Operational Control")
    
    # Metrics Row
    m1, m2, m3 = st.columns(3)
    total_projects = len(projects_df)
    completed = len(projects_df[projects_df['Status'] == 'Complete'])
    m1.metric("Total Projects", total_projects)
    m2.metric("Completed", completed)
    m3.metric("Completion Rate", f"{int((completed/total_projects)*100)}%")
    
    st.divider()

    # Gantt Chart for Project Dependencies
    st.markdown("#### 📅 Implementation Gantt Chart")
    
    # Ensure dates are datetime for Plotly
    fig_gantt = px.timeline(
        projects_df, 
        x_start="Start Date", 
        x_end="End Date", 
        y="Project Name", 
        color="Status",
        hover_data=["Owner", "Dependency"],
        title="Project Timeline & Status",
        color_discrete_map={"Complete": "green", "In Progress": "blue", "On Hold": "orange", "Planned": "gray"}
    )
    fig_gantt.update_yaxes(categoryorder="total ascending") # Organize tasks
    st.plotly_chart(fig_gantt, use_container_width=True)
    
    # Detailed Table
    with st.expander("View Project Details Table"):
        st.dataframe(projects_df, use_container_width=True)

# --- TAB 3: CHECK ---
with tab_check:
    st.subheader("Performance Monitoring & Internal Audit")
    
    col_check1, col_check2 = st.columns([3, 1])
    
    with col_check1:
        st.markdown("#### 📉 EnPI vs. Energy Baseline (EnB)")
        
        # Interactive Line Chart
        fig_enpi = px.line(
            enpi_df, 
            x="Date", 
            y=["Baseline (kWh)", "Actual (kWh)"],
            markers=True,
            title="Electricity Consumption: Actual vs Baseline (2023)"
        )
        # Highlight the savings area roughly
        fig_enpi.update_layout(hovermode="x unified")
        st.plotly_chart(fig_enpi, use_container_width=True)
        
    with col_check2:
        st.markdown("#### 🔍 Audit Status")
        st.success("External Audit Passed: Jan 2023")
        st.info("Internal Audit: In Progress")
        
        total_savings = enpi_df["Savings"].sum()
        st.metric(label="YTD Energy Savings (kWh)", value=f"{total_savings:,.0f}")

# --- TAB 4: ACT ---
with tab_act:
    st.subheader("Non-Conformities & Corrective Actions")
    
    # Filter mechanism
    status_filter = st.multiselect("Filter by Status", options=nc_df["Status"].unique(), default=nc_df["Status"].unique())
    
    filtered_nc = nc_df[nc_df["Status"].isin(status_filter)]
    
    # Styled Dataframe for NCs
    st.markdown("#### Action Tracking Register")
    
    # Color coding function for dataframe
    def color_status(val):
        color = 'red' if val == 'Open' else 'green' if val == 'Closed' else 'orange'
        return f'color: {color}'

    st.dataframe(
        filtered_nc.style.map(color_status, subset=['Status']),
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    st.markdown("#### ➕ Log New Improvement Idea")
    with st.form("new_idea_form"):
        col_form1, col_form2 = st.columns(2)
        with col_form1:
            st.text_input("Improvement Opportunity")
            st.selectbox("Source", ["Employee Suggestion", "Audit Finding", "Management Review"])
        with col_form2:
            st.text_input("Potential Savings (Estimated)")
            st.date_input("Target Date")
            
        st.form_submit_button("Submit to Register")
