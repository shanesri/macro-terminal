import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="Stress Testing", page_icon="🌊", layout="wide")

# --- Custom CSS (shared look with the other pages) ---
st.markdown(
    """
    <style>
    [data-testid="stAppViewBlockContainer"] { max-width: 1200px !important; margin: 0 auto !important; padding-top: 2rem !important; }
    .stMainBlockContainer { max-width: 1200px !important; margin: 0 auto !important; }
    [data-testid="stSidebar"] { background-color: #0e1117; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; }
    div[data-testid="stNotification"] { background-color: #ff4b4b !important; color: white !important; }
    div[data-testid="stNotification"] svg { fill: white !important; }

    .metric-card { background-color: #1e2130; padding: 20px; border-radius: 10px; border: 1px solid #30363d; text-align: center; margin-bottom: 10px; min-height: 120px; }
    .metric-label { color: #8b949e; font-size: 13px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .metric-value { color: #ffffff; font-size: 26px; font-weight: 700; }
    .metric-sub { color: #8b949e; font-size: 13px; margin-top: 6px; }
    .val-loss { color: #ef5350; }
    .val-gain { color: #26a69a; }
    .crisis-card { background-color: #1a1d29; border: 1px solid #30363d; border-radius: 12px; padding: 22px 24px; margin-bottom: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Ticker name helper (cached) ---
@st.cache_data
def get_ticker_info(ticker_list):
    info_map = {}
    for t in ticker_list:
        try:
            info_map[t] = yf.Ticker(t).info.get('shortName', t)
        except Exception:
            info_map[t] = t
    return info_map

# --- Historical price fetch (cached) ---
@st.cache_data(show_spinner=False)
def fetch_close(tickers, start, end):
    raw = yf.download(list(tickers), start=start, end=end, auto_adjust=True)
    if raw is None or len(raw) == 0:
        return pd.DataFrame()
    close = raw['Close'] if isinstance(raw.columns, pd.MultiIndex) else raw[['Close']]
    if isinstance(close, pd.Series):
        close = close.to_frame()
    return close

# --- Crisis windows (well-known Black-Swan / bear episodes) ---
CRISES = {
    "1997 Tom Yum Kung (Asian Crisis)": ("1997-06-01", "1999-06-30"),
    "2000 Dot-com Crash":               ("2000-03-01", "2003-06-30"),
    "2008 Global Financial Crisis":     ("2007-10-01", "2009-12-31"),
    "2018 Q4 Selloff":                  ("2018-09-01", "2019-04-30"),
    "2020 COVID Crash":                 ("2020-01-01", "2020-08-31"),
    "2022 Rate-Hike Bear":              ("2022-01-01", "2022-12-31"),
}
BENCHMARK = "SPY"

# --- Portfolio / drawdown math ---
def usable_columns(close, start, min_coverage=0.6, start_buffer_days=30):
    """Keep tickers that actually traded across (most of) the window."""
    usable, excluded = [], []
    start_ts = pd.Timestamp(start)
    for col in close.columns:
        s = close[col].dropna()
        covered = close[col].notna().mean()
        fvi = s.index[0] if len(s) else None
        if len(s) == 0 or covered < min_coverage or (fvi is not None and fvi > start_ts + pd.Timedelta(days=start_buffer_days)):
            excluded.append(col)
        else:
            usable.append(col)
    return usable, excluded

def portfolio_equity(close, weights):
    """weights: dict ticker->weight (any scale). Returns equity rebased to 1.0."""
    prices = close.dropna()
    if len(prices) < 2:
        return None
    w = np.array([weights[c] for c in prices.columns], dtype=float)
    if w.sum() == 0:
        return None
    w = w / w.sum()
    rets = prices.pct_change().dropna()
    port_ret = rets.dot(w)
    return (1 + port_ret).cumprod()

def drawdown_stats(equity):
    roll_max = equity.cummax()
    dd = equity / roll_max - 1.0
    mdd = float(dd.min())
    trough = dd.idxmin()
    peak = equity.loc[:trough].idxmax()
    peak_val = equity.loc[peak]
    after = equity.loc[trough:]
    recovered = after[after >= peak_val]
    rec_date = recovered.index[0] if len(recovered) else None
    return {
        "mdd": mdd,
        "peak": peak, "trough": trough, "rec_date": rec_date,
        "decline_days": (trough - peak).days,
        "recovery_days": (rec_date - trough).days if rec_date is not None else None,
        "total_return": float(equity.iloc[-1] / equity.iloc[0] - 1.0),
    }

# --- Session state (shared with the other pages: configure once, use everywhere) ---
preset_tickers = {'VTI': 30.0, 'TLT': 40.0, 'IEF': 15.0, 'GLD': 7.5, 'PDBC': 7.5}
if 'tickers_list' not in st.session_state:
    st.session_state.tickers_list = list(preset_tickers.keys())
for t, wgt in preset_tickers.items():
    if f"w_val_{t}" not in st.session_state:
        st.session_state[f"w_val_{t}"] = float(wgt)

# --- Header ---
st.title("🌊 Stress Testing (Black-Swan Replay)")
st.markdown("""
Monte Carlo shows a *range of futures*; this page does the opposite — it drops your portfolio into the **worst moments of the past** and asks a simple question: *how badly would it have hurt, and how long to climb back?*

**What it does:** rebuilds your exact weights and replays them day-by-day through historical crises (2008 GFC, the 2020 COVID crash, and more), then measures the **maximum drawdown**, the **peak-to-trough slide**, and the **time to recover** — benchmarked against the S&P 500 (SPY).
""")
st.divider()

# --- Section 1: Portfolio (same editor as the other tools) ---
st.header("1. Portfolio", help="This shares the same portfolio you set on the other pages.")
col_input, col_add = st.columns([3, 1])
with col_input:
    new_ticker = st.text_input("Add Ticker", placeholder="Try AAPL", key="ticker_input_stress",
                               label_visibility="collapsed").strip().upper()
with col_add:
    if st.button("Add Ticker", use_container_width=True):
        if new_ticker and new_ticker not in st.session_state.tickers_list:
            st.session_state.tickers_list.append(new_ticker)
            st.session_state[f"w_val_{new_ticker}"] = 0.0
            st.rerun()

if not st.session_state.tickers_list:
    st.info("Add at least one ticker to run a stress test.")
    st.stop()

tickers = st.session_state.tickers_list
ticker_names = get_ticker_info(tickers)

b1, b2 = st.columns(2)
with b1:
    if st.button("⚖️ Set Equal Weights", use_container_width=True):
        eq = round(100.0 / len(tickers), 2)
        for t in tickers:
            st.session_state[f"w_val_{t}"] = eq
        st.rerun()
with b2:
    if st.button("🔄 Reset All to 0%", use_container_width=True):
        for t in tickers:
            st.session_state[f"w_val_{t}"] = 0.0
        st.rerun()

df = pd.DataFrame([{
    "Active": True, "Ticker": t, "Name": ticker_names.get(t, t),
    "Weight (%)": float(st.session_state.get(f"w_val_{t}", 0.0))
} for t in tickers])

edited = st.data_editor(
    df, use_container_width=True, hide_index=True, key="stress_weight_editor",
    column_config={
        "Active": st.column_config.CheckboxColumn("Active", help="Uncheck to remove", default=True),
        "Ticker": st.column_config.TextColumn("Ticker", disabled=True),
        "Name": st.column_config.TextColumn("Asset Name", disabled=True),
        "Weight (%)": st.column_config.NumberColumn("Weight", min_value=0.0, max_value=100.0, format="%.2f%%", step=0.01),
    },
)

to_remove = edited[edited["Active"] == False]["Ticker"].tolist()
if to_remove:
    for t_rem in to_remove:
        st.session_state.tickers_list.remove(t_rem)
        st.session_state.pop(f"w_val_{t_rem}", None)
    st.rerun()

for _, row in edited.iterrows():
    st.session_state[f"w_val_{row['Ticker']}"] = row["Weight (%)"]

active_tickers = edited["Ticker"].tolist()
weights_map = {t: float(edited.loc[edited["Ticker"] == t, "Weight (%)"].iloc[0]) for t in active_tickers}
total_weight = sum(weights_map.values())
st.markdown(f"**Total Assets:** {len(active_tickers)} | **Sum Weight:** {total_weight:.2f}%")

# --- Section 2: Pick crises ---
st.header("2. Choose Crises")
chosen = st.multiselect("Crisis windows to replay", list(CRISES.keys()),
                        default=["2008 Global Financial Crisis", "2020 COVID Crash"])
st.caption("⚠️ Pre-2005 crises (Tom Yum Kung, Dot-com) only replay if your portfolio holds long-history assets — "
           "individual stocks (e.g. AAPL, MSFT) or indices (e.g. ^GSPC). Most ETFs launched later and are skipped "
           "automatically, with a note telling you which.")
run = st.button("🌊 Run Stress Test", use_container_width=True)

# --- Section 3: Results ---
if run:
    if abs(total_weight - 100.0) > 0.1:
        st.error(f"⚠️ Weights sum to {total_weight:.2f}%. Please adjust to 100% first.")
        st.stop()
    if not chosen:
        st.error("Pick at least one crisis window.")
        st.stop()

    for name in chosen:
        start, end = CRISES[name]
        st.markdown(f"### {name}")
        st.caption(f"Window: {start} → {end}")

        with st.spinner(f"Replaying {name}..."):
            close = fetch_close(active_tickers + [BENCHMARK], start, end)

        if close.empty:
            st.error("No data returned for this window.")
            continue

        # Split benchmark out, decide which assets actually traded in this window
        bench = close[BENCHMARK].dropna() if BENCHMARK in close.columns else None
        asset_close = close[[c for c in close.columns if c != BENCHMARK]]
        usable, excluded = usable_columns(asset_close, start)

        if not usable:
            st.warning("None of your assets have price history for this window, so it can't be replayed. "
                       "(Many ETFs launched after 2008.)")
            continue
        if excluded:
            st.info("Excluded (no history this far back): " + ", ".join(excluded)
                    + " — remaining weights were renormalized.")

        sub_weights = {c: weights_map[c] for c in usable}
        equity = portfolio_equity(asset_close[usable], sub_weights)
        if equity is None:
            st.warning("Not enough overlapping data to build the portfolio for this window.")
            continue

        stats = drawdown_stats(equity)

        # Benchmark drawdown for comparison
        bench_stats, bench_equity = None, None
        if bench is not None and len(bench) > 2:
            bench_equity = (bench / bench.iloc[0])
            bench_equity = bench_equity.reindex(equity.index).dropna()
            if len(bench_equity) > 2:
                bench_stats = drawdown_stats(bench_equity)

        # --- Metric cards ---
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Max Drawdown</div>'
                        f'<div class="metric-value val-loss">{stats["mdd"]*100:.1f}%</div>'
                        f'<div class="metric-sub">SPY: {bench_stats["mdd"]*100:.1f}%</div></div>'
                        if bench_stats else
                        f'<div class="metric-card"><div class="metric-label">Max Drawdown</div>'
                        f'<div class="metric-value val-loss">{stats["mdd"]*100:.1f}%</div></div>',
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Peak → Trough</div>'
                        f'<div class="metric-value">{stats["decline_days"]} days</div>'
                        f'<div class="metric-sub">{stats["peak"].date()} → {stats["trough"].date()}</div></div>',
                        unsafe_allow_html=True)
        with c3:
            if stats["recovery_days"] is not None:
                rec_html = (f'<div class="metric-value">{stats["recovery_days"]} days</div>'
                            f'<div class="metric-sub">back to prior peak</div>')
            else:
                rec_html = ('<div class="metric-value val-loss">Not recovered</div>'
                            '<div class="metric-sub">within this window</div>')
            st.markdown(f'<div class="metric-card"><div class="metric-label">Recovery Time</div>{rec_html}</div>',
                        unsafe_allow_html=True)
        with c4:
            tr = stats["total_return"]
            cls = "val-gain" if tr >= 0 else "val-loss"
            st.markdown(f'<div class="metric-card"><div class="metric-label">Return Over Window</div>'
                        f'<div class="metric-value {cls}">{tr*100:+.1f}%</div>'
                        f'<div class="metric-sub">end vs start of window</div></div>',
                        unsafe_allow_html=True)

        # --- Equity curve chart (rebased to 100), portfolio vs SPY ---
        plot_df = pd.DataFrame({"Date": equity.index, "Your Portfolio": (equity / equity.iloc[0] * 100).values})
        if bench_equity is not None and len(bench_equity) > 2:
            b = (bench_equity / bench_equity.iloc[0] * 100).reindex(equity.index)
            plot_df["S&P 500 (SPY)"] = b.values
        long_df = plot_df.melt("Date", var_name="Series", value_name="Value").dropna()

        chart = alt.Chart(long_df).mark_line().encode(
            x=alt.X("Date:T", title=None),
            y=alt.Y("Value:Q", title="Growth of 100", scale=alt.Scale(zero=False)),
            color=alt.Color("Series:N", legend=alt.Legend(orient="bottom", title=None),
                            scale=alt.Scale(domain=["Your Portfolio", "S&P 500 (SPY)"],
                                            range=["#4589ff", "#8b949e"])),
            tooltip=["Date:T", "Series:N", alt.Tooltip("Value:Q", format=".1f")],
        ).properties(height=340)
        st.altair_chart(chart, use_container_width=True)
        st.divider()

else:
    st.info("Set your weights to 100%, choose one or more crises, and hit **Run Stress Test**.")
