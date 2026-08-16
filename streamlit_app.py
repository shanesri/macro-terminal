import streamlit as st

st.set_page_config(page_title="Macro Terminal", page_icon="📈", layout="wide")

# The entrypoint runs before every page, so this sidebar greeting shows on ALL pages.
with st.sidebar:
    st.markdown("## สวัสดี 🙏 Welcome!")
    st.caption("A little lab where I turn finance theory into working tools.")

# Custom page names + icons (defined here, not from filenames — so the sidebar reads nicely).
pages = [
    st.Page("home.py", title="Welcome Note", icon="🙏", default=True),
    st.Page("pages/1_Weight_Optimizer.py", title="Weight Optimizer", icon="⚖️"),
    st.Page("pages/2_Monte_Carlo_Simulator.py", title="Monte Carlo Simulator", icon="📈"),
    st.Page("pages/3_Crisis_Replay.py", title="Crisis Replay", icon="🌊"),
]
st.navigation(pages).run()
