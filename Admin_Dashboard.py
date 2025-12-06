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

# CSS - Move UI up
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem;
        max-width: 800px;
    }
    .stApp header {
        display: none;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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

# Configure Gemini - USE LATEST MODEL
genai.configure(api_key=GEMINI_API_KEY)

# Use the NEWEST model available (as of Dec 2025)
MODEL_NAME = 'gemini-2.0-flash-exp'  # Latest experimental model

try:
    model = genai.GenerativeModel(MODEL_NAME)
    st.caption(f"✅ Using model: {MODEL_NAME}")
except:
    # Fallback to stable model
    MODEL_NAME = 'gemini-1.5-flash'
    model = genai.GenerativeModel(MODEL_NAME)
    st.caption(f"✅ Using fallback model: {MODEL_NAME}")

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

# SAFETY SETTINGS - BLOCK NOTHING
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# GENERATION CONFIG
GENERATION_CONFIG = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 500,
}

# AI FUNCTION WITH PROPER ERROR HANDLING
def generate_user_response(rating, review):
    """Generate AI response - GUARANTEED TO WORK"""

    prompt = f"""You are a friendly customer service manager. Write a warm response to this review.

Rating: {rating} out of 5 stars
Customer review: {review}

Write 3-4 sentences thanking them and addressing their specific feedback.

Your response:"""

    for attempt in range(3):
        try:
            # Generate with safety settings OFF
            response = model.generate_content(
                prompt,
                safety_settings=SAFETY_SETTINGS,
                generation_config=GENERATION_CONFIG
            )

            # Check if response was blocked
            if hasattr(response, 'prompt_feedback'):
                if response.prompt_feedback.block_reason:
                    st.warning(f"⚠️ Attempt {attempt+1}: Response blocked - {response.prompt_feedback.block_reason}")
                    time.sleep(1)
                    continue

            # Check if we got candidates
            if not response.candidates:
                st.warning(f"⚠️ Attempt {attempt+1}: No candidates returned")
                time.sleep(1)
                continue

            # Try to get text
            if hasattr(response, 'text') and response.text:
                text = response.text.strip()
                if len(text) > 20:
                    st.success(f"✅ AI generated response on attempt {attempt+1}")
                    return text

            # Try parts
            if response.candidates[0].content.parts:
                text = response.candidates[0].content.parts[0].text.strip()
                if len(text) > 20:
                    st.success(f"✅ AI generated response on attempt {attempt+1}")
                    return text

        except Exception as e:
            st.warning(f"⚠️ Attempt {attempt+1} error: {str(e)[:100]}")
            time.sleep(2)

    # If all attempts fail, use template
    st.info("ℹ️ Using template response (AI generation failed)")

    if rating >= 4:
        return f"Thank you so much for your wonderful {rating}-star review! We're thrilled to hear about your positive experience. Your feedback means the world to us and motivates our team to keep delivering excellent service. We look forward to serving you again soon!"
    elif rating <= 2:
        return f"We sincerely apologize for your experience that led to this {rating}-star review. Your feedback is extremely important to us and we take it very seriously. We would love the opportunity to make things right and discuss how we can improve. Please don't hesitate to reach out to our support team."
    else:
        return f"Thank you for your {rating}-star review and honest feedback. We appreciate you taking the time to share your experience with us. We're always working to improve our service and your input helps us identify areas where we can do better. We hope to exceed your expectations next time!"

def generate_summary(rating, review):
    """Generate summary"""
    prompt = f"Summarize in 15 words: {rating}-star review: {review}"

    try:
        response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if hasattr(response, 'text') and response.text:
            return response.text.strip()
    except:
        pass

    return f"{rating}⭐ review: {review[:40]}..."

def generate_actions(rating, review):
    """Generate actions"""
    prompt = f"List 3 action items for this {rating}-star review: {review}. Use bullet points (•)."

    try:
        response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if hasattr(response, 'text') and response.text:
            return response.text.strip()
    except:
        pass

    if rating <= 2:
        return "• Contact customer immediately\n• Investigate root cause\n• Implement corrective measures"
    elif rating >= 4:
        return "• Thank customer personally\n• Request testimonial\n• Share positive feedback with team"
    else:
        return "• Acknowledge feedback\n• Identify improvement areas\n• Follow up on concerns"

def generate_all_ai_content_parallel(rating, review):
    """Generate all AI content"""
    results = {}

    def call_user():
        results['user'] = generate_user_response(rating, review)

    def call_summary():
        results['summary'] = generate_summary(rating, review)

    def call_actions():
        results['actions'] = generate_actions(rating, review)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(call_user),
            executor.submit(call_summary),
            executor.submit(call_actions)
        ]
        concurrent.futures.wait(futures)

    return results['user'], results['summary'], results['actions']

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
        supabase.table('Feedback').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

def get_stats():
    try:
        response = supabase.table('Feedback').select('*').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            total = len(df)
            avg_rating = df['rating'].mean()
            week_start = (datetime.now() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
            recent = len(df[df['timestamp'] >= week_start])
            return total, avg_rating, recent
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

if st.session_state.submission_complete:
    st.success("✅ Thank you! Your feedback has been submitted.")
    st.markdown("---")
    st.subheader("Our Response")
    st.info(st.session_state.last_response)

    if st.session_state.last_rating >= 4:
        st.balloons()
        st.markdown("🎉 **We're thrilled you had a great experience!**")
    elif st.session_state.last_rating <= 2:
        st.markdown("🙏 **We're sorry. We'll work to make it right.**")

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📝 Submit Another Review", use_container_width=True, type="primary"):
            reset_form()

else:
    st.subheader("Rate Your Experience")
    st.markdown("**Click to select rating:**")

    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            star_emoji = "⭐" if i < st.session_state.selected_rating else "☆"
            if st.button(star_emoji, key=f"star_{i+1}", use_container_width=True):
                st.session_state.selected_rating = i + 1
                st.rerun()

    star_display = "⭐" * st.session_state.selected_rating + "☆" * (5 - st.session_state.selected_rating)
    st.markdown(f"<p style='text-align: center; font-size: 2rem; margin: 0.5rem 0;'>{star_display}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #666; margin-bottom: 1.5rem;'>{st.session_state.selected_rating}/5 stars selected</p>", unsafe_allow_html=True)

    st.markdown("---")

    with st.form("feedback_form", clear_on_submit=True):
        review = st.text_area(
            "Tell us more about your experience:",
            placeholder="What did you like? What could we improve?",
            height=150,
            max_chars=500
        )
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True, type="primary")

    if submitted:
        if not review.strip():
            st.error("⚠️ Please write a review.")
        elif len(review.strip()) < 10:
            st.error("⚠️ At least 10 characters please.")
        else:
            with st.spinner("🤖 Generating AI response..."):
                start_time = time.time()

                try:
                    ai_response, ai_summary, recommended_actions = generate_all_ai_content_parallel(
                        st.session_state.selected_rating, review
                    )

                    if save_feedback(st.session_state.selected_rating, review, ai_response, ai_summary, recommended_actions):
                        elapsed_time = time.time() - start_time
                        st.success(f"✅ Processed in {elapsed_time:.1f} seconds!")

                        st.session_state.submission_complete = True
                        st.session_state.last_response = ai_response
                        st.session_state.last_rating = st.session_state.selected_rating
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

st.markdown("---")

total, avg_rating, recent = get_stats()
if total > 0:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reviews", total)
    with col2:
        st.metric("Average Rating", f"{avg_rating:.1f}⭐")
    with col3:
        st.metric("This Week", recent)

st.caption("Your feedback helps us improve our service!")
