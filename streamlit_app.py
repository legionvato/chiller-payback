import streamlit as st

st.set_page_config(
    page_title="Chiller Payback Calculator (V2)",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Chiller Payback Calculator (V2)")
st.caption("V2 adds IPLV and optional 4-point part-load efficiency (25/50/75/100%).")

st.info(
    "How energy is calculated:\n"
    "- If you select **4-point part-load** and provide EERs, the app uses those at 25/50/75/100%.\n"
    "- If some points are missing, it falls back to **IPLV** (if given).\n"
    "- If IPLV is missing too, it falls back to **full-load EER**.\n\n"
    "Payback (operating months) counts only cooling months. Payback (calendar months) is real time."
)

# --------------------
# Sidebar inputs
# --------------------
with st.sidebar:
    st.header("Plant Inputs")
    chillers = st.number_input("Number of chillers", 1, 10, 1)
    capacity_per_chiller_kw = st.number_input("Capacity per chiller (kW)", 50.0, 50000.0, 1000.0, step=50.0)
    load_factor = st.number_input("Avg load factor (during operating months)", 0.01, 1.0, 0.35, step=0.01)

    operating_months = st.number_input("Operating months per year", 1, 12, 5)
    days_per_month = st.number_input("Days per month (assumption)", 25, 31, 30)
    operating_hours = operating_months * days_per_month * 24
    st.write(f"**Calculated operating hours:** {operating_hours:,} h/year (months × {days_per_month} × 24)")

    st.header("Electricity & FX")
    gel_per_kwh = st.number_input("Electricity price (GEL/kWh)", 0.0001, 5.0, 0.30, step=0.01, format="%.4f")
    eur_to_gel = st.number_input("EUR → GEL", 0.01, 20.0, 3.16, step=0.01, format="%.2f")

    st.header("Energy Method (V2)")
    method = st.radio(
        "Choose method",
        ["Auto (recommended)", "Use IPLV only", "Use 4-point part-load (25/50/75/100)"],
        index=0,
    )

    st.header("Option 1 (Higher efficiency)")
    capex_1_eur = st.number_input("Price per chiller (EUR) - Option 1", 0.0, 2_000_000.0, 137000.0, step=1000.0)
    eer_1_full = st.number_input("Full-load EER (100%) - Option 1", 0.1, 20.0, 3.3, step=0.1)
    iplv_1 = st.number_input("IPLV (optional) - Option 1", 0.0, 20.0, 0.0, step=0.1)

    with st.expander("Option 1: Part-load EERs (optional)", expanded=False):
        eer_1_75 = st.number_input("EER @ 75% (optional) - Opt 1", 0.0, 20.0, 0.0, step=0.1)
        eer_1_50 = st.number_input("EER @ 50% (optional) - Opt 1", 0.0, 20.0, 0.0, step=0.1)
        eer_1_25 = st.number_input("EER @ 25% (optional) - Opt 1", 0.0, 20.0, 0.0, step=0.1)

    st.header("Option 2 (Lower efficiency)")
    capex_2_eur = st.number_input("Price per chiller (EUR) - Option 2", 0.0, 2_000_000.0, 115000.0, step=1000.0)
    eer_2_full = st.number_input("Full-load EER (100%) - Option 2", 0.1, 20.0, 2.7, step=0.1)
    iplv_2 = st.number_input("IPLV (optional) - Option 2", 0.0, 20.0, 0.0, step=0.1)

    with st.expander("Option 2: Part-load EERs (optional)", expanded=False):
        eer_2_75 = st.number_input("EER @ 75% (optional) - Opt 2", 0.0, 20.0, 0.0, step=0.1)
        eer_2_50 = st.number_input("EER @ 50% (optional) - Opt 2", 0.0, 20.0, 0.0, step=0.1)
        eer_2_25 = st.number_input("EER @ 25% (optional) - Opt 2", 0.0, 20.0, 0.0, step=0.1)

# --------------------
# Core calculations
# --------------------
total_capacity_kw = chillers * capacity_per_chiller_kw
avg_cooling_kw = total_capacity_kw * load_factor

def safe_positive(x: float) -> bool:
    return x is not None and x > 0

def pick_energy_method(
    method_choice: str,
    eer_full: float,
    iplv: float,
    eer75: float,
    eer50: float,
    eer25: float,
):
    """
    Returns a tuple: (method_used, details_dict)
    method_used in {"partload", "iplv", "full"}
    """
    # Determine availability
    has_iplv = safe_positive(iplv)
    has_partload = all(safe_positive(v) for v in [eer_full, eer75, eer50, eer25])

    # Decide method
    if method_choice == "Use 4-point part-load (25/50/75/100)":
        if has_partload:
            return "partload", {"eer100": eer_full, "eer75": eer75, "eer50": eer50, "eer25": eer25}
        # fallback
        if has_iplv:
            return "iplv", {"iplv": iplv}
        return "full", {"eer100": eer_full}

    if method_choice == "Use IPLV only":
        if has_iplv:
            return "iplv", {"iplv": iplv}
        return "full", {"eer100": eer_full}

    # Auto (recommended)
    if has_partload:
        return "partload", {"eer100": eer_full, "eer75": eer75, "eer50": eer50, "eer25": eer25}
    if has_iplv:
        return "iplv", {"iplv": iplv}
    return "full", {"eer100": eer_full}

def annual_kwh_full_eer(load_kw: float, hours: float, eer: float) -> float:
    # kW_elec = load_kw / eer
    return (load_kw / eer) * hours

def annual_kwh_iplv(load_kw: float, hours: float, iplv: float) -> float:
    # Treat IPLV as effective seasonal EER
    return (load_kw / iplv) * hours

def annual_kwh_partload_4pt(load_kw: float, hours: float, eer100: float, eer75: float, eer50: float, eer25: float) -> float:
    """
    Uses a simple 4-bin load distribution (same spirit as IPLV bins),
    but applies your provided EERs.

    Assumed hour weights (common approximation):
      100%: 1%
      75% : 42%
      50% : 45%
      25% : 12%

    (Weights sum to 100%.)
    """
    weights = {
        "100": 0.01,
        "75":  0.42,
        "50":  0.45,
        "25":  0.12
    }

    # Convert "average load" into bin loads as a fraction of full capacity.
    # We scale around the plant load_kw; simplest approach:
    # assume load_kw represents the season-average cooling load,
    # and bins represent typical variation around it at 25/50/75/100% of capacity.
    #
    # For V2, we interpret bins as % of *installed capacity*.
    # So actual load in each bin = total_capacity_kw * bin_fraction.
    # But to keep consistent with your V1 (based on avg load), we compute using bins of total capacity.
    #
    # This requires total_capacity_kw; we can use the outer scope variable.
    cap = total_capacity_kw

    load_100 = cap * 1.00
    load_75  = cap * 0.75
    load_50  = cap * 0.50
    load_25  = cap * 0.25

    # If your average load is lower than 25% capacity, bins will overestimate.
    # To stay conservative, we scale bin loads so that weighted average equals the avg load input.
    avg_from_bins = (weights["100"]*load_100 + weights["75"]*load_75 + weights["50"]*load_50 + weights["25"]*load_25)
    scale = 1.0
    if avg_from_bins > 0:
        scale = load_kw / avg_from_bins

    load_100 *= scale
    load_75  *= scale
    load_50  *= scale
    load_25  *= scale

    # Annual kWh = sum( (load_i / eer_i) * (hours * weight_i) )
    kwh = 0.0
    kwh += (load_100 / eer100) * (hours * weights["100"])
    kwh += (load_75  / eer75)  * (hours * weights["75"])
    kwh += (load_50  / eer50)  * (hours * weights["50"])
    kwh += (load_25  / eer25)  * (hours * weights["25"])
    return kwh

def compute_option(
    capex_eur: float,
    eer_full: float,
    iplv: float,
    eer75: float,
    eer50: float,
    eer25: float,
    method_choice: str
):
    used, params = pick_energy_method(method_choice, eer_full, iplv, eer75, eer50, eer25)

    if used == "partload":
        kwh = annual_kwh_partload_4pt(avg_cooling_kw, operating_hours,
                                      params["eer100"], params["eer75"], params["eer50"], params["eer25"])
        method_label = "4-point part-load"
    elif used == "iplv":
        kwh = annual_kwh_iplv(avg_cooling_kw, operating_hours, params["iplv"])
        method_label = "IPLV"
    else:
        kwh = annual_kwh_full_eer(avg_cooling_kw, operating_hours, params["eer100"])
        method_label = "Full-load EER"

    annual_cost_gel = kwh * gel_per_kwh
    capex_total_gel = (capex_eur * chillers) * eur_to_gel
    avg_elec_kw = kwh / operating_hours if operating_hours > 0 else 0.0

    return {
        "kwh": kwh,
        "annual_cost_gel": annual_cost_gel,
        "capex_gel": capex_total_gel,
        "avg_elec_kw": avg_elec_kw,
        "method": method_label,
    }

opt1 = compute_option(capex_1_eur, eer_1_full, iplv_1, eer_1_75, eer_1_50, eer_1_25, method)
opt2 = compute_option(capex_2_eur, eer_2_full, iplv_2, eer_2_75, eer_2_50, eer_2_25, method)

annual_savings_gel = opt2["annual_cost_gel"] - opt1["annual_cost_gel"]  # savings if choosing option 1
delta_capex_gel = opt1["capex_gel"] - opt2["capex_gel"]

# Payback calculations
payback_calendar_months = None
payback_operating_months = None
if annual_savings_gel > 0 and delta_capex_gel > 0 and operating_months > 0:
    payback_years = delta_capex_gel / annual_savings_gel
    payback_calendar_months = payback_years * 12
    payback_operating_months = delta_capex_gel / (annual_savings_gel / operating_months)

# --------------------
# UI output
# --------------------
st.divider()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total installed capacity (kW)", f"{total_capacity_kw:,.0f}")
m2.metric("Avg cooling load (kW)", f"{avg_cooling_kw:,.0f}")
m3.metric("Operating hours (calculated)", f"{operating_hours:,.0f}")
m4.metric("Electricity price", f"{gel_per_kwh:.4f} GEL/kWh")

st.divider()

c1, c2 = st.columns(2)

with c1:
    st.subheader("Option 1 (Higher efficiency)")
    st.caption(f"Energy method used: **{opt1['method']}**")
    st.write(f"Average electric power: **{opt1['avg_elec_kw']:.1f} kW**")
    st.write(f"Annual electricity: **{opt1['kwh']:,.0f} kWh**")
    st.write(f"Annual cost: **{opt1['annual_cost_gel']:,.0f} GEL**")
    st.write(f"CAPEX total: **{opt1['capex_gel']:,.0f} GEL**")

with c2:
    st.subheader("Option 2 (Lower efficiency)")
    st.caption(f"Energy method used: **{opt2['method']}**")
    st.write(f"Average electric power: **{opt2['avg_elec_kw']:.1f} kW**")
    st.write(f"Annual electricity: **{opt2['kwh']:,.0f} kWh**")
    st.write(f"Annual cost: **{opt2['annual_cost_gel']:,.0f} GEL**")
    st.write(f"CAPEX total: **{opt2['capex_gel']:,.0f} GEL**")

st.divider()

st.subheader("Comparison (Savings if you choose Option 1 instead of Option 2)")

k1, k2, k3 = st.columns(3)
k1.metric("Annual savings (GEL)", f"{annual_savings_gel:,.0f}")
k2.metric("Annual savings (kWh)", f"{(opt2['kwh'] - opt1['kwh']):,.0f}")
k3.metric("Extra CAPEX for Option 1 (GEL)", f"{delta_capex_gel:,.0f}")

if payback_calendar_months is None:
    st.warning("No payback under current inputs (either savings ≤ 0 or extra CAPEX ≤ 0).")
else:
    p1, p2 = st.columns(2)
    p1.metric("Payback (calendar months)", f"{payback_calendar_months:,.1f}")
    p2.metric("Payback (operating months)", f"{payback_operating_months:,.1f}")

with st.expander("Debug / assumptions (optional)", expanded=False):
    st.write("**Part-load bin weights used for 4-point method:** 100%:1%, 75%:42%, 50%:45%, 25%:12%")
    st.write("**4-point method note:** Bin loads are scaled so the weighted-average cooling load equals your input average load.")
    st.write(f"Option 1 method used: {opt1['method']}")
    st.write(f"Option 2 method used: {opt2['method']}")
