import streamlit as st

st.set_page_config(
    page_title="Customer Feedback System",
    page_icon="⭐",
    layout="wide"
)

st.title("⭐ Customer Feedback System")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 👤 User Feedback

    **For Customers:**
    - Submit your experience
    - Rate our service (1-5 stars)
    - Get instant AI-powered response
    - Help us improve!

    👈 **Click "User Feedback" in the sidebar to start**
    """)
    st.info("📝 Share your thoughts and get a personalized response")

with col2:
    st.markdown("""
    ### 📊 Admin Dashboard

    **For Administrators:**
    - View all customer feedback
    - Real-time analytics & charts
    - AI-generated summaries
    - Recommended actions

    👈 **Click "Admin Dashboard" in the sidebar**
    """)
    st.success("📈 Monitor feedback and gain insights")

st.markdown("---")

st.markdown("""
### 🤖 Features

- **AI-Powered Responses**: Instant, personalized replies using Google Gemini
- **Smart Analytics**: Real-time sentiment analysis and trends
- **Action Recommendations**: AI suggests next steps based on feedback
- **Live Updates**: Admin dashboard auto-refreshes every 5 seconds
- **Fast Processing**: Parallel API calls (3x faster than sequential)

### 🚀 Get Started

Use the **sidebar** to navigate between User Feedback and Admin Dashboard.
""")

st.caption("Built with Streamlit • Powered by Google Gemini AI")
