import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import os
import concurrent.futures
import time
from supabase import create_client, Client

# Page configuration
st.set_page_config(
    page_title="Customer Feedback System",
    page_icon="⭐",
    layout="centered"
)

# CSS - COMPACT UI & FORCE UP (Your preferred layout)
st.markdown("""
<style>
    /* 1. Remove the huge default top padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem;
        max-width: 800px;
    }
    
    /* 2. Hide header and footer */
    header {visibility: hidden !important;}
    footer {visibility: hidden;}
    
    /* 3. Pull Title Up */
    h1 {
        margin-top: -20px !important;
        padding-top: 0px !important;
        margin-bottom: 0px !important;
    }
    
    /* 4. REDUCE GAP BETWEEN ALL ELEMENTS */
    .stElementContainer {
        margin-bottom: -0.5rem !important;
    }
    
    /* 5. Tighten the star rating columns */
    div[data-testid="column"] {
        padding: 0px !important;
    }
    
    /* 6. Fix button spacing */
    .stButton button {
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Load secrets
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    try:
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
    except:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not GEMINI_API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Missing credentials")
    st.stop()

# Configure Gemini - USING STABLE MODEL
# Note: Reverted to 1.5-flash for stability as 2.5 is not fully available yet
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Supabase
@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# Session state
if 'submission_complete' not in st.session_state:
    st.session_state.submission_complete = False
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'last_rating' not in st.session_state:
    st.session_state.last_rating = None
if 'selected_rating' not in st.session_state:
    st.session_state.selected_rating = 5

# SAFETY SETTINGS
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# --- IMPROVED AI PROMPTS (Based on your reference code) ---

def generate_user_response(rating, review):
    """Generate a friendly, empathetic response using the improved prompt structure."""
    prompt = f"""You are an empathetic customer service manager personally responding to this customer review.

Rating: {rating}/5 stars
Review: "{review}"

Write a warm, personalized response (3-4 sentences) that:
1. SPECIFICALLY mentions what the customer talked about - use their exact words and context
2. Shows genuine emotion appropriate to their rating
3. If negative (1-2 stars): 
   - Apologize SPECIFICALLY for what went wrong
   - Offer a concrete solution or next step
4. If positive (4-5 stars): 
   - Express genuine excitement about the SPECIFIC things they praised
5. If neutral (3 stars): 
   - Acknowledge the mixed feelings and commit to improvement

CRITICAL: Be conversational, warm, and reference SPECIFIC details. Do not use a generic template.

Response:"""

    for attempt in range(3):
        try:
            response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
            if response.text:
                return response.text.strip()
        except Exception:
            time.sleep(1)

    # Fallback
    return f"Thank you for your {rating}-star review! We appreciate your feedback and will use it to improve our service."

def generate_summary(rating, review):
    """Generate detailed summary."""
    prompt = f"""Create a detailed admin summary (20 to 25 words) that captures the KEY SPECIFIC POINTS from this review.

Rating: {rating}/5 stars
Review: "{review}"

Focus on WHAT SPECIFICALLY they mentioned. Be concrete, informative, and actionable.

Summary:"""

    for attempt in range(3):
        try:
            response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
            if response.text:
                return response.text.strip()
        except:
            time.sleep(1)
    return f"{rating}⭐ review: {review[:40]}..."

def generate_actions(rating, review):
    """Generate specific actions."""
    prompt = f"""You are a business consultant analyzing this feedback. Generate 3 CONCRETE, SPECIFIC action items.

Rating: {rating}/5 stars
Review: "{review}"

Requirements:
1. Reference SPECIFIC issues or praises from the review
2. Use action verbs: Contact, Investigate, Train, Implement, etc.
3. Format as bullet points (•)

Actions:"""

    for attempt in range(3):
        try:
            response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
            if response.text:
                return response.text.strip()
        except:
            time.sleep(1)
            
    if rating <= 2:
        return "• Contact customer for service recovery\n• Investigate reported issues\n• Implement corrective measures"
    else:
        return "• Acknowledge feedback\n• Identify improvement areas\n• Monitor similar issues"

def generate_all_ai_content_parallel(rating, review):
    """Generate all AI content in parallel"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f1 = executor.submit(generate_user_response, rating, review)
        f2 = executor.submit(generate_summary, rating, review)
        f3 = executor.submit(generate_actions, rating, review)
        return f1.result(), f2.result(), f3.result()

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
        st.error(f"Database error: {e}")
        return False

def get_stats():
    try:
        response = supabase.table('feedback').select('*').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            return len(df), df['rating'].mean(), len(df)
    except:
        pass
    return 0, 0, 0

def reset_form():
    st.session_state.submission_complete = False
    st.session_state.last_response = None
    st.session_state.last_rating = None
    st.session_state.selected_rating = 5
    st.rerun()

# MAIN UI
st.title("⭐ Customer Feedback System")
st.markdown("We value your feedback! Please share your experience with us.")

# Spacer
st.write("")

if st.session_state.submission_complete:
    st.success("✅ Thank you! Your feedback has been submitted.")
    
    st.markdown("### Our Response")
    st.info(st.session_state.last_response)
    
    if st.session_state.last_rating >= 4:
        st.balloons()
        st.markdown("🎉 **We're thrilled you had a great experience!**")
    elif st.session_state.last_rating <= 2:
        st.markdown("🙏 **We're sorry to hear about your experience.**")
    
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    
    if st.button("📝 Submit Another Review", use_container_width=True, type="primary"):
        reset_form()

else:
    st.markdown("### Rate Your Experience")
    
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            star_emoji = "⭐" if i < st.session_state.selected_rating else "☆"
            if st.button(star_emoji, key=f"star_{i+1}", use_container_width=True):
                st.session_state.selected_rating = i + 1
                st.rerun()

    star_display = "⭐" * st.session_state.selected_rating + "☆" * (5 - st.session_state.selected_rating)
    st.markdown(f"""
        <div style='text-align: center; margin-top: -10px;'>
            <p style='font-size: 2rem; margin: 0;'>{star_display}</p>
            <p style='color: #666; font-size: 0.9rem; margin-top: 0px; margin-bottom: 10px;'>
                {st.session_state.selected_rating}/5 stars selected
            </p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("feedback_form", clear_on_submit=True):
        review = st.text_area(
            "Tell us more about your experience:",
            placeholder="What did you like? What could we improve?",
            height=120,
            max_chars=500
        )
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True, type="primary")

    if submitted:
        if not review.strip():
            st.error("⚠️ Please write a review.")
        elif len(review.strip()) < 10:
            st.error("⚠️ Please provide more details (at least 10 chars).")
        else:
            with st.spinner("🤖 Processing your feedback..."):
                start_time = time.time()
                try:
                    ai_response, ai_summary, recommended_actions = generate_all_ai_content_parallel(
                        st.session_state.selected_rating, review
                    )
                    
                    if save_feedback(st.session_state.selected_rating, review, ai_response, ai_summary, recommended_actions):
                        st.session_state.submission_complete = True
                        st.session_state.last_response = ai_response
                        st.session_state.last_rating = st.session_state.selected_rating
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Footer stats
st.markdown("---")
total, avg_rating, recent = get_stats()
if total > 0:
    c1, c2, c3 = st.columns(3)
    c1.metric("Reviews", total)
    c2.metric("Avg", f"{avg_rating:.1f}⭐")
    c3.metric("Total", recent)
