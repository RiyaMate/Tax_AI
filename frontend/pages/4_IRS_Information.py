import streamlit as st
from utils.state import init_session_state
from utils.styles import DARK_THEME_CSS
from utils.sidebar_toggle import add_mobile_sidebar_toggle

st.set_page_config(
    page_title="IRS Information",
    layout="wide",
    initial_sidebar_state="auto"
)

init_session_state()

st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# Add mobile sidebar toggle
add_mobile_sidebar_toggle()

st.markdown("<h1 style='background: #1a1f3a; color: white !important; text-align: center; padding: 20px; border-radius: 8px; margin: 0; border: 2px solid #ff6b6b; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);'>IRS INFORMATION & RESOURCES</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #ff6b6b !important; text-align: center; opacity: 0.9; font-size: 0.95em;'>Comprehensive Guide to IRS Services, Forms & Tax Information</p>", unsafe_allow_html=True)

tabs = st.tabs(["Home", "Tax Forms", "Filing Status", "Tax Topics", "Payment Info", "Help & Support"])

with tabs[0]:
    st.subheader("Welcome to IRS Information Center")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
**About the IRS**

The Internal Revenue Service (IRS) is a bureau of the Department of the Treasury responsible for:
- Collecting federal taxes
- Enforcing tax laws
- Administering tax benefits
- Processing tax returns
- Managing taxpayer accounts

**Official Website:** www.irs.gov
        """)
    
    with col2:
        st.success("""
**Quick Facts**

- **Established:** 1862
- **Employees:** ~80,000
- **Offices:** Nationwide
- **Languages Supported:** 200+
- **Phone Support:** Available year-round
- **E-file Available:** Yes, free & paid options
        """)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tax Year", "2024")
    with col2:
        st.metric("Filing Deadline", "April 15, 2025")
    with col3:
        st.metric("Extensions Available", "Until Oct 15, 2025")
    
    st.markdown("---")
    st.subheader("Key Services")
    
    service_col1, service_col2, service_col3 = st.columns(3)
    
    with service_col1:
        st.write("**File Your Tax Return**")
        st.write("""
- Online filing (IRS Free File)
- Paper forms
- Tax professional help
- E-file services
        """)
    
    with service_col2:
        st.write("**Check Status**")
        st.write("""
- Filing status (Where's My Refund?)
- Payment status
- Account information
- Tax records
        """)
    
    with service_col3:
        st.write("**Get Help**")
        st.write("""
- Phone support
- In-person appointments
- Online assistance
- Publication library
        """)

with tabs[1]:
    st.subheader("Tax Forms & Publications")
    
    st.write("**Find the forms you need for your tax situation:**")
    
    form_tabs = st.tabs(["Individual Forms", "Business Forms", "Income Documents", "Deduction Forms"])
    
    with form_tabs[0]:
        st.markdown("""
**Individual Income Tax Forms**

**Main Forms:**
- **Form 1040** - U.S. Individual Income Tax Return
  - Primary form for most taxpayers
  - Used with schedules for deductions, credits
  
- **Form 1040-SR** - For Senior Citizens (65+)
  - Larger print
  - Easier to complete
  
- **Form 1040-NR** - Nonresident Alien
  - For foreign nationals with US income

**Schedule Forms (attached to 1040):**
- **Schedule A** - Itemized Deductions
  - Mortgage interest, property taxes, charitable gifts
  
- **Schedule C** - Business Income (Self-Employment)
  - Sole proprietors and freelancers
  
- **Schedule D** - Capital Gains and Losses
  - Investment earnings/losses
  
- **Schedule E** - Rental Property Income
  - Real estate and rental income
        """)
    
    with form_tabs[1]:
        st.markdown("""
**Business Tax Forms**

- **Form 1065** - Partnership Return
- **Form 1120** - Corporation Income Tax
- **Form 1120-S** - S Corporation Income Tax
- **Form 990-N** - Tax Exempt Organization
- **Schedule SE** - Self-Employment Tax
- **Form 8832** - Entity Classification
        """)
    
    with form_tabs[2]:
        st.markdown("""
**Income Report Forms (Received by Taxpayers)**

- **Form W-2** - Wage and Tax Statement
  - Employer reported income and withholding
  
- **Form 1099-NEC** - Nonemployee Compensation
  - Freelance, contract, business income
  
- **Form 1099-INT** - Interest Income
  - Bank interest, bond income
  
- **Form 1099-DIV** - Dividend Income
  - Stock dividends, mutual funds
  
- **Form 1099-MISC** - Miscellaneous Income
  - Royalties, prizes, awards
  
- **Form 1099-K** - Payment Card Transactions
  - Credit/debit card payments received
  
- **Form 1099-B** - Brokerage Transactions
  - Stock and bond sales
        """)
    
    with form_tabs[3]:
        st.markdown("""
**Deduction & Credit Forms**

- **Form 1098-T** - Education Credit
  - Qualified education expenses
  
- **Form 1098** - Mortgage Interest Statement
  - Home loan interest paid
  
- **Form 5498** - IRA Contribution Information
  - IRA and Roth IRA contributions
  
- **Form 8863** - Education Credit
  - American Opportunity / Lifetime Learning
  
- **Form 8839** - Adoption Credit
  - Qualified adoption expenses
  
- **Form 3468** - Investment Credit
  - Energy and business property credits
        """)
    
    st.markdown("---")
    st.info("Download all forms free at: www.irs.gov/forms")

with tabs[2]:
    st.subheader("Check Your Filing Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**How to Check Where's My Refund?**")
        st.markdown("""
1. Visit www.irs.gov
2. Select "Where's My Refund?"
3. Enter:
   - Social Security Number
   - Filing Status
   - Refund Amount (exact dollar)

**Processing Times:**
- E-filed returns: 21 calendar days
- Paper returns: 4-6 weeks
- After acceptance: 1-2 weeks usually

**Status Updates:**
- Updated daily (except weekends)
- SMS alerts available
- Email notifications option
        """)
    
    with col2:
        st.warning("""
**Important Notes**

- Have your return handy
- Must wait 24 hours after filing
- Refund amount should be exact
- Payment method selected matters
- Direct deposit is fastest (3-5 days)

**If You Don't See Status:**
- Still being processed
- Return is under review
- Additional info needed
- Contact IRS if delayed 21+ days
        """)
    
    st.markdown("---")
    st.subheader("What to Do If Refund is Delayed")
    
    st.markdown("""
**Reasons for Delay:**
1. Return still processing (normal)
2. Math errors detected
3. Missing information
4. Identity verification needed
5. Fraud investigation
6. Payment hold

**Solutions:**
- Check status online (updated daily)
- Call IRS: 1-800-829-1040
- Visit local IRS office
- Response to notices (if received)
- Patient waiting (most resolve)
    """)

with tabs[3]:
    st.subheader("Tax Topics & Guidance")
    
    topic_tabs = st.tabs(["Filing Requirements", "Deductions", "Credits", "Special Situations"])
    
    with topic_tabs[0]:
        st.markdown("""
**Who Must File a Tax Return?**

**Generally Must File If:**
- Single: Gross income $13,850+ (2023)
- Married Filing Jointly: $27,700+ (2023)
- Head of Household: $20,800+ (2023)
- 65+ (Single): $15,000+ (2023)

**Additional Filing Requirements:**
- Self-employment income: $400+
- Had taxes withheld (to get refund)
- Received Advance Child Tax Credit
- Health insurance requirement penalty

**Dependents:**
- Must file if gross income $1,150+
- Parents may claim on their return
        """)
    
    with topic_tabs[1]:
        st.markdown("""
**Common Tax Deductions**

**Standard Deduction (Easier)**
- Single 2024: $14,600
- Married 2024: $29,200
- Head of Household 2024: $21,900
- Reduces taxable income by fixed amount

**Itemized Deductions (If Higher)**
- Mortgage interest
- Property taxes
- State income taxes (max $10,000)
- Charitable contributions
- Medical expenses (over 7.5% AGI)
- Business expenses (self-employed)
- Education expenses
- Investment losses

**Self-Employment Deductions:**
- Home office
- Business equipment
- Vehicle expenses
- Business supplies
- Professional fees
        """)
    
    with topic_tabs[2]:
        st.markdown("""
**Tax Credits (Direct Reduction)**

**Major Credits:**
- Earned Income Tax Credit (EITC)
  - Up to $3,995 depending on income
  
- Child Tax Credit
  - $2,000 per child under 17
  
- Child and Dependent Care Credit
  - Up to $3,000 in care expenses
  
- Education Credits
  - American Opportunity: $2,500
  - Lifetime Learning: $2,000
  
- Saver's Credit
  - Retirement account contributions
  
- Energy Credits
  - Solar, wind installations

**How Credits Work:**
Credits reduce tax owed dollar-for-dollar
More valuable than deductions
        """)
    
    with topic_tabs[3]:
        st.markdown("""
**Special Tax Situations**

**Self-Employed:**
- File Schedule C with Form 1040
- Pay self-employment tax (15.3%)
- Quarterly estimated tax payments
- Can deduct business expenses

**Retired:**
- Social Security may be taxable
- Withdrawal strategies matter
- Form 1040-SR available (65+)

**Freelancer/Contractor:**
- Receive 1099-NEC forms
- Quarterly tax payments required
- Deduct business expenses
- Estimated tax form: 1040-ES

**Rental Property Owner:**
- Report rental income on Schedule E
- Can deduct property expenses
- Depreciation considerations
- Capital gains on sale
        """)

with tabs[4]:
    st.subheader("Payment Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
**Payment Methods**

**Online:**
- IRS Direct Pay (free)
- Credit/debit card (fee)
- EFTPS (free, bank account)

**Mail:**
- Check or money order
- Include Form 1040-V

**Phone:**
- Call 1-800-829-1040
- Payment plan options

**In Person:**
- Local IRS office
- By appointment
        """)
    
    with col2:
        st.success("""
**Payment Due Date**

**Tax Year 2024:**
- Regular deadline: April 15, 2025
- Automatic extension: Oct 15, 2025
- Interest accrues after due date
- Penalties for late payment

**Payment Plans:**
- Short-term: up to 180 days
- Long-term: installment agreement
- Partial payment
        """)
    
    st.markdown("---")
    st.subheader("Check Your Payment Status")
    
    st.markdown("""
**What's My Payment Status?**

Visit: www.irs.gov/payments

**Information Needed:**
- Social Security Number
- Date of Birth
- Zip Code
- Amount Paid

**Shows:**
- Payment received
- Application date
- Remaining balance
- Payment history
    """)

with tabs[5]:
    st.subheader("Help & Support Resources")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Contact IRS**")
        st.markdown("""
**Phone:**
- Main: 1-800-829-1040
- TTY: 1-800-829-4059
- Business: 1-800-829-4933

**Hours:**
- Monday-Friday
- 7am-7pm local time

**Best Times:**
- Early morning
- Mid-week (less busy)
- Before April 15
        """)
    
    with col2:
        st.write("**Online Resources**")
        st.markdown("""
**Official Site:** www.irs.gov

**Available:**
- Interactive tax assistant
- FAQs database
- Publication library
- Form downloads
- Video tutorials

**Account Tools:**
- Create online account
- Check filing status
- Payment information
- Tax transcripts
        """)
    
    with col3:
        st.write("**Taxpayer Assistance**")
        st.markdown("""
**Free Help:**
- VITA (low-income)
- TCE (seniors)
- Military OneSource

**Paid Services:**
- Tax professionals
- CPAs
- Enrolled Agents
- Tax software

**Accessibility:**
- Multiple languages
- TTY/relay services
- In-person help
        """)
    
    st.markdown("---")
    st.subheader("Common Questions")
    
    with st.expander("When is the tax deadline?"):
        st.write("The tax filing deadline is typically April 15th. For 2024 taxes, the deadline is April 15, 2025.")
    
    with st.expander("Can I get an extension?"):
        st.write("Yes, you can request an automatic 6-month extension (until October 15). File Form 4868 before the original deadline.")
    
    with st.expander("What if I can't pay my taxes?"):
        st.write("Contact the IRS. Options include short-term extensions, payment plans, and installment agreements. File anyway to avoid penalties.")
    
    with st.expander("How do I file my taxes?"):
        st.write("You can e-file online, use tax software, work with a tax professional, or file a paper return by mail.")
    
    with st.expander("What documents do I need?"):
        st.write("Gather W-2s, 1099s, receipts for deductions, and any tax documents received. Your Social Security Number and last year's return help too.")
    
    with st.expander("Can I amend my return?"):
        st.write("Yes, use Form 1040-X (Amended U.S. Individual Income Tax Return) within 3 years of the original filing date.")

st.markdown("---")
st.caption("Official IRS Information | Visit www.irs.gov for complete details | Call 1-800-829-1040 for support")
