"""
Shared CSS styling for consistent theming across all pages
Professional Dark Theme with Premium Green Accents
"""

DARK_THEME_CSS = """<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* Hide deploy button and toolbar */
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    .stDeployButton {display: none !important;}
    
    /* Hide loading skeletons and spinners */
    [data-testid="stElementContainer"] > div > div > div {
        animation: none !important;
    }
    .stSpinner {display: none !important;}
    [data-testid="stSpinner"] {display: none !important;}
    
    html, body, div, section, main {
        background: #0f0f0f !important;
        color: #e8eef7 !important;
    }
    
    /* Comprehensive background coverage */
    .main {
        background: #0f0f0f !important;
        color: #e8eef7;
    }
    [data-testid="stAppViewContainer"] {
        background: #0f0f0f !important;
    }
    [data-testid="stMainBlockContainer"] {
        background: #0f0f0f !important;
    }
    .stApp {
        background: #0f0f0f !important;
    }
    .appview-container {
        background: #0f0f0f !important;
    }
    .main > [data-testid="stBlock"] {
        background: #0f0f0f !important;
    }
    [data-testid="stVerticalBlock"] {
        background: #0f0f0f !important;
    }
    section {
        background: #0f0f0f !important;
    }
    
    /* Sidebar styling - Professional Dark with Premium Green */
    [data-testid="stSidebar"] {
        background: #0f0f0f !important;
        border-right: 2px solid #10b981 !important;
        box-shadow: 2px 0 20px rgba(16, 185, 129, 0.15) !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background: #0f0f0f !important;
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
    }
    [data-testid="stSidebar"] > div {
        background: #0f0f0f !important;
        width: 100% !important;
    }
    
    /* Sidebar text */
    [data-testid="stSidebar"] * {
        color: #e8eef7 !important;
    }
    
    /* Page links styling */
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
        background: rgba(16, 185, 129, 0.08) !important;
        border-radius: 8px !important;
        margin: 12px auto !important;
        padding: 14px 16px !important;
        color: #cbd5e1 !important;
        border: none !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
        letter-spacing: 0.3px !important;
        width: 85% !important;
        text-align: center !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
        background: rgba(16, 185, 129, 0.15) !important;
        border-left-color: transparent !important;
        transform: translateX(5px) !important;
        color: #10b981 !important;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {
        background: rgba(16, 185, 129, 0.25) !important;
        border-left-color: transparent !important;
        font-weight: 600 !important;
        color: #10b981 !important;
        box-shadow: inset 0 0 15px rgba(16, 185, 129, 0.1) !important;
    }
    
    /* Center nav links container */
    [data-testid="stSidebar"] nav {
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
    }
    
    /* Remove default streamlit styling */
    [data-testid="stMetricRow"] {
        background: transparent !important;
    }
    
    /* Headers with better hierarchy */
    h1 {
        color: #10b981 !important;
        font-weight: 700 !important;
        font-size: 2.2em !important;
        margin-bottom: 1.2em !important;
        letter-spacing: 0.5px !important;
    }
    
    h2 {
        color: #10b981 !important;
        font-weight: 700 !important;
        font-size: 1.8em !important;
        margin-top: 1.5em !important;
        margin-bottom: 0.8em !important;
        letter-spacing: 0.3px !important;
    }
    
    h3 {
        color: #10b981 !important;
        font-weight: 600 !important;
        font-size: 1.4em !important;
        margin-bottom: 0.6em !important;
    }
    
    h4, h5, h6 {
        color: #10b981 !important;
        font-weight: 600 !important;
    }
    
    /* CRITICAL: Force white text on green backgrounds */
    h1[style*="background"],
    h1[style*="gradient"],
    p[style*="background"],
    p[style*="gradient"],
    div[style*="background"] h1,
    div[style*="background"] p,
    div[style*="background"] span,
    div[style*="background"] * {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Text with better readability */
    p, span {
        color: #d8dde6 !important;
        line-height: 1.6 !important;
    }
    
    /* Container styling with better spacing */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(15, 15, 15, 0.5) !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        border-radius: 10px !important;
        padding: 1.5em !important;
        margin: 1em 0 !important;
    }
    
    /* Input fields - Professional styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea,
    .stDateInput > div > div > input,
    input, 
    select, 
    textarea {
        background-color: #1a1f3a !important;
        color: #e8eef7 !important;
        border: 1.5px solid #10b981 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 0.95em !important;
        transition: all 0.2s ease !important;
    }
    
    /* Input focus state - Premium green glow */
    input:focus,
    select:focus,
    textarea:focus {
        border-color: #10b981 !important;
        background-color: #242d4a !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15), inset 0 1px 3px rgba(0,0,0,0.2) !important;
    }
    
    /* Placeholder text */
    input::placeholder, 
    textarea::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
    }
    
    /* Select options */
    option {
        background-color: #1a1f3a !important;
        color: #e8eef7 !important;
        padding: 10px !important;
    }
    
    /* Streamlit number input */
    [data-testid="stNumberInput"] input {
        background-color: #1a1f3a !important;
        color: #e8eef7 !important;
    }
    
    /* Streamlit text area */
    [data-testid="stTextArea"] textarea {
        background-color: #1a1f3a !important;
        color: #e8eef7 !important;
    }
    
    /* Input label text */
    label {
        color: #e8eef7 !important;
        font-weight: 600 !important;
        font-size: 0.95em !important;
        margin-bottom: 0.5em !important;
        display: block !important;
    }
    
    /* Remove button container background - All levels */
    [data-testid="stButton"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    /* Hide column borders around buttons - Direct child */
    [data-testid="stButton"] > div {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Remove wrapper styling */
    .stButton {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Hide black box styling - Deep nesting */
    [data-testid="stButton"] > div > div {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* All descendants of button containers */
    [data-testid="stButton"] * {
        background: transparent !important;
    }
    
    /* Button wrapper container */
    [data-testid="stVerticalBlock"] > [data-testid="stButton"] {
        background: transparent !important;
        padding: 0 !important;
    }
    
    /* Button in column context */
    [data-testid="stColumn"] [data-testid="stButton"] {
        background: transparent !important;
        padding: 0 !important;
    }
    
    [data-testid="stColumn"] [data-testid="stButton"] > div {
        background: transparent !important;
        padding: 0 !important;
    }
    
    [data-testid="stColumn"] [data-testid="stButton"] > div > div {
        background: transparent !important;
        padding: 0 !important;
    }
    
    /* Buttons - Premium Green with enhanced styling */
    .stButton > button {
        background-color: #10b981 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 14px 32px !important;
        font-weight: 600 !important;
        font-size: 0.95em !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.25) !important;
        letter-spacing: 0.4px !important;
        cursor: pointer !important;
    }
    .stButton > button:hover {
        background-color: #059669 !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.35) !important;
    }
    .stButton > button:active {
        transform: translateY(-1px) !important;
    }
    
    /* Secondary button styling */
    .stButton > button:nth-child(2) {
        background-color: rgba(16, 185, 129, 0.15) !important;
        color: #10b981 !important;
        border: 1.5px solid #10b981 !important;
    }
    .stButton > button:nth-child(2):hover {
        background-color: rgba(16, 185, 129, 0.25) !important;
    }
    
    /* Divider with better spacing */
    hr {
        background-color: rgba(16, 185, 129, 0.25) !important;
        border: none !important;
        height: 1.5px !important;
        margin: 2em 0 !important;
    }
    
    /* Column and row spacing */
    [data-testid="stHorizontalBlock"] {
        gap: 1.5em !important;
    }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    
    /* Reduce spacing for forms */
    [data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }
    
    /* Compact input spacing */
    .stTextInput, .stNumberInput, .stSelectbox, .stDateInput {
        margin-bottom: 0.3rem !important;
    }
    
    /* Reduce header spacing */
    h1, h2, h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Compact section labels */
    label {
        margin-bottom: 0.2rem !important;
        padding-bottom: 0.2rem !important;
    }
    
    /* Reduce subheader spacing */
    .stSubheader {
        margin-bottom: 0.3rem !important;
    }
    
    /* Reduce divider spacing */
    hr {
        margin: 0.8rem 0 !important;
    }
    
    /* Compact columns gap */
    [data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: rgba(16, 185, 129, 0.05) !important;
        border: 1px solid rgba(16, 185, 129, 0.15) !important;
        border-radius: 10px !important;
        padding: 1.2em !important;
    }
    
    /* Expander styling */
    [data-testid="stExpander"] {
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        border-radius: 8px !important;
        background: rgba(16, 185, 129, 0.03) !important;
    }
    
    [data-testid="stExpander"] summary {
        color: #10b981 !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stExpander"] summary:hover {
        background: rgba(16, 185, 129, 0.08) !important;
    }
    
    /* Better spacing between elements */
    [data-testid="stVerticalBlock"] > * + * {
        margin-top: 1.5em !important;
    }
    
    /* Table/Column alignment - Equal height */
    [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: stretch !important;
        height: 100% !important;
    }
    
    [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"] > * {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        min-height: 100% !important;
    }
    
    /* Column content alignment */
    [data-testid="stColumn"] {
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    [data-testid="stColumn"] > [data-testid="stVerticalBlock"] {
        height: 100% !important;
        justify-content: space-between !important;
    }
    
    /* Text within columns - vertically centered */
    [data-testid="stColumn"] p,
    [data-testid="stColumn"] div > p {
        margin: 0 !important;
        padding: 10px 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 50px !important;
    }
    
    /* Button in columns - full height */
    [data-testid="stColumn"] .stButton > button {
        height: 100% !important;
        min-height: 50px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
</style>"""

def apply_theme(st_app):
    """Apply the dark theme to a Streamlit app"""
    st_app.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
