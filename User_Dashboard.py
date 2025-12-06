import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import os
import time
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Customer Feedback System",
    page_icon="⭐",
    layout="centered"
)

# ---------------------------------------------------------
# 2. CSS - COMPACT UI
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Remove huge default top padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem;
        max-width: 800px;
    }
    /* Hide header and footer */
    header {visibility: hidden !important;}
    footer {visibility: hidden;}
    /* Pull Title Up */
    h1 {
        margin-top: -20px !important;
        padding-top: 0px !important;
        margin-bottom: 0px !important;
    }
    /* Reduce gap between elements */
    .stElementContainer {
        margin-bottom: -0.5rem !important; 
    }
    /* Tighten columns */
    div[data-testid="column"] {
        padding: 0px !important;
    }
    /* Fix button spacing */
    .stButton button {
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. SETUP CREDENTIALS
# ---------------------------------------------------------
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    # Fallback for local testing if secrets not found
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not GEMINI_API_KEY or not SUPABASE_URL:
    st.error("⚠️ Missing API Keys. Please check your .streamlit/secrets.toml file.")
    st.stop()

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
try:
    # Try Flash first (faster/cheaper), fallback to Pro
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-2.5-flasH')

# Configure Supabase
@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = get_supabase()
except Exception as e:
    st.error(f"Supabase Connection Error: {e}")
    st.stop()

# ---------------------------------------------------------
# 4. SESSION STATE
# ---------------------------------------------------------
if 'submission_complete' not in st.session_state:
    st.session_state.submission_complete = False
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'last_rating' not in st.session_state:
    st.session_state.last_rating = None
if 'selected_rating' not in st.session_state:
    st.session_state.selected_rating = 5

# ---------------------------------------------------------
# 5. AI FUNCTIONS (SEQUENTIAL FOR FREE TIER STABILITY)
# ---------------------------------------------------------

def generate_user_response(rating, review):
    prompt = f"""You are a customer service manager. Write a warm, 3-sentence response to this review.
    Rating: {rating}/5 stars
    Review: "{review}"
    Response:"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

def generate_summary(rating, review):
    prompt = f"""Summarize this review in 15 words for an admin dashboard.
    Rating: {rating}/5
    Review: "{review}"
    Summary:"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

def generate_actions(rating, review):
    prompt = f"""List 3 short bullet points (max 5 words each) for actions to take.
    Rating: {rating}/5
    Review: "{review}"
    Format:
    • Action 1
    • Action 2
    • Action 3"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

# ---------------------------------------------------------
# 6. DATABASE FUNCTIONS
# ---------------------------------------------------------
def save_feedback(rating, review, ai_response, ai_summary, recommended_actions):
    try:
        data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'rating': rating,
            'review': review,
            'ai_response': ai_response,
            'ai_summary': ai_summary,
            'recommended_actions': recommended_actions
        }
        supabase.table('feedback').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"DB Error: {str(e)}")
        return False

def get_stats():
    try:
        response = supabase.table('feedback').select('rating, timestamp').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            total = len(df)
            avg = df['rating'].mean() if total > 0 else 0
            recent = len(df[df['timestamp'] >= (datetime.now() - pd.Timedelta(days=7))])
            return total, avg, recent
    except:
        return 0, 0, 0

def reset_form():
    st.session_state.submission_complete = False
    st.session_state.last_response = None
    st.session_state.selected_rating = 5
    st.rerun()

# ---------------------------------------------------------
# 7. MAIN UI
# ---------------------------------------------------------
st.title("⭐ Customer Feedback System")
st.markdown("We value your feedback! Please share your experience.", help=None)
st.write("") 

# --- SUBMISSION COMPLETE VIEW ---
if st.session_state.submission_complete:
    st.success("✅ Feedback submitted!")
    
    if st.session_state.last_rating >= 4:
        st.balloons()
    
    st.subheader("Our Response")
    st.info(st.session_state.last_response)
    
    if st.button("📝 Submit Another Review", use_container_width=True, type="primary"):
        reset_form()

# --- FEEDBACK FORM VIEW ---
else:
    st.markdown("### Rate Your Experience")
    
    # Star Buttons
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            star_emoji = "⭐" if i < st.session_state.selected_rating else "☆"
            if st.button(star_emoji, key=f"star_{i+1}", use_container_width=True):
                st.session_state.selected_rating = i + 1
                st.rerun()

    # Star Display Text
    star_display = "⭐" * st.session_state.selected_rating + "☆" * (5 - st.session_state.selected_rating)
    st.markdown(f"""
        <div style='text-align: center; margin-top: -10px;'>
            <p style='font-size: 2rem; margin: 0;'>{star_display}</p>
            <p style='color: #666; font-size: 0.9rem; margin-top: 0px; margin-bottom: 10px;'>
                {st.session_state.selected_rating}/5 stars selected
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Input Form
    with st.form("feedback_form", clear_on_submit=True):
        review = st.text_area(
            "Tell us more:",
            placeholder="What did you like? What could we improve?",
            height=120, 
            max_chars=500
        )
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True, type="primary")

    if submitted:
        if not review.strip():
            st.error("⚠️ Please write a review.")
        elif len(review.strip()) < 5:
            st.error("⚠️ Please write at least 5 characters.")
        else:
            with st.spinner("🤖 Processing..."):
                # 1. Generate User Response
                ai_response = generate_user_response(st.session_state.selected_rating, review)
                
                # Check for API Error immediately
                if "ERROR:" in ai_response:
                    st.error("⚠️ API Failed: " + ai_response)
                else:
                    # If successful, wait 1s (Rate Limit Protection) and continue
                    time.sleep(1) 
                    ai_summary = generate_summary(st.session_state.selected_rating, review)
                    
                    time.sleep(1)
                    recommended_actions = generate_actions(st.session_state.selected_rating, review)

                    # Save to DB
                    if save_feedback(st.session_state.selected_rating, review, ai_response, ai_summary, recommended_actions):
                        st.session_state.submission_complete = True
                        st.session_state.last_response = ai_response
                        st.session_state.last_rating = st.session_state.selected_rating
                        st.rerun()

# ---------------------------------------------------------
# 8. FOOTER STATS
# ---------------------------------------------------------
st.markdown("---")
total, avg_rating, recent = get_stats()
if total > 0:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Reviews", total)
    c2.metric("Average", f"{avg_rating:.1f}⭐")
    c3.metric("This Week", recent)
