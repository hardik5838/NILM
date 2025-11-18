## data_utils.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_projects_data():
    """
    Simulates fetching project data from a database/sheet.
    Includes Start/End dates and Status for Gantt charts.
    """
    data = {
        "Project Name": ["BMS Monitoring Upgrade", "LED Retrofit - Warehouse", "Boiler Economizer", "Staff Awareness Training", "ISO 50001 Internal Audit"],
        "Owner": ["J. Doe", "M. Smith", "T. Engineer", "HR Dept", "Quality Team"],
        "Start Date": [datetime(2023, 1, 10), datetime(2023, 3, 1), datetime(2023, 6, 15), datetime(2023, 2, 1), datetime(2023, 11, 1)],
        "End Date": [datetime(2023, 4, 30), datetime(2023, 5, 15), datetime(2023, 9, 30), datetime(2023, 12, 20), datetime(2023, 12, 15)],
        "Status": ["Complete", "Complete", "In Progress", "On Hold", "Planned"],
        "Phase": ["Do", "Do", "Do", "Do", "Check"],
        "Dependency": ["None", "BMS Monitoring Upgrade", "None", "None", "All Projects"]
    }
    return pd.DataFrame(data)

def get_enpi_data():
    """
    Generates Energy Performance Indicator (EnPI) data vs Energy Baseline (EnB).
    """
    dates = pd.date_range(start="2023-01-01", end="2023-12-01", freq="MS")
    
    # Simulate data: Baseline is somewhat static, Actual fluctuates
    df = pd.DataFrame({
        "Date": dates,
        "Baseline (kWh)": [50000, 48000, 45000, 42000, 40000, 38000, 39000, 41000, 43000, 46000, 49000, 52000],
        "Actual (kWh)":   [49500, 47000, 46000, 41000, 38000, 36000, 37500, 40500, 42000, 44000, 47000, 50000]
    })
    # Calculate savings
    df["Savings"] = df["Baseline (kWh)"] - df["Actual (kWh)"]
    return df

def get_nc_data():
    """
    Simulates Non-Conformity (NC) and Corrective Action data (ACT Phase).
    """
    data = {
        "ID": ["NC-001", "NC-002", "NC-003"],
        "Description": ["Missing calibration records for gas meter", "Energy Policy not communicated to contractors", "HVAC setpoints overridden manually"],
        "Root Cause": ["Procedure gap", "Training gap", "Operational control failure"],
        "Action Owner": ["Maintenance Mgr", "HR / EHS", "Facility Mgr"],
        "Due Date": ["2023-10-15", "2023-11-01", "2023-09-30"],
        "Status": ["Closed", "Open", "Effectiveness Check Pending"]
    }
    return pd.DataFrame(data)

def get_seu_list():
    """Returns Significant Energy Uses (SEUs)"""
    return pd.DataFrame({
        "SEU Name": ["Compressed Air System", "Chillers / HVAC", "Process Furnace A"],
        "Energy Type": ["Electricity", "Electricity", "Natural Gas"],
        "% of Total Consumption": [25, 30, 20]
    })
