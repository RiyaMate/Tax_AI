import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)
print(f"[DEBUG] Frontend .env loaded. VISION_AGENT_API_KEY: {os.getenv('VISION_AGENT_API_KEY')[:50]}...")

import streamlit as st
from utils.styles import DARK_THEME_CSS

st.set_page_config(
    page_title="Welcome - Tax Calculator",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items={"About": "GreenGrowth Tax AI System"}
)

# Apply shared dark theme
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# Remove top padding and hide header/footer + mobile responsive styling
st.markdown("""
<style>
    header {display: none;}
    footer {display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stDecoration"] {display: none;}
    .reportview-container .main .block-container {max-width: 100%;}
    
    /* Mobile responsive header */
    @media (max-width: 768px) {
        .branding-header {padding: 30px 15px !important; margin: 20px 0;}
        .branding-header h1 {font-size: 2em !important;}
        .branding-header p {font-size: 0.9em !important;}
    }
</style>
""", unsafe_allow_html=True)

# Header with GreenGrowth branding
st.markdown("""
<div class='branding-header' style='background: #2d2d2d; padding: 50px 30px; border-radius: 12px; text-align: center; margin-bottom: 40px; border: 2px solid #7bff50;'>
    <div style='font-size: 3em; margin-bottom: 15px;'>🌱</div>
    <h1 style='color: #7bff50; font-size: 2.8em; margin-bottom: 10px; font-weight: 900;'>GreenGrowth CPAs</h1>
    <p style='color: #d0d0d0; font-size: 1.2em; margin-bottom: 5px;'>Leading CPA Firm Offering Expert Tax, Audit & Financial Services</p>
    <p style='color: #888; font-size: 0.95em;'>Serving Diverse US Industries</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Main content
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📄</div>
        <div class="feature-title">Process Your Document</div>
        <div class="feature-desc">Upload and parse your tax documents using AI-powered LandingAI technology. Automatically extract all relevant fields from W-2s, 1099s, and more.</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">👤</div>
        <div class="feature-title">Tax Details</div>
        <div class="feature-desc">Enter your personal information, filing status, dependents, and other details needed for accurate tax calculation.</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🧮</div>
        <div class="feature-title">Tax Calculator</div>
        <div class="feature-desc">Get precise 2024 tax calculations with automatic Form 1040 PDF generation. See your refund or amount owed instantly.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# How it works
st.markdown("<h2 style='text-align: center; color: white;'>How It Works</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='text-align: center; padding: 20px; color: white;'>
        <div style='font-size: 2.5em; margin-bottom: 10px;'>1️⃣</div>
        <div style='font-weight: bold; font-size: 1.1em;'>Upload Documents</div>
        <div style='opacity: 0.9; margin-top: 10px;'>Upload your tax documents to get started</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='text-align: center; padding: 20px; color: white;'>
        <div style='font-size: 2.5em; margin-bottom: 10px;'>2️⃣</div>
        <div style='font-weight: bold; font-size: 1.1em;'>Enter Details</div>
        <div style='opacity: 0.9; margin-top: 10px;'>Provide your personal and tax information</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='text-align: center; padding: 20px; color: white;'>
        <div style='font-size: 2.5em; margin-bottom: 10px;'>3️⃣</div>
        <div style='font-weight: bold; font-size: 1.1em;'>Get Results</div>
        <div style='opacity: 0.9; margin-top: 10px;'>Download your Form 1040 PDF instantly</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Features list
st.markdown("<h2 style='text-align: center; color: #1b5e20; margin-top: 40px;'>Why Choose GreenGrowth CPAs?</h2>", unsafe_allow_html=True)

features_html = """
<div style='background: #f5f5f5; padding: 30px; border-radius: 12px; margin: 20px 0; border-left: 6px solid #4caf50;'>
    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 30px; color: #333;'>
        <div style='padding: 15px;'>
            <div style='font-weight: bold; margin-bottom: 8px; font-size: 1.1em; color: #1b5e20;'>✅ Expert Tax Specialists</div>
            <div style='opacity: 0.85; line-height: 1.6;'>Certified CPAs with decades of experience in diverse industries</div>
        </div>
        <div style='padding: 15px;'>
            <div style='font-weight: bold; margin-bottom: 8px; font-size: 1.1em; color: #1b5e20;'>✅ 2024 IRS Compliant</div>
            <div style='opacity: 0.85; line-height: 1.6;'>All calculations follow the latest 2024 tax regulations</div>
        </div>
        <div style='padding: 15px;'>
            <div style='font-weight: bold; margin-bottom: 8px; font-size: 1.1em; color: #1b5e20;'>✅ AI-Powered Efficiency</div>
            <div style='opacity: 0.85; line-height: 1.6;'>LandingAI technology automatically extracts data from documents</div>
        </div>
        <div style='padding: 15px;'>
            <div style='font-weight: bold; margin-bottom: 8px; font-size: 1.1em; color: #1b5e20;'>✅ Comprehensive Services</div>
            <div style='opacity: 0.85; line-height: 1.6;'>Tax preparation, audit, and financial consulting all in one place</div>
        </div>
    </div>
</div>
"""
st.markdown(features_html, unsafe_allow_html=True)

st.markdown("---")

# Call to action
st.markdown("""
<div style='text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #1b5e20 0%, #2d7a3e 100%); border-radius: 12px; margin: 40px 0;'>
    <div style='font-size: 1.5em; margin-bottom: 15px; color: white; font-weight: bold;'>
        Ready to File Your Taxes?
    </div>
    <div style='color: #c8e6c9; margin-bottom: 25px; font-size: 1.05em;'>
        Let GreenGrowth CPAs handle your tax preparation with precision and care
    </div>
    <div style='color: #a5d6a7;'>
        Use the sidebar to navigate to <strong style='color: white;'>Process Your Document</strong> to get started
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center; padding: 30px 20px; background: #e8f5e9; border-top: 2px solid #4caf50; border-radius: 8px; margin-top: 40px; color: #1b5e20;'>
    <div style='font-weight: bold; font-size: 1.1em; margin-bottom: 10px;'>🌱 GreenGrowth CPAs</div>
    <div style='font-size: 0.9em; opacity: 0.85;'>Expert Tax & Financial Services for Your Business</div>
    <div style='margin-top: 15px; font-size: 0.85em; opacity: 0.7;'>For audit purposes, always cross-reference official IRS guidance</div>
</div>
""", unsafe_allow_html=True)
