import streamlit as st

st.set_page_config(page_title="Chiller Payback Calculator", layout="wide")

st.title("Chiller Payback Calculator")
st.caption("Simple V1 calculator using average load factor and full-load EER")

with st.sidebar:
    st.header("Plant Inputs")
    chillers = st.number_input("Number of chillers", 1, 10, 1)
    capacity_per_chiller = st.number_input("Capacity per chiller (kW)", 100, 10000, 1000)
    load_factor = st.number_input("Avg load factor (during operating hours)", 0.01, 1.0, 0.35, step=0.01)
    operating_hours = st.number_input("Annual operating hours", 500, 8760, 3600)
    operating_months = st.number_input("Operating months per year", 1, 12, 5)

    st.header("Electricity & FX")
    electricity_price = st.number_input("Electricity price (GEL/kWh)", 0.01, 2.0, 0.30, step=0.01)
    eur_to_gel = st.number_input("EUR → GEL", 0.1, 10.0, 3.16, step=0.01)

    st.header("Option 1 (Higher EER)")
    eer_1 = st.number_input("EER option 1", 0.1, 10.0, 3.3, step=0.1)
    price_1 = st.number_input("Price per chiller option 1 (EUR)", 0, 500000, 137000, step=1000)

    st.header("Option 2 (Lower EER)")
    eer_2 = st.number_input("EER option 2", 0.1, 10.0, 2.7, step=0.1)
    price_2 = st.number_input("Price per chiller option 2 (EUR)", 0, 500000, 115000, step=1000)

# ---- Calculations ----
total_capacity = chillers * capacity_per_chiller
avg_cooling_load = total_capacity * load_factor

def calc(eer, price_eur):
    elec_kw = avg_cooling_load / eer
    annual_kwh = elec_kw * operating_hours
    annual_cost = annual_kwh * electricity_price
    capex_gel = price_eur * chillers * eur_to_gel
    return elec_kw, annual_kwh, annual_cost, capex_gel

p1_kw, p1_kwh, p1_cost, p1_capex = calc(eer_1, price_1)
p2_kw, p2_kwh, p2_cost, p2_capex = calc(eer_2, price_2)

annual_savings = p2_cost - p1_cost
capex_diff = p1_capex - p2_capex

st.divider()

c1, c2 = st.columns(2)

with c1:
    st.subheader("Option 1 (Higher EER)")
    st.write(f"Electric power: **{p1_kw:.1f} kW**")
    st.write(f"Annual energy: **{p1_kwh:,.0f} kWh**")
    st.write(f"Annual cost: **{p1_cost:,.0f} GEL**")
    st.write(f"CAPEX: **{p1_capex:,.0f} GEL**")

with c2:
    st.subheader("Option 2 (Lower EER)")
    st.write(f"Electric power: **{p2_kw:.1f} kW**")
    st.write(f"Annual energy: **{p2_kwh:,.0f} kWh**")
    st.write(f"Annual cost: **{p2_cost:,.0f} GEL**")
    st.write(f"CAPEX: **{p2_capex:,.0f} GEL**")

st.divider()

st.subheader("Payback Analysis")

if annual_savings > 0 and capex_diff > 0:
    payback_years = capex_diff / annual_savings
    payback_calendar_months = payback_years * 12
    payback_operating_months = capex_diff / (annual_savings / operating_months)

    st.metric("Annual savings (GEL)", f"{annual_savings:,.0f}")
    st.metric("Payback (calendar months)", f"{payback_calendar_months:.1f}")
    st.metric("Payback (operating months)", f"{payback_operating_months:.1f}")
else:
    st.warning("No payback with current inputs.")
