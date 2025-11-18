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
        min-width: 250px !important;
        max-width: 300px !important;
        transition: all 0.3s ease-in-out !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background: #0f0f0f !important;
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        min-height: 100vh !important;
        transition: all 0.3s ease-in-out !important;
    }
    [data-testid="stSidebar"] > div {
        background: #0f0f0f !important;
        width: 100% !important;
        transition: all 0.3s ease-in-out !important;
    }
    
    /* Sidebar text */
    [data-testid="stSidebar"] * {
        color: #e8eef7 !important;
    }
    
    /* Page links styling */
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
        background: rgba(16, 185, 129, 0.08) !important;
        border-radius: 8px !important;
        margin: 12px 16px !important;
        padding: 14px 16px !important;
        color: #cbd5e1 !important;
        border: none !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
        letter-spacing: 0.3px !important;
        width: calc(100% - 32px) !important;
        text-align: left !important;
        display: block !important;
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
        justify-content: flex-start !important;
        align-items: stretch !important;
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
    
    /* ===============================================================
       MOBILE-FRIENDLY RESPONSIVE DESIGN (768px and below)
       =============================================================== */
    @media (max-width: 768px) {
        /* Page layout adjustments */
        .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            max-width: 100% !important;
        }
        
        /* Responsive headers */
        h1 {
            font-size: 1.6em !important;
            margin-bottom: 0.6em !important;
            padding: 10px !important;
            word-wrap: break-word !important;
        }
        
        h2 {
            font-size: 1.3em !important;
            margin-bottom: 0.4em !important;
        }
        
        h3 {
            font-size: 1.05em !important;
            margin-bottom: 0.3em !important;
        }
        
        /* Force horizontal blocks to stack */
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            gap: 0.8rem !important;
            width: 100% !important;
        }
        
        [data-testid="stColumn"] {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            flex: 1 !important;
        }
        
        [data-testid="stVerticalBlock"] > [data-testid="stColumn"] {
            width: 100% !important;
        }
        
        /* Input fields responsive */
        input, select, textarea {
            font-size: 16px !important;
            padding: 12px 10px !important;
            width: 100% !important;
            max-width: 100% !important;
        }
        
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea > div > div > textarea {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        label {
            font-size: 0.9em !important;
            margin-bottom: 0.4em !important;
            display: block !important;
            width: 100% !important;
        }
        
        /* Button sizing for touch - large hit targets */
        .stButton > button {
            padding: 14px 16px !important;
            font-size: 0.9em !important;
            min-height: 48px !important;
            border-radius: 6px !important;
            width: 100% !important;
            max-width: 100% !important;
        }
        
        [data-testid="stButton"] {
            width: 100% !important;
        }
        
        [data-testid="stButton"] > button {
            width: 100% !important;
        }
        
        /* Metric cards - responsive */
        [data-testid="metric-container"] {
            padding: 0.8em !important;
            margin: 0.6em 0 !important;
            width: 100% !important;
        }
        
        [data-testid="stMetric"] {
            width: 100% !important;
        }
        
        [data-testid="stMetricRow"] {
            flex-direction: column !important;
            width: 100% !important;
        }
        
        /* Chat container mobile */
        [data-testid="stContainer"] {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        /* Tabs - better touch targets */
        [role="tablist"] {
            gap: 0.3rem !important;
            overflow-x: auto !important;
            flex-wrap: wrap !important;
        }
        
        [role="tab"] {
            padding: 10px 10px !important;
            font-size: 0.8em !important;
            min-width: auto !important;
            flex: 1 !important;
            min-height: 40px !important;
        }
        
        /* Sidebar on mobile - full width when expanded */
        [data-testid="stSidebar"] {
            width: 100vw !important;
            max-width: 100vw !important;
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            height: 100vh !important;
            z-index: 999999 !important;
            background: #0f0f0f !important;
            border-right: 2px solid #10b981 !important;
            overflow-y: auto !important;
            padding: 1rem 0 !important;
            transition: all 0.3s ease-in-out !important;
            animation: slideInLeft 0.3s ease-in-out !important;
        }
        
        /* Smooth slide-in animation for sidebar */
        @keyframes slideInLeft {
            from {
                transform: translateX(-100%) !important;
                opacity: 0 !important;
            }
            to {
                transform: translateX(0) !important;
                opacity: 1 !important;
            }
        }
        
        /* Hamburger menu close button on mobile */
        [data-testid="stSidebar"] [data-testid="collapsedControl"] {
            position: fixed !important;
            top: 12px !important;
            left: 12px !important;
            z-index: 1000001 !important;
            background: rgba(16, 185, 129, 0.2) !important;
            border: 2px solid #10b981 !important;
            border-radius: 8px !important;
            padding: 10px 12px !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            width: 48px !important;
            height: 48px !important;
            min-width: 48px !important;
            min-height: 48px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            touch-action: manipulation !important;
        }
        [data-testid="stSidebar"] [data-testid="collapsedControl"]:active {
            background: rgba(16, 185, 129, 0.4) !important;
            transform: scale(0.95) !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
            display: flex !important;
            align-items: center !important;
            width: calc(100% - 24px) !important;
            padding: 16px 12px !important;
            margin: 8px 12px !important;
            font-size: 0.95em !important;
            background: rgba(16, 185, 129, 0.08) !important;
            border-radius: 8px !important;
            color: #cbd5e1 !important;
            text-align: left !important;
            border: none !important;
            transition: all 0.2s ease !important;
            min-height: 48px !important;
            user-select: none !important;
            -webkit-user-select: none !important;
            cursor: pointer !important;
            touch-action: manipulation !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
            background: rgba(16, 185, 129, 0.2) !important;
            color: #10b981 !important;
            transform: translateX(4px) !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15) !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:active {
            transform: translateX(2px) scale(0.98) !important;
            background: rgba(16, 185, 129, 0.25) !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {
            background: rgba(16, 185, 129, 0.3) !important;
            color: #10b981 !important;
            font-weight: 600 !important;
            box-shadow: inset 0 0 15px rgba(16, 185, 129, 0.1) !important;
            border-left: 3px solid #10b981 !important;
            padding-left: 9px !important;
        }
        
        /* Expander - mobile friendly */
        [data-testid="stExpander"] {
            border-radius: 6px !important;
            width: 100% !important;
        }
        
        [data-testid="stExpander"] summary {
            font-size: 0.9em !important;
            padding: 10px 8px !important;
            min-height: 40px !important;
        }
        
        /* Reduce divider margins on mobile */
        hr {
            margin: 0.8rem 0 !important;
        }
        
        /* Download buttons - stack on mobile */
        [data-testid="stDownloadButton"] {
            width: 100% !important;
        }
        
        [data-testid="stDownloadButton"] > button {
            width: 100% !important;
        }
        
        /* Better spacing for forms */
        .stTextInput, .stNumberInput, .stSelectbox, .stDateInput, .stTextArea {
            margin-bottom: 0.8rem !important;
            width: 100% !important;
        }
        
        /* Text readability on mobile */
        p, span {
            font-size: 0.95em !important;
            line-height: 1.5 !important;
            word-wrap: break-word !important;
        }
        
        /* Container padding */
        [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0.8rem !important;
            margin: 0.5rem 0 !important;
            border-radius: 8px !important;
            width: 100% !important;
        }
        
        /* Centered content */
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            text-align: center !important;
        }
        
        /* Chat input full width */
        [data-testid="stChatInput"] {
            width: 100% !important;
        }
        
        [data-testid="stChatInput"] input {
            width: 100% !important;
        }
        
        /* Form elements full width */
        [data-testid="stForm"] {
            width: 100% !important;
        }
        
        [data-testid="stForm"] > div {
            width: 100% !important;
        }
    }
    
    /* ===============================================================
       SMALL MOBILE (480px and below)
       =============================================================== */
    @media (max-width: 480px) {
        /* Very small screens */
        h1 {
            font-size: 1.5em !important;
            padding: 12px !important;
        }
        
        h2 {
            font-size: 1.2em !important;
        }
        
        h3 {
            font-size: 1em !important;
        }
        
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        /* Buttons more touchable */
        .stButton > button {
            width: 100% !important;
            padding: 12px 16px !important;
            font-size: 0.85em !important;
        }
        
        /* Input sizing */
        input, select, textarea {
            font-size: 16px !important;
            padding: 12px 10px !important;
        }
        
        /* Metrics stack better */
        [data-testid="stMetricRow"] {
            flex-direction: column !important;
        }
        
        /* Reduce gaps */
        [data-testid="stHorizontalBlock"] {
            gap: 0.5rem !important;
        }
        
        /* Radio buttons and checkboxes */
        [data-testid="stRadio"] {
            font-size: 0.9em !important;
        }
        
        /* Better text sizing */
        label {
            font-size: 0.85em !important;
        }
        
        p, span {
            font-size: 0.9em !important;
        }
        
        /* Sidebar for very small screens */
        [data-testid="stSidebar"] {
            width: 100vw !important;
            max-width: 100vw !important;
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            height: 100vh !important;
            padding: 2rem 0 1rem 0 !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
            width: calc(100% - 20px) !important;
            padding: 14px 10px !important;
            margin: 6px 10px !important;
            font-size: 0.9em !important;
        }
    }
    
    /* ===============================================================
       TABLET & LANDSCAPE (769px - 1024px)
       =============================================================== */
    @media (min-width: 769px) and (max-width: 1024px) {
        h1 {
            font-size: 2em !important;
        }
        
        h2 {
            font-size: 1.6em !important;
        }
        
        .block-container {
            max-width: 90% !important;
        }
        
        /* 2-column layout on tablets */
        [data-testid="stHorizontalBlock"] {
            gap: 1rem !important;
        }
        
        [data-testid="stColumn"] {
            width: 100% !important;
        }
        
        /* Sidebar for tablets */
        [data-testid="stSidebar"] {
            max-width: 200px !important;
            width: 200px !important;
        }
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
            width: calc(100% - 20px) !important;
            margin: 8px 10px !important;
            padding: 12px 12px !important;
            font-size: 0.9em !important;
        }
    }
</style>"""

def apply_theme(st_app):
    """Apply the dark theme to a Streamlit app"""
    st_app.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
