import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="Monte Carlo Simulator", page_icon="📈", layout="wide")

# --- Custom CSS for Layout, Cards & Sidebar ---
st.markdown(
    """
    <style>
    [data-testid="stAppViewBlockContainer"] {
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding-top: 2rem !important;
    }
    
    .stMainBlockContainer {
        max-width: 1200px !important;
        margin: 0 auto !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0e1117;
    }
    
    .nav-item {
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 5px;
        font-weight: 500;
        color: #8b949e;
        font-size: 16px;
    }
    
    .nav-item a {
        color: inherit;
        text-decoration: none;
        display: block;
        width: 100%;
    }

    .nav-active {
        background-color: #1f2937;
        color: #ffffff !important;
        border-left: 4px solid #4589ff;
    }

    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
    }

    /* Custom Danger Red for Warning Bubbles */
    div[data-testid="stNotification"] {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    div[data-testid="stNotification"] svg {
        fill: white !important;
    }

    /* Card Styling for Results */
    .metric-card {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-label {
        color: #8b949e;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #ffffff;
        font-size: 28px;
        font-weight: 700;
    }
    .metric-delta {
        font-size: 16px;
        font-weight: 600;
        margin-top: 4px;
    }
    .delta-gain {
        color: #26a69a;
    }
    .delta-loss {
        color: #ef5350;
    }
    .delta-neutral {
        color: #ffffff;
    }
    
    /* Special VAR/CVAR Card styling */
    .risk-card {
        background-color: #251212;
        border: 1px solid #632a2a;
        text-align: left;
        padding: 22px;
        min-height: 140px;
    }
    .cvar-card {
        background-color: #350a0a;
        border: 1px solid #8e1e1e;
    }
    .var-text {
        color: #ffffff;
        font-size: 17px;
        line-height: 1.4;
    }
    .var-highlight {
        font-weight: 700;
        color: #ef5350;
    }
    
    /* Success/Failure Card styling */
    .success-card {
        background-color: #102a1e;
        border: 1px solid #1e6341;
    }
    .failure-card {
        background-color: #2a1010;
        border: 1px solid #631e1e;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Helper to get Ticker Names ---
@st.cache_data
def get_ticker_info(ticker_list):
    info_map = {}
    for t in ticker_list:
        try:
            # Fetching shortName to ensure we get the full asset title
            name = yf.Ticker(t).info.get('shortName', t)
            info_map[t] = name
        except:
            info_map[t] = t
    return info_map

# --- Historical windows for the Crisis regime + helpers ---
CRISES = {
    "1997 Tom Yum Kung (Asian Crisis)": ("1997-06-01", "1999-06-30"),
    "2000 Dot-com Crash":               ("2000-03-01", "2003-06-30"),
    "2008 Global Financial Crisis":     ("2007-10-01", "2009-12-31"),
    "2018 Q4 Selloff":                  ("2018-09-01", "2019-04-30"),
    "2020 COVID Crash":                 ("2020-01-01", "2020-08-31"),
    "2022 Rate-Hike Bear":              ("2022-01-01", "2022-12-31"),
}

@st.cache_data(show_spinner=False)
def fetch_close_window(tickers, start, end):
    raw = yf.download(list(tickers), start=start, end=end, auto_adjust=True)
    if raw is None or len(raw) == 0:
        return pd.DataFrame()
    close = raw['Close'] if isinstance(raw.columns, pd.MultiIndex) else raw[['Close']]
    return close.to_frame() if isinstance(close, pd.Series) else close

def align_and_filter(close, tickers, weights_pct, start):
    """Keep tickers that actually traded in the window, renormalize their weights,
       and align the weight vector to the data columns. Returns (data, w, excluded)."""
    start_ts = pd.Timestamp(start)
    keep = []
    for c in close.columns:
        s = close[c].dropna()
        if len(s) and close[c].notna().mean() > 0.6 and s.index[0] <= start_ts + pd.Timedelta(days=45):
            keep.append(c)
    excluded = [c for c in close.columns if c not in keep]
    data = close[keep].dropna()
    wmap = dict(zip(tickers, weights_pct))
    w = np.array([wmap[c] for c in data.columns], dtype=float)
    if w.sum() > 0:
        w = w / w.sum()
    return data, w, excluded

# --- Initialize Session State for Tickers ---
preset_tickers = {
    'VTI': 30.0,
    'TLT': 40.0,
    'IEF': 15.0,
    'GLD': 7.5,
    'PDBC': 7.5
}

if 'tickers_list' not in st.session_state:
    st.session_state.tickers_list = list(preset_tickers.keys())

for ticker, weight in preset_tickers.items():
    if f"w_val_{ticker}" not in st.session_state:
        st.session_state[f"w_val_{ticker}"] = float(weight)

if 'portfolio_sims' not in st.session_state:
    st.session_state.portfolio_sims = None
if 'sim_initial_investment' not in st.session_state:
    st.session_state.sim_initial_investment = 10000
if 'sim_active_tickers' not in st.session_state:
    st.session_state.sim_active_tickers = []
if 'sim_returns_data' not in st.session_state:
    st.session_state.sim_returns_data = None
if 'sim_days' not in st.session_state:
    st.session_state.sim_days = 252
if 'sim_regime' not in st.session_state:
    st.session_state.sim_regime = None

# --- Main App ---
st.title("📈 Portfolio Simulator (Monte Carlo)")

st.markdown("""
Hey there! I'm Shane from Thailand :) I built this app using Python, Streamlit, and GitHub to bring some of the CFA curriculum's finance concepts to life!

**What this app does:** This tool simulates thousands of potential future paths for your portfolio using historical data (Monte Carlo Simulation). It helps you visualize the range of possible outcomes, from best-case scenarios to potential downturns, so you can plan with more confidence.

**Inputs & Outcomes:**
* **Inputs:** Select your assets (stocks/ETFs), assign portfolio weights, and set simulation parameters like time horizon and historical data range.
* **Outcomes:** See the median expected value, probability of profit, and detailed tail-risk metrics (Value at Risk & Conditional VaR).

**Key Features:**
* 🎲 **Monte Carlo Engine:** Runs up to 10,000 simulations based on historical volatility and correlations.
* 📊 **Risk Analysis:** Quantifies downside risk using statistical confidence intervals.
* 📉 **Interactive Charts:** Visualize potential future price paths and outcome distributions.
* 🌊 **Crisis Regime:** Re-run the simulation using the volatility & correlations of a past crisis (2008, COVID, Tom Yum Kung...) to stress-test the range of outcomes. *(For the actual historical path instead, see the **Crisis Replay** page.)*
""")

st.divider()

# --- Section 1: Asset Configuration ---
# Added help tooltip here as requested
st.header("1. Asset Configuration", help="Any ticker you find on Yahoo Finance can be used here!")
col_input, col_add = st.columns([3, 1])
with col_input:
    # Retained the tooltip here as well just in case
    new_ticker = st.text_input("Add Ticker", placeholder="Try AAPL", key="ticker_input", label_visibility="collapsed", help="Found a ticker on Yahoo Finance? Pop it in here!").strip().upper()

with col_add:
    if st.button("Add Ticker", use_container_width=True):
        if new_ticker and new_ticker not in st.session_state.tickers_list:
            st.session_state.tickers_list.append(new_ticker)
            st.session_state[f"w_val_{new_ticker}"] = 0.0
            st.rerun()

if st.session_state.tickers_list:
    tickers = st.session_state.tickers_list
    ticker_names = get_ticker_info(tickers)
    col_weights, col_pie = st.columns([1.2, 0.8], gap="large")
    
    with col_weights:
        st.subheader("Portfolio Weights")
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("⚖️ Set Equal Weights", use_container_width=True):
                if tickers:
                    eq_val = round(100.0 / len(tickers), 2)
                    for t in tickers: st.session_state[f"w_val_{t}"] = eq_val
                    st.rerun()
        with btn_col2:
            if st.button("🔄 Reset All to 0%", use_container_width=True):
                for t in tickers:
                    st.session_state[f"w_val_{t}"] = 0.0
                st.rerun()
        
        df_data = []
        for t in tickers:
            df_data.append({
                "Active": True, "Ticker": t, "Name": ticker_names.get(t, t),
                "Weight (%)": float(st.session_state.get(f"w_val_{t}", 0.0))
            })
        df = pd.DataFrame(df_data)

        column_config = {
            "Active": st.column_config.CheckboxColumn("Active", help="Uncheck to remove", default=True),
            "Ticker": st.column_config.TextColumn("Ticker", disabled=True),
            "Name": st.column_config.TextColumn("Asset Name", disabled=True),
            "Weight (%)": st.column_config.NumberColumn("Weight", min_value=0.0, max_value=100.0, format="%.2f%%", step=0.01)
        }

        edited_df = st.data_editor(df, column_config=column_config, use_container_width=True, hide_index=True, key="weight_editor")

        to_remove = edited_df[edited_df["Active"] == False]["Ticker"].tolist()
        if to_remove:
            for t_rem in to_remove:
                st.session_state.tickers_list.remove(t_rem)
                if f"w_val_{t_rem}" in st.session_state: del st.session_state[f"w_val_{t_rem}"]
            st.rerun()

        active_tickers = edited_df["Ticker"].tolist()
        active_weights = edited_df["Weight (%)"].tolist()
        for idx, row in edited_df.iterrows(): st.session_state[f"w_val_{row['Ticker']}"] = row['Weight (%)']
        
        total_weight = sum(active_weights)
        st.markdown(f"**Total Assets:** {len(active_tickers)} | **Sum Weight:** {total_weight:.2f}%")
        
    with col_pie:
        st.subheader("Allocation Visual")
        if abs(total_weight - 100.0) > 0.1: st.error(f"⚠️ Total: {total_weight:.2f}%. Please adjust to 100%.")
        if any(w > 0 for w in active_weights):
            chart_df = pd.DataFrame({'Ticker': active_tickers, 'Weight': active_weights})
            chart_df = chart_df[chart_df['Weight'] > 0]
            pie_chart = alt.Chart(chart_df).mark_arc(innerRadius=60).encode(
                theta=alt.Theta(field="Weight", type="quantitative"),
                color=alt.Color(field="Ticker", type="nominal", legend=alt.Legend(orient="bottom")),
                tooltip=['Ticker', 'Weight']
            ).properties(height=350)
            st.altair_chart(pie_chart, use_container_width=True)
        else: st.info("Assign weights to see the chart.")

    st.header("2. Simulation Parameters")

    # --- Return & Volatility Regime: where the simulation's "DNA" comes from ---
    st.markdown("**Return & Volatility Regime** — where should the simulation draw its volatility & correlations from?")
    reg_col1, reg_col2 = st.columns([1, 1])
    with reg_col1:
        regime = st.radio("Regime", ["📈 Normal (recent history)", "🌊 Crisis (stressed)"],
                          label_visibility="collapsed", horizontal=True)
    is_crisis = regime.startswith("🌊")
    crisis_choice = None
    with reg_col2:
        if is_crisis:
            crisis_choice = st.selectbox("Crisis window", list(CRISES.keys()), label_visibility="collapsed")
    if is_crisis:
        st.caption("🌊 **Crisis regime** runs a *forward* Monte Carlo using that crisis period's volatility & "
                   "correlations — a **range of possible futures** if such conditions return. It is **not** the actual "
                   "historical path; for the real day-by-day replay, use the **Crisis Replay** page. "
                   "(Pre-2005 crises need long-history assets like ^GSPC / individual stocks; newer ETFs are skipped.)")
    else:
        st.caption("📈 **Normal regime** estimates volatility & correlations from the recent lookback you pick below.")

    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    with s_col1:
        simulations = st.slider("Simulations", 100, 10000, 1000)
    with s_col2:
        time_horizon = st.number_input("Horizon (Days)", min_value=1, value=252, help="How many trading days into the future should we simulate?")
    with s_col3:
        lookback_years = st.selectbox("Data Range (Years)", [1, 3, 5, 10], index=1, disabled=is_crisis,
                                      help="Recent history used to estimate the simulation's volatility & correlations. Ignored in Crisis regime (the crisis window is used instead).")
    with s_col4:
        initial_investment = st.number_input("Initial ($)", min_value=1, value=10000, help="Your starting investment amount.")

    if st.button("🚀 Run Monte Carlo Simulation", use_container_width=True) and abs(total_weight - 100.0) <= 0.1:
        # Pick the data window based on the chosen regime
        if is_crisis:
            start_date, end_date = CRISES[crisis_choice]
            regime_label = f"🌊 {crisis_choice}"
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_years * 365)
            regime_label = f"📈 Recent history ({lookback_years}y)"

        with st.spinner("Analyzing macro DNA..."):
            try:
                close = fetch_close_window(active_tickers, start_date, end_date)
                if close.empty:
                    st.error("No price data returned for this window.")
                else:
                    # Keep only assets that traded in the window; renormalize weights to them
                    data, weights, excluded = align_and_filter(close, active_tickers, active_weights, start_date)
                    if data.shape[1] == 0 or len(data) < 30:
                        st.error("Not enough history in this window to simulate — try adding long-history assets "
                                 "(e.g. ^GSPC) or a more recent window.")
                    else:
                        if excluded:
                            st.info("Excluded (no history in this window): " + ", ".join(excluded)
                                    + " — remaining weights were renormalized.")

                        log_returns = np.log(data / data.shift(1)).dropna()
                        L = np.linalg.cholesky(log_returns.cov())
                        drift = log_returns.mean().values - 0.5 * np.diag(log_returns.cov().values)

                        portfolio_sims = np.zeros((time_horizon, simulations))
                        for i in range(simulations):
                            Z = np.random.normal(size=(time_horizon, len(weights)))
                            daily_log_returns = drift + np.dot(Z, L.T)
                            portfolio_path = np.exp(np.cumsum(np.dot(daily_log_returns, weights)))
                            portfolio_sims[:, i] = portfolio_path * initial_investment

                        # Annualized vol of the portfolio under this regime (feedback for the user)
                        ann_vol = float(log_returns.dot(weights).std() * np.sqrt(252))

                        st.session_state.portfolio_sims = portfolio_sims
                        st.session_state.sim_initial_investment = initial_investment
                        st.session_state.sim_active_tickers = list(data.columns)
                        st.session_state.sim_returns_data = data
                        st.session_state.sim_days = time_horizon
                        st.session_state.sim_regime = f"{regime_label} · annualized vol ≈ {ann_vol*100:.0f}%"
                        st.rerun()
            except Exception as e:
                st.error(f"Engine failure: {e}")

    # --- Section 3: Results ---
    if st.session_state.portfolio_sims is not None:
        st.divider()
        st.header("3. Simulation Results")
        if st.session_state.get('sim_regime'):
            st.markdown(f"🧬 **Simulated under:** {st.session_state.sim_regime}")
        portfolio_sims, initial_inv = st.session_state.portfolio_sims, st.session_state.sim_initial_investment
        final_values = portfolio_sims[-1, :]
        avg_final, med_final = np.mean(final_values), np.median(final_values)
        profit_prob = (final_values > initial_inv).mean() * 100

        def get_delta_html(current, base):
            delta_pct = ((current - base) / base) * 100
            color_class = "delta-gain" if delta_pct > 0 else "delta-loss" if delta_pct < 0 else "delta-neutral"
            sign = "+" if delta_pct > 0 else ""
            return f'<div class="metric-delta {color_class}">({sign}{delta_pct:.2f}%)</div>'

        c_res1, c_res2, c_res3 = st.columns(3)
        with c_res1: st.markdown(f'<div class="metric-card"><div class="metric-label">Median Final Value</div><div class="metric-value">${med_final:,.0f}</div>{get_delta_html(med_final, initial_inv)}</div>', unsafe_allow_html=True)
        with c_res2: st.markdown(f'<div class="metric-card"><div class="metric-label">Average Final Value</div><div class="metric-value">${avg_final:,.0f}</div>{get_delta_html(avg_final, initial_inv)}</div>', unsafe_allow_html=True)
        with c_res3: 
            st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">Probability of Profit</div>
                    <div class="metric-value">{profit_prob:.1f}%</div>
                    <div class="metric-delta" style="visibility: hidden;">(Placeholder)</div>
                </div>
            ''', unsafe_allow_html=True)

        st.write("")
        col_paths_header, col_reroll = st.columns([3, 1])
        with col_paths_header:
            # Added help tooltip for Sample Paths
            st.subheader("Visualize Sample Paths", help="Displaying just 50 random paths to keep your browser running smoothly! 🚀 (Don't worry, the math still uses your full simulation count).")
        with col_reroll:
            if st.button("🎲 Reroll Sample", use_container_width=True): st.rerun()

        days = np.arange(portfolio_sims.shape[0])
        num_to_display = min(portfolio_sims.shape[1], 50)
        random_indices = np.random.choice(portfolio_sims.shape[1], num_to_display, replace=False)
        path_data = pd.DataFrame({'Day': days})
        for idx, sim_idx in enumerate(random_indices): path_data[f'Path {idx+1}'] = portfolio_sims[:, sim_idx]
        melted_paths = path_data.melt('Day', var_name='Reality', value_name='Value')
        median_path = np.median(portfolio_sims, axis=1)
        median_df = pd.DataFrame({'Day': days, 'Value': median_path, 'Reality': 'Overall Median'})

        base_paths = alt.Chart(melted_paths).mark_line(opacity=0.15, strokeWidth=1, color='#4589ff').encode(x=alt.X('Day:Q', title='Days'), y=alt.Y('Value:Q', title='Portfolio Value ($)', scale=alt.Scale(zero=False)), detail='Reality')
        median_line = alt.Chart(median_df).mark_line(strokeWidth=4, color='#ffffff').encode(x='Day:Q', y='Value:Q', tooltip=['Day', 'Reality', 'Value'])
        baseline = alt.Chart(pd.DataFrame({'y': [initial_inv]})).mark_rule(color='#8b949e', strokeWidth=1, strokeDash=[4,4]).encode(y='y:Q')
        st.altair_chart(base_paths + median_line + baseline, use_container_width=True)

        # --- Probability of Success ---
        st.divider()
        st.subheader("🎯 Probability of Success")
        
        sim_min, sim_max = float(np.min(final_values)), float(np.max(final_values))
        col_success_input, col_fail_card, col_success_card = st.columns([2, 1, 1])
        
        with col_success_input:
            target_amount = st.slider("Target Final Amount ($)", min_value=sim_min, max_value=sim_max, value=float(initial_inv), format="$%d")
            
        success_rate = (final_values >= target_amount).mean() * 100
        failure_rate = 100 - success_rate

        with col_fail_card:
            st.markdown(f'<div class="metric-card failure-card"><div class="metric-label">Probability of Failure</div><div class="metric-value">{failure_rate:.1f}%</div><div class="metric-delta">Below ${target_amount:,.0f}</div></div>', unsafe_allow_html=True)
        with col_success_card:
            st.markdown(f'<div class="metric-card success-card"><div class="metric-label">Probability of Success</div><div class="metric-value">{success_rate:.1f}%</div><div class="metric-delta">Above ${target_amount:,.0f}</div></div>', unsafe_allow_html=True)

        # --- Risk Metrics ---
        st.divider()
        st.header("4. Risk Metrics")
        st.subheader("🛡️ Tail Risk Analysis")
        col_risk_input, col_var_card, col_cvar_card = st.columns([2, 1, 1])
        
        with col_risk_input:
            alpha = st.select_slider("Risk Threshold (α)", options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], value=5)
            confidence = 100 - alpha
            
        var_value = np.percentile(final_values, alpha)
        var_loss = initial_inv - var_value
        var_loss_pct = (var_loss / initial_inv) * 100
        worst_case_values = final_values[final_values <= var_value]
        cvar_value = np.mean(worst_case_values)
        cvar_loss = initial_inv - cvar_value
        cvar_loss_pct = (cvar_loss / initial_inv) * 100

        with col_var_card:
            st.markdown(f'<div class="metric-card risk-card"><div class="metric-label">Value at Risk (VaR)</div><div class="var-text"><span class="var-highlight">{confidence}%</span> chance loss will not exceed <span class="var-highlight">${var_loss:,.0f} (-{var_loss_pct:.2f}%)</span> over <span class="var-highlight">{st.session_state.sim_days}-days</span>.</div></div>', unsafe_allow_html=True)
        with col_cvar_card:
            st.markdown(f'<div class="metric-card risk-card cvar-card"><div class="metric-label">Conditional VaR (CVaR)</div><div class="var-text">Average loss of <span class="var-highlight">${cvar_loss:,.0f} (-{cvar_loss_pct:.2f}%)</span> if the worst-case <span class="var-highlight">{alpha}%</span> occurs.</div></div>', unsafe_allow_html=True)

        # --- Charts ---
        c_dist, c_corr = st.columns(2)
        with c_dist:
            st.subheader("Outcome Distribution")
            dist_df = pd.DataFrame({'Final Value': final_values})
            hist = alt.Chart(dist_df).mark_bar(color="#1f77b4", opacity=0.7).encode(x=alt.X("Final Value:Q", bin=alt.Bin(maxbins=50), title="Final Value ($)"), y=alt.Y("count()", title="Frequency")).properties(height=350)
            rule = alt.Chart(pd.DataFrame({'x': [initial_inv]})).mark_rule(color='white', strokeDash=[5,5]).encode(x='x:Q')
            st.altair_chart(hist + rule, use_container_width=True)
        with c_corr:
            st.subheader("Asset Correlation Matrix")
            if st.session_state.sim_returns_data is not None:
                corr_matrix = st.session_state.sim_returns_data.pct_change().corr()
                styled_corr = corr_matrix.style.background_gradient(cmap='RdBu_r', axis=None, vmin=-1, vmax=1).format("{:.2f}")
                st.dataframe(styled_corr, use_container_width=True)
else: st.info("Add some tickers to start.")
