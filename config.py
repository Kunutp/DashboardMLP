"""
Configuration file for Water Quality Dashboard
"""

import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent

# Database Configuration
DATABASE_PATH = PROJECT_ROOT / "data" / "water_quality.db"

# Sampling Point Groups
SAMPLING_GROUPS = {
    "RW": ["RW", "RW 1", "RW2"],
    "RW_MAIN": ["RW"],  # Special: Only "RW" (not "RW 1", "RW2")
    "CW": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10",
           "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C19", "C20",
           "C21", "C22", "C23", "C24", "CW1", "CW2"],
    "CW_MAIN": ["CW"],  # Special: Only "CW" (not CW1, CW2, C1-C24)
    "FW": ["FW1", "FW2"],
    "FW_MAIN": ["FW"],  # Special: Only "FW" (not FW1, FW2)
    "TW": ["TW1", "TW2", "TW3", "DPS1", "DPS2"],
    "TW_MAIN": ["TW"]  # Special: Only "TW" (not TW1-3, DPS1-2)
}

# Custom sampling point mapping for specific parameters
# Format: {parameter: {group: [sampling_points]}}
PARAMETER_SAMPLING_POINT_OVERRIDE = {
    "O2 Consume": {
        "RW": ["RW"],       # Use only "RW" for O2 Consume in raw water
        "CW": ["CW"],       # Use only "CW" for O2 Consume in clarifier water
        "FW": ["FW"],       # Use only "FW" for O2 Consume in filtered water
        "TW": ["TW"]        # Use only "TW" for O2 Consume in treated water
    },
    "NH3-N": {
        "TW": ["TW"]
    },
    "Color": {
        "TW": ["TW"]
    },
    "Conductivity": {
        "TW": ["TW"]
    },
    "SS": {
        "TW": ["TW"]
    }
}

# All Parameters
PARAMETERS = [
    "Turbidity",
    "Alkalinity",
    "pH",
    "Free Residual Cl2",
    "Chemical Dosage",
    "% Sludge",
    "O2 Consume",
    "Conductivity",
    "DO",
    "Color",
    "SS",
    "NH3-N"
]

# Default Thresholds (can be overridden in UI)
DEFAULT_THRESHOLDS = {
    "turbidity_tw_max": 1.00,  # NTU
    "cl2_min": 0.8,             # mg/L
    "ph_min": 6.5,
    "ph_max": 8.5,
    "rw_turbidity_threshold": 100.0  # NTU (changed to float)
}

# Time Periods
TIME_PERIODS = ["00.00-08.00", "08.00-16.00", "16.00-24.00"]

# App Configuration
APP_TITLE = "💧 Monthly Water Quality Report Dashboard"
APP_LAYOUT = "wide"
