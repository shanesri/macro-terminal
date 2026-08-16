import streamlit as st

# --- Page Config ---
st.set_page_config(page_title="Macro Terminal", page_icon="📈", layout="wide")

# --- Custom CSS for Styling ---
st.markdown(
    """
    <style>
    /* Center the main block */
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

    /* Content Styling */
    .intro-section {
        background-color: #1e2130;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #30363d;
        margin-bottom: 30px;
    }

    /* Workflow Tiles */
    .workflow-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }
    .workflow-tile {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
    }
    .workflow-tile h4 {
        margin-top: 0;
        color: #deff9a;
    }

    /* Roadmap Styles */
    .roadmap-container {
        border-left: 2px solid #30363d;
        margin-left: 20px;
        padding-left: 30px;
        position: relative;
    }

    .phase-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        position: relative;
    }

    .phase-card.active {
        border: 1px solid #deff9a;
        background-color: #1c2128;
    }

    .phase-badge {
        position: absolute;
        left: -41px;
        top: 20px;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background-color: #30363d;
        border: 4px solid #0a0c10;
    }

    .phase-badge.active {
        background-color: #deff9a;
        box-shadow: 0 0 10px #deff9a;
    }

    .status-pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 10px;
        background-color: #deff9a;
        color: #000;
    }

    .contact-link {
        color: #deff9a;
        text-decoration: none;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Sidebar greeting ---
with st.sidebar:
    st.markdown("## สวัสดี 🙏 Welcome!")
    st.caption("A little lab where I turn finance theory into working tools — pick one from the menu above.")

# --- Header ---
st.title("📈 Welcome to the Macro Terminal")

# --- A bit about me ---
st.markdown(
    """
    <div class="intro-section">
        <h3>A bit about me</h3>
        <p>Hi! I’m <strong>Shane from Thailand 🇹🇭</strong>. I work in <strong>finance</strong> and I’ve passed all three levels of the <strong>CFA Program</strong>. 
        This app is my personal lab for turning CFA concepts into working, interactive tools — a place to explore portfolio theory in code rather than just on paper.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Workflow ---
st.subheader("How I built this (The 'Finance Guy' way)")
st.write("I’m definitely not a professional developer — I’m a finance guy who leaned on **AI, Python, and Streamlit** to bring these ideas to life. Huge thanks to those tools for doing the heavy lifting so I could focus on the finance. Here’s the simple stack I used:")

st.markdown(
    """
    <div class="workflow-container">
        <div class="workflow-tile">
            <h4>🐍 Python</h4>
            <p style="font-size: 14px; color: #daffde;">I picked Python because it’s surprisingly easy to learn, but it’s still powerful enough to handle all the heavy math for finance. It lets me automate calculations that would take forever in a spreadsheet, and the charts actually look pretty nice and meaningful!</p>
        </div>
        <div class="workflow-tile">
            <h4>🐙 GitHub</h4>
            <p style="font-size: 14px; color: #daffde;">This is basically where I keep my "save files." It stores my code in the cloud so I don't lose it and can track every single change.</p>
        </div>
        <div class="workflow-tile">
            <h4>🎨 Streamlit</h4>
            <p style="font-size: 14px; color: #daffde;">This is what you’re looking at right now! It’s a really cool tool that takes my Python code and turns it into a website. It saved me from having to learn how to design a site from scratch.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Balloon magic trigger
if st.button("🎈 Celebrate with Streamlit magic!", use_container_width=True):
    st.balloons()
    st.toast("Balloons sent! 🚀")

st.divider()

# --- Roadmap ---
st.subheader("🗺️ What I’ve built")

st.markdown(
    """
    <div class="roadmap-container">
        <div class="status-pill">All 6 phases live 🎉</div>
        <!-- Phase 1 -->
        <div class="phase-card active">
            <div class="phase-badge active"></div>
            <h4 style="margin: 0;">Phase 1 · Buy & Hold Monte Carlo ✅</h4>
            <p style="color: #8b949e; font-size: 14px; margin-top: 10px;">
                Pick your assets, a date range, and weights; a Monte Carlo simulation shows the range of outcomes your portfolio could see over time.
            </p>
        </div>
        <!-- Phase 2 -->
        <div class="phase-card active">
            <div class="phase-badge active"></div>
            <h4 style="margin: 0;">Phase 2 · Finding "Better" Weights ✅</h4>
            <p style="color: #8b949e; font-size: 14px; margin-top: 10px;">
                An Efficient Frontier optimizer that finds the mix of assets giving the best return for the level of risk you take.
            </p>
        </div>
        <!-- Phase 3 -->
        <div class="phase-card active">
            <div class="phase-badge active"></div>
            <h4 style="margin: 0;">Phase 3 · Stress Testing ✅</h4>
            <p style="color: #8b949e; font-size: 14px; margin-top: 10px;">
                Replays your portfolio through real Black-Swan events (2008, COVID, Tom Yum Kung) and can simulate crisis-level volatility to show how it would hold up.
            </p>
        </div>
        <!-- Phase 4 -->
        <div class="phase-card active">
            <div class="phase-badge active"></div>
            <h4 style="margin: 0;">Phase 4 · Alternative Weighting ✅</h4>
            <p style="color: #8b949e; font-size: 14px; margin-top: 10px;">
                Risk Parity weighting — each asset is sized by its volatility so every holding contributes a similar amount of risk.
            </p>
        </div>
        <!-- Phase 5 -->
        <div class="phase-card active">
            <div class="phase-badge active"></div>
            <h4 style="margin: 0;">Phase 5 · Real-World Math ✅</h4>
            <p style="color: #8b949e; font-size: 14px; margin-top: 10px;">
                Fat-tailed (Student-t) returns, so extreme crashes are modelled far more realistically than a plain bell curve allows.
            </p>
        </div>
        <!-- Phase 6 -->
        <div class="phase-card active">
            <div class="phase-badge active"></div>
            <h4 style="margin: 0;">Phase 6 · To Rebalance or Not? ✅</h4>
            <p style="color: #8b949e; font-size: 14px; margin-top: 10px;">
                Compare Buy & Hold against periodic and threshold rebalancing to see whether — and how often — resetting your weights actually helps.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Contact ---
st.divider()
st.subheader("🤝 Let’s chat!")
st.markdown(
    """
    I work in finance and love talking markets. If you want to talk shop — or you’ve spotted a bug or have an idea for the app — I’d love to hear from you.
    
    👉 **LinkedIn:** [shanesri](https://www.linkedin.com/in/shanesri/)
    """,
    unsafe_allow_html=True,
)
