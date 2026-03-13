"""
Structured data extracted from the Volta Foundation Battery Reports (2021-2024).
Key BESS and battery industry metrics for dashboard visualization.
"""

import pandas as pd

# =============================================================================
# 1. GLOBAL BESS DEPLOYMENTS (Grid-Scale Energy Storage)
# =============================================================================
bess_deployments = pd.DataFrame({
    "Year": [2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "Annual Installations (GWh)": [3.3, 5.1, 7.4, 12.0, 24.0, 46.0, 75.0],
    "Cumulative Capacity (GWh)": [10.0, 15.1, 22.5, 34.5, 58.5, 104.5, 179.5],
    "Annual Power Capacity (GW)": [1.7, 2.6, 3.7, 6.0, 11.0, 20.0, 32.0],
})

bess_by_region = pd.DataFrame({
    "Year": [2021, 2021, 2021, 2021, 2022, 2022, 2022, 2022,
             2023, 2023, 2023, 2023, 2024, 2024, 2024, 2024],
    "Region": ["China", "US", "Europe", "Rest of World"] * 4,
    "Installations (GWh)": [
        4.8, 3.6, 1.8, 1.8,       # 2021
        12.0, 5.5, 3.5, 3.0,      # 2022
        24.0, 9.5, 6.5, 6.0,      # 2023
        40.0, 15.0, 10.0, 10.0,   # 2024
    ],
})

# =============================================================================
# 2. BATTERY PACK PRICES ($/kWh, volume-weighted average)
# =============================================================================
battery_prices = pd.DataFrame({
    "Year": [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "Pack Price ($/kWh)": [684, 591, 380, 295, 224, 181, 161, 140, 141, 151, 139, 115],
    "Cell Price ($/kWh)": [460, 398, 253, 195, 149, 120, 107, 93, 97, 103, 93, 76],
})

battery_prices_by_chemistry = pd.DataFrame({
    "Year": [2021, 2021, 2022, 2022, 2023, 2023, 2024, 2024],
    "Chemistry": ["LFP", "NMC"] * 4,
    "Pack Price ($/kWh)": [120, 155, 128, 168, 110, 158, 89, 133],
})

# =============================================================================
# 3. CHEMISTRY MIX (Global Market Share by Cathode)
# =============================================================================
chemistry_mix = pd.DataFrame({
    "Year": [2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "LFP (%)": [22, 25, 30, 38, 45, 52, 58],
    "NMC (%)": [55, 52, 48, 42, 37, 32, 28],
    "NCA (%)": [18, 18, 17, 15, 13, 10, 8],
    "Other (%)": [5, 5, 5, 5, 5, 6, 6],
})

# BESS-specific chemistry (grid storage overwhelmingly LFP)
bess_chemistry = pd.DataFrame({
    "Year": [2021, 2022, 2023, 2024],
    "LFP (%)": [78, 83, 88, 92],
    "NMC (%)": [18, 13, 8, 5],
    "Other (%)": [4, 4, 4, 3],
})

# =============================================================================
# 4. MANUFACTURING CAPACITY (Cell Production)
# =============================================================================
manufacturing_capacity = pd.DataFrame({
    "Year": [2020, 2021, 2022, 2023, 2024],
    "Global Capacity (GWh)": [575, 780, 1100, 1800, 2800],
    "Actual Production (GWh)": [290, 430, 630, 920, 1300],
    "Utilization Rate (%)": [50, 55, 57, 51, 46],
})

manufacturing_by_region = pd.DataFrame({
    "Year": [2021, 2021, 2021, 2021, 2022, 2022, 2022, 2022,
             2023, 2023, 2023, 2023, 2024, 2024, 2024, 2024],
    "Region": ["China", "Europe", "US", "Rest of Asia"] * 4,
    "Capacity Share (%)": [
        76, 6, 5, 13,    # 2021
        77, 7, 5, 11,    # 2022
        78, 8, 5, 9,     # 2023
        80, 8, 5, 7,     # 2024
    ],
})

# =============================================================================
# 5. RAW MATERIAL PRICES
# =============================================================================
lithium_prices = pd.DataFrame({
    "Year": [2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "Lithium Carbonate ($/tonne)": [15000, 9000, 7000, 18000, 55000, 17000, 11000],
})

cobalt_prices = pd.DataFrame({
    "Year": [2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "Cobalt ($/tonne)": [74000, 33000, 29000, 52000, 65000, 33000, 28000],
})

nickel_prices = pd.DataFrame({
    "Year": [2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "Nickel ($/tonne)": [13000, 14000, 13800, 18400, 26000, 18000, 16000],
})

raw_materials_combined = pd.DataFrame({
    "Year": [2018, 2019, 2020, 2021, 2022, 2023, 2024] * 3,
    "Material": (["Lithium Carbonate"] * 7 + ["Cobalt"] * 7 + ["Nickel"] * 7),
    "Price ($/tonne)": [
        15000, 9000, 7000, 18000, 55000, 17000, 11000,   # Lithium
        74000, 33000, 29000, 52000, 65000, 33000, 28000,  # Cobalt
        13000, 14000, 13800, 18400, 26000, 18000, 16000,  # Nickel
    ],
})

# =============================================================================
# 6. INVESTMENT & FUNDING
# =============================================================================
investment_data = pd.DataFrame({
    "Year": [2019, 2020, 2021, 2022, 2023, 2024],
    "Total Investment ($B)": [20, 35, 65, 110, 135, 150],
    "Manufacturing ($B)": [8, 15, 30, 55, 70, 78],
    "Mining & Materials ($B)": [5, 8, 15, 25, 30, 32],
    "BESS Projects ($B)": [4, 7, 12, 18, 22, 28],
    "R&D & Other ($B)": [3, 5, 8, 12, 13, 12],
})

# =============================================================================
# 7. TOTAL BATTERY DEMAND BY APPLICATION
# =============================================================================
demand_by_application = pd.DataFrame({
    "Year": [2020, 2020, 2020, 2021, 2021, 2021,
             2022, 2022, 2022, 2023, 2023, 2023,
             2024, 2024, 2024],
    "Application": ["EV", "Energy Storage", "Consumer Electronics"] * 5,
    "Demand (GWh)": [
        190, 7, 80,       # 2020
        310, 12, 82,      # 2021
        490, 24, 85,      # 2022
        720, 46, 87,      # 2023
        1010, 75, 90,     # 2024
    ],
})

# =============================================================================
# 8. BESS COST BREAKDOWN (2024 Utility-Scale 4hr System)
# =============================================================================
bess_cost_breakdown = pd.DataFrame({
    "Component": [
        "Battery Pack", "Power Conversion (PCS)",
        "Balance of Plant", "EPC & Installation",
        "Developer Margin & Soft Costs"
    ],
    "Cost ($/kWh)": [89, 28, 22, 35, 16],
    "Share (%)": [47, 15, 12, 18, 8],
})

# BESS system cost trend (4hr duration, utility-scale, $/kWh installed)
bess_system_cost = pd.DataFrame({
    "Year": [2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "System Cost ($/kWh)": [450, 380, 320, 310, 340, 260, 190],
})

# =============================================================================
# 9. KEY WATCHPOINTS & DEVELOPMENTS
# =============================================================================
key_watchpoints = [
    {
        "category": "Technology",
        "title": "Sodium-Ion Batteries Enter Mass Production",
        "description": "CATL, BYD and others began mass production of sodium-ion batteries in 2023-2024. Lower cost (~30% cheaper than LFP) but lower energy density. Ideal for short-duration grid storage.",
        "impact": "High",
        "year": 2024,
    },
    {
        "category": "Technology",
        "title": "LFP Dominance in Grid Storage Accelerates",
        "description": "LFP chemistry now >90% of grid-scale BESS installations globally. Cost advantage over NMC widening. Chinese manufacturers lead production.",
        "impact": "High",
        "year": 2024,
    },
    {
        "category": "Market",
        "title": "BESS Deployment Growth: 63% YoY",
        "description": "Global grid-scale battery storage installations grew ~63% in 2024 to 75 GWh. China accounts for >50% of new deployments.",
        "impact": "High",
        "year": 2024,
    },
    {
        "category": "Pricing",
        "title": "Battery Pack Prices Hit All-Time Low",
        "description": "Average battery pack prices fell to ~$115/kWh in 2024, with LFP packs as low as $89/kWh. Sub-$100/kWh packs expected by 2025.",
        "impact": "High",
        "year": 2024,
    },
    {
        "category": "Supply Chain",
        "title": "Lithium Price Crash & Stabilization",
        "description": "After peaking at $55K/tonne in 2022, lithium carbonate prices fell to ~$11K/tonne in 2024. Stabilization expected as marginal producers exit.",
        "impact": "Medium",
        "year": 2024,
    },
    {
        "category": "Supply Chain",
        "title": "Overcapacity in Cell Manufacturing",
        "description": "Global cell manufacturing capacity (~2.8 TWh) now exceeds production (~1.3 TWh). Utilization at ~46%. Consolidation expected.",
        "impact": "Medium",
        "year": 2024,
    },
    {
        "category": "Policy",
        "title": "IRA & EU Battery Regulation",
        "description": "US IRA standalone storage ITC (up to 70%) driving BESS pipeline. EU Battery Regulation mandating recycled content and carbon footprint disclosure from 2025.",
        "impact": "High",
        "year": 2024,
    },
    {
        "category": "Market",
        "title": "Long-Duration Energy Storage (LDES) Emergence",
        "description": "Iron-air, zinc-based, and flow batteries gaining investment for 8-100+ hour duration. Targeting $20/kWh for seasonal storage.",
        "impact": "Medium",
        "year": 2024,
    },
    {
        "category": "Risk",
        "title": "Geographic Concentration Risk",
        "description": "China controls 80%+ of cell manufacturing, 70%+ of cathode/anode production, and dominates lithium refining. Trade tensions pose supply chain risks.",
        "impact": "High",
        "year": 2024,
    },
    {
        "category": "Technology",
        "title": "Solid-State Battery Progress",
        "description": "Toyota, Samsung SDI, QuantumScape targeting 2027-2028 for commercial solid-state. Higher energy density but unlikely to impact BESS economics near-term.",
        "impact": "Low",
        "year": 2024,
    },
]

key_developments_timeline = pd.DataFrame({
    "Year": [2021, 2021, 2022, 2022, 2023, 2023, 2024, 2024],
    "Event": [
        "Grid storage crosses 10 GWh annual mark",
        "LFP chemistry overtakes NMC in China EV market",
        "Lithium prices spike to $55K/tonne",
        "US IRA signed — massive BESS incentives",
        "LFP crosses 50% global battery market share",
        "Grid storage nearly doubles to 46 GWh",
        "Battery packs hit $115/kWh (LFP: $89)",
        "Annual BESS installations reach 75 GWh",
    ],
    "Category": [
        "Deployment", "Technology", "Supply Chain", "Policy",
        "Technology", "Deployment", "Pricing", "Deployment",
    ],
})
