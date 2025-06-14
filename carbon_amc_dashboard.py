import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Carbon AMC NAV Model", layout="centered")

st.title("🌍 Carbon AMC NAV Projection Dashboard")
st.markdown("""
This tool estimates the NAV of an Actively Managed Certificate (AMC) backed by carbon credits from Genneia's renewable energy portfolio.
""")

# --- User inputs ---
price_2021 = st.slider("2021 Vintage Price ($/tCO₂e)", 3.0, 10.0, 4.0)
price_2022 = st.slider("2022 Vintage Price ($/tCO₂e)", 3.0, 10.0, 4.2)
price_2023 = st.slider("2023 Vintage Price ($/tCO₂e)", 3.0, 10.0, 4.5)
price_2024 = st.slider("2024 Vintage Price ($/tCO₂e)", 3.0, 10.0, 4.8)
price_2025 = st.slider("2025 Vintage Price ($/tCO₂e)", 3.0, 10.0, 5.0)

growth_scenario = st.selectbox("Select Growth Scenario", ["Base (5%)", "Bull (10%)", "Bear (0%)"])
fee_pct = st.slider("Performance Fee (%)", 0, 20, 10)
hurdle_rate = st.slider("Hurdle Rate (%)", 0, 10, 6) / 100
redemption_rate = st.slider("Annual Redemption Rate (%)", 0, 20, 5) / 100

# --- Parameters ---
vintages = ['2021', '2022', '2023', '2024', '2025']
volumes = [250000] * 5
prices = [price_2021, price_2022, price_2023, price_2024, price_2025]
years = list(range(2025, 2030))

if "Base" in growth_scenario:
    growth = 0.05
elif "Bull" in growth_scenario:
    growth = 0.10
else:
    growth = 0.00

# --- NAV Calculation ---
nav = pd.DataFrame({'Year': years})

for vintage, vol, price in zip(vintages, volumes, prices):
    nav[f'{vintage} NAV'] = [round(vol * price * ((1 + growth) ** (y - 2025)), 0) for y in years]

nav['Total NAV'] = nav[[col for col in nav.columns if 'NAV' in col]].sum(axis=1)

# --- Apply performance fee ---
adj_nav = []
for i, row in nav.iterrows():
    if i == 0:
        adj_nav.append(row['Total NAV'])
    else:
        prev = adj_nav[-1]
        hurdle = prev * (1 + hurdle_rate)
        if row['Total NAV'] > hurdle:
            fee = (row['Total NAV'] - hurdle) * (fee_pct / 100)
            adj_nav.append(row['Total NAV'] - fee)
        else:
            adj_nav.append(row['Total NAV'])

# --- Apply redemptions ---
red_nav = []
for i, val in enumerate(adj_nav):
    if i == 0:
        red_nav.append(val)
    else:
        red_nav.append(red_nav[-1] * (1 - redemption_rate) + (val - adj_nav[i-1]))

nav['Perf Fee Adj NAV'] = adj_nav
nav['Final Adj NAV'] = red_nav

# --- Plotting ---
st.subheader("📈 NAV Over Time")
fig, ax = plt.subplots()
ax.plot(nav['Year'], nav['Total NAV'], label='Gross NAV', linestyle='--')
ax.plot(nav['Year'], nav['Perf Fee Adj NAV'], label='After Perf. Fee', linestyle='-.')
ax.plot(nav['Year'], nav['Final Adj NAV'], label='Final (w/ Redemptions)', linewidth=2)
ax.set_ylabel("USD")
ax.set_xlabel("Year")
ax.set_title("AMC NAV Projection")
ax.legend()
ax.grid(True)
st.pyplot(fig)

# --- Show table ---
st.subheader("📊 NAV Table")
st.dataframe(nav.set_index('Year'))
