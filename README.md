# 📈 Macro Terminal

An interactive suite of portfolio-analytics tools built in **Python + Streamlit**, pulling live market data from **Yahoo Finance** (`yfinance`). It turns CFA-curriculum theory — Monte Carlo simulation, Modern Portfolio Theory, risk metrics — into hands-on tools anyone can run in the browser.

This repository merges three previously separate apps into a **single multi-page Streamlit application**:

| Old repo | Now |
|---|---|
| `shanegreeting` | Home page (`streamlit_app.py`) |
| `portoptimize` | Weight Optimizer page (Efficient Frontier) |
| `portmng` | Monte Carlo Simulator page |

## Structure

```
macro-terminal/
├── streamlit_app.py                    # Home: intro + roadmap (app entry point)
├── pages/
│   ├── 1_Weight_Optimizer.py          # Efficient Frontier optimizer (MPT)
│   ├── 2_Monte_Carlo_Simulator.py     # Monte Carlo (+ Crisis regime option)
│   └── 3_Crisis_Replay.py             # Historical stress test (actual crisis path)
├── requirements.txt
├── .devcontainer/
└── README.md
```

Streamlit auto-builds the sidebar navigation from the `pages/` folder — no hand-wired cross-links between apps anymore.

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy (Streamlit Community Cloud)

Point a new app at this repo with **main file path** `streamlit_app.py`. The two tools appear automatically as pages in the sidebar.

## Roadmap

- ✅ **Phase 1 — Buy & Hold MCS.** Pick stocks, date range, and weights; run a Monte Carlo simulation of portfolio outcomes.
- ✅ **Phase 2 — Efficient Frontier.** Find the weight mix that maximises return for a given level of risk (Modern Portfolio Theory).
- 🚧 **Phase 3 — Stress Testing.** Replay portfolios through Black-Swan windows (2008 GFC, 2020 COVID) to see how they'd have held up.
- ⬜ **Phase 4 — Alternative Weighting.** Risk Parity and other schemes vs. plain Buy & Hold.
- ⬜ **Phase 5 — Non-Normal Returns.** Fat-tailed / non-normal distribution models to capture tail risk.
- ⬜ **Phase 6 — Rebalancing.** Simulate periodic (6- / 12-month) auto-rebalancing and measure the impact.

---

Built by [Shane (Rattapon Sriphathoorat)](https://shanesri.com) · [LinkedIn](https://www.linkedin.com/in/shanesri/)
