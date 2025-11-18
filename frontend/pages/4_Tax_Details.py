import streamlit as st
import json
from datetime import datetime
from utils.state import init_session_state
from utils.styles import DARK_THEME_CSS

# Set page config for mobile
st.set_page_config(
    page_title="Tax Details",
    layout="centered",
    initial_sidebar_state="auto"
)

init_session_state()

# Apply shared dark theme
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

st.markdown("<h1 style='background: #1a1f3a; color: white !important; text-align: center; padding: 20px; border-radius: 8px; margin: 0; border: 2px solid #10b981; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);'>👤 Tax Details Collection</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #10b981 !important; text-align: center; opacity: 0.9; font-size: 0.95em;'>Enter your personal and filing information</p>", unsafe_allow_html=True)

# Initialize session state for tax details
if "tax_details" not in st.session_state:
    st.session_state.tax_details = {}

st.markdown("---")
st.markdown("<div class='section-header'>📋 Personal Information</div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    first_name = st.text_input(
        "First Name",
        value=st.session_state.tax_details.get("first_name", ""),
        key="first_name_input"
    )
    st.session_state.tax_details["first_name"] = first_name

with col2:
    last_name = st.text_input(
        "Last Name",
        value=st.session_state.tax_details.get("last_name", ""),
        key="last_name_input"
    )
    st.session_state.tax_details["last_name"] = last_name

col1, col2 = st.columns(2)

with col1:
    ssn = st.text_input(
        "Social Security Number (XXX-XX-XXXX)",
        value=st.session_state.tax_details.get("ssn", ""),
        placeholder="123-45-6789",
        key="ssn_input"
    )
    st.session_state.tax_details["ssn"] = ssn

with col2:
    dob_value = st.session_state.tax_details.get("dob")
    # Convert ISO string back to date object if it exists
    if isinstance(dob_value, str):
        try:
            dob_value = datetime.fromisoformat(dob_value).date()
        except (ValueError, TypeError):
            dob_value = None
    
    dob = st.date_input(
        "Date of Birth",
        value=dob_value,
        key="dob_input"
    )
    st.session_state.tax_details["dob"] = dob.isoformat() if dob else None

col1, col2 = st.columns(2)

with col1:
    email = st.text_input(
        "Email Address",
        value=st.session_state.tax_details.get("email", ""),
        key="email_input"
    )
    st.session_state.tax_details["email"] = email

with col2:
    phone = st.text_input(
        "Phone Number",
        value=st.session_state.tax_details.get("phone", ""),
        placeholder="(123) 456-7890",
        key="phone_input"
    )
    st.session_state.tax_details["phone"] = phone

st.markdown("---")
st.markdown("<div class='section-header'>📝 Filing Status & Dependents</div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    filing_status = st.selectbox(
        "Filing Status",
        ["Select...", "Single", "Married Filing Jointly", "Married Filing Separately", "Head of Household", "Qualifying Widow/Widower"],
        index=0 if st.session_state.tax_details.get("filing_status") == "Select..." or not st.session_state.tax_details.get("filing_status") 
              else ["Select...", "Single", "Married Filing Jointly", "Married Filing Separately", "Head of Household", "Qualifying Widow/Widower"].index(st.session_state.tax_details.get("filing_status", "Select...")),
        key="filing_status_input"
    )
    st.session_state.tax_details["filing_status"] = filing_status if filing_status != "Select..." else ""

with col2:
    num_dependents = st.number_input(
        "Number of Dependents",
        min_value=0,
        max_value=20,
        value=st.session_state.tax_details.get("num_dependents", 0),
        key="num_dependents_input"
    )
    st.session_state.tax_details["num_dependents"] = int(num_dependents)

# Dependent details
if num_dependents > 0:
    st.markdown("#### Dependent Information")
    
    if "dependents" not in st.session_state.tax_details:
        st.session_state.tax_details["dependents"] = []
    
    # Ensure we have enough slots for dependents
    while len(st.session_state.tax_details["dependents"]) < num_dependents:
        st.session_state.tax_details["dependents"].append({})
    
    # Trim if we have too many
    st.session_state.tax_details["dependents"] = st.session_state.tax_details["dependents"][:num_dependents]
    
    for idx in range(num_dependents):
        with st.expander(f"👶 Dependent {idx + 1}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                dep_name = st.text_input(
                    f"Dependent {idx + 1} Name",
                    value=st.session_state.tax_details["dependents"][idx].get("name", ""),
                    key=f"dep_name_{idx}"
                )
                st.session_state.tax_details["dependents"][idx]["name"] = dep_name
            
            with col2:
                dep_ssn = st.text_input(
                    f"Dependent {idx + 1} SSN",
                    value=st.session_state.tax_details["dependents"][idx].get("ssn", ""),
                    placeholder="123-45-6789",
                    key=f"dep_ssn_{idx}"
                )
                st.session_state.tax_details["dependents"][idx]["ssn"] = dep_ssn
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                dep_dob_value = st.session_state.tax_details["dependents"][idx].get("dob")
                # Convert ISO string back to date object if it exists
                if isinstance(dep_dob_value, str):
                    try:
                        dep_dob_value = datetime.fromisoformat(dep_dob_value).date()
                    except (ValueError, TypeError):
                        dep_dob_value = None
                
                dep_dob = st.date_input(
                    f"Dependent {idx + 1} DOB",
                    value=dep_dob_value,
                    key=f"dep_dob_{idx}"
                )
                st.session_state.tax_details["dependents"][idx]["dob"] = dep_dob.isoformat() if dep_dob else None
            
            with col2:
                dep_relationship = st.selectbox(
                    f"Dependent {idx + 1} Relationship",
                    ["Select...", "Child", "Parent", "Sibling", "Other"],
                    index=0 if not st.session_state.tax_details["dependents"][idx].get("relationship")
                          else ["Select...", "Child", "Parent", "Sibling", "Other"].index(st.session_state.tax_details["dependents"][idx].get("relationship", "Select...")),
                    key=f"dep_rel_{idx}"
                )
                st.session_state.tax_details["dependents"][idx]["relationship"] = dep_relationship if dep_relationship != "Select..." else ""
            
            with col3:
                dep_months = st.number_input(
                    f"Dependent {idx + 1} Months in Home",
                    min_value=0,
                    max_value=12,
                    value=st.session_state.tax_details["dependents"][idx].get("months_in_home", 12),
                    key=f"dep_months_{idx}"
                )
                st.session_state.tax_details["dependents"][idx]["months_in_home"] = int(dep_months)

st.markdown("---")
st.subheader("[MONEY] Income Sources")

col1, col2 = st.columns(2)

with col1:
    has_w2 = st.checkbox(
        "📄 W-2 Income (Employment)",
        value=st.session_state.tax_details.get("has_w2", False),
        key="has_w2_input"
    )
    st.session_state.tax_details["has_w2"] = has_w2

with col2:
    has_1099_nec = st.checkbox(
        "📄 1099-NEC (Self-Employment)",
        value=st.session_state.tax_details.get("has_1099_nec", False),
        key="has_1099_nec_input"
    )
    st.session_state.tax_details["has_1099_nec"] = has_1099_nec

col1, col2 = st.columns(2)

with col1:
    has_1099_int = st.checkbox(
        "📄 1099-INT (Interest Income)",
        value=st.session_state.tax_details.get("has_1099_int", False),
        key="has_1099_int_input"
    )
    st.session_state.tax_details["has_1099_int"] = has_1099_int

with col2:
    has_1099_div = st.checkbox(
        "📄 1099-DIV (Dividend Income)",
        value=st.session_state.tax_details.get("has_1099_div", False),
        key="has_1099_div_input"
    )
    st.session_state.tax_details["has_1099_div"] = has_1099_div

st.markdown("---")
st.subheader("🏠 Deductions & Credits")

col1, col2 = st.columns(2)

with col1:
    deduction_type = st.radio(
        "Deduction Type",
        ["Standard Deduction", "Itemized Deductions"],
        index=0 if st.session_state.tax_details.get("deduction_type") != "Itemized Deductions" else 1,
        key="deduction_type_input"
    )
    st.session_state.tax_details["deduction_type"] = deduction_type

with col2:
    if deduction_type == "Itemized Deductions":
        itemized_amount = st.number_input(
            "Itemized Deductions Amount ($)",
            min_value=0.0,
            value=st.session_state.tax_details.get("itemized_amount", 0.0),
            step=100.0,
            key="itemized_amount_input"
        )
        st.session_state.tax_details["itemized_amount"] = itemized_amount
    else:
        st.info("ℹ️ Standard Deduction will be applied based on filing status and age")

col1, col2 = st.columns(2)

with col1:
    education_credits = st.number_input(
        "Education Credits ($)",
        min_value=0.0,
        value=st.session_state.tax_details.get("education_credits", 0.0),
        step=100.0,
        key="education_credits_input"
    )
    st.session_state.tax_details["education_credits"] = education_credits

with col2:
    child_tax_credit = st.number_input(
        "Child Tax Credit ($)",
        min_value=0.0,
        value=st.session_state.tax_details.get("child_tax_credit", 0.0),
        step=100.0,
        key="child_tax_credit_input"
    )
    st.session_state.tax_details["child_tax_credit"] = child_tax_credit

col1, col2 = st.columns(2)

with col1:
    earned_income_credit = st.number_input(
        "Earned Income Credit ($)",
        min_value=0.0,
        value=st.session_state.tax_details.get("earned_income_credit", 0.0),
        step=100.0,
        key="earned_income_credit_input"
    )
    st.session_state.tax_details["earned_income_credit"] = earned_income_credit

with col2:
    other_credits = st.number_input(
        "Other Credits ($)",
        min_value=0.0,
        value=st.session_state.tax_details.get("other_credits", 0.0),
        step=100.0,
        key="other_credits_input"
    )
    st.session_state.tax_details["other_credits"] = other_credits

st.markdown("---")
st.subheader("📍 Address Information")

address = st.text_input(
    "Street Address",
    value=st.session_state.tax_details.get("address", ""),
    key="address_input"
)
st.session_state.tax_details["address"] = address

col1, col2, col3 = st.columns(3)

with col1:
    city = st.text_input(
        "City",
        value=st.session_state.tax_details.get("city", ""),
        key="city_input"
    )
    st.session_state.tax_details["city"] = city

with col2:
    state = st.selectbox(
        "State",
        ["", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"],
        index=0 if not st.session_state.tax_details.get("state") else ["", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"].index(st.session_state.tax_details.get("state", "")),
        key="state_input"
    )
    st.session_state.tax_details["state"] = state

with col3:
    zip_code = st.text_input(
        "ZIP Code",
        value=st.session_state.tax_details.get("zip_code", ""),
        key="zip_code_input"
    )
    st.session_state.tax_details["zip_code"] = zip_code

st.markdown("---")
st.subheader("[CHART] Summary & Actions")

# Display summary
col1, col2, col3 = st.columns(3)

with col1:
    name = f"{st.session_state.tax_details.get('first_name', '')} {st.session_state.tax_details.get('last_name', '')}".strip()
    st.metric("Filer Name", name if name else "Not provided")

with col2:
    filing = st.session_state.tax_details.get('filing_status', 'Not selected')
    st.metric("Filing Status", filing if filing else "Not selected")

with col3:
    dependents = st.session_state.tax_details.get('num_dependents', 0)
    st.metric("Dependents", dependents)

# Save/Clear buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💾 Save Tax Details", use_container_width=True):
        # Validate required fields
        if not st.session_state.tax_details.get("first_name"):
            st.error("[FAIL] First Name is required")
        elif not st.session_state.tax_details.get("last_name"):
            st.error("[FAIL] Last Name is required")
        elif not st.session_state.tax_details.get("filing_status"):
            st.error("[FAIL] Filing Status is required")
        else:
            st.success("[YES] Tax Details Saved!")
            st.json(st.session_state.tax_details)

with col2:
    if st.button("🔄 Clear All", use_container_width=True):
        st.session_state.tax_details = {}
        st.rerun()

with col3:
    if st.button("📥 Export JSON", use_container_width=True):
        import json
        json_str = json.dumps(st.session_state.tax_details, indent=2, default=str)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"tax_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

st.markdown("---")
st.info("""
💡 **How to use this page:**
1. Fill in your personal information
2. Select your filing status and number of dependents
3. Add dependent details if applicable
4. Select income sources (W-2, 1099-NEC, 1099-INT, etc.)
5. Enter deductions and credits
6. Provide address information
7. Click **Save Tax Details** to store for tax calculation

[YES] These details will be used with your extracted form data for accurate tax calculation.
""")
