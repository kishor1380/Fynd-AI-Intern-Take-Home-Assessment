import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import os
import concurrent.futures
import time
from supabase import create_client, Client

# Page configuration - MUST be first
st.set_page_config(
    page_title="Customer feedback System",
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

# Load secrets with better error handling
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    try:
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
    except:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    try:
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
    except:
        SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Validate credentials
if not GEMINI_API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Missing credentials. Please check secrets.")
    st.info(f"""
    Required secrets:
    - GEMINI_API_KEY: {'✅ Found' if GEMINI_API_KEY else '❌ Missing'}
    - SUPABASE_URL: {'✅ Found' if SUPABASE_URL else '❌ Missing'}
    - SUPABASE_KEY: {'✅ Found' if SUPABASE_KEY else '❌ Missing'}
    """)
    st.stop()

# Configure Gemini with the RIGHT model name
genai.configure(api_key=GEMINI_API_KEY)

# Try different model names (Gemini API changes names sometimes)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')  # Most stable
except:
    try:
        model = genai.GenerativeModel('gemini-pro')
    except:
        model = genai.GenerativeModel('models/gemini-pro')

# Supabase connection
@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = get_supabase()
except Exception as e:
    st.error(f"Supabase connection failed: {e}")
    st.stop()

# Session state
if 'submission_complete' not in st.session_state:
    st.session_state.submission_complete = False
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'last_rating' not in st.session_state:
    st.session_state.last_rating = None
if 'selected_rating' not in st.session_state:
    st.session_state.selected_rating = 5

# FIXED AI FUNCTIONS - GUARANTEED TO WORK
def generate_user_response(rating, review):
    """Generate AI response with multiple retries"""
    prompt = f"""You are a customer service manager. Write a warm, personal response to this review.

Rating: {rating}/5 stars
Review: {review}

Write 3-4 sentences that mention specific details from their review.

Response:"""

    for attempt in range(3):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=400,
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )

            if response and response.text and len(response.text.strip()) > 20:
                return response.text.strip()

        except Exception as e:
            st.warning(f"Attempt {attempt+1}/3 failed: {str(e)[:100]}")
            time.sleep(2)

    # Final fallback
    return f"Thank you for your {rating}-star review! We truly appreciate you taking the time to share your experience. Your feedback is invaluable and helps us improve our service."

def generate_summary(rating, review):
    """Generate admin summary"""
    prompt = f"""Summarize this review in 15-20 words for admin dashboard.

Rating: {rating}/5
Review: {review}

Summary:"""

    for attempt in range(3):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.5,
                    max_output_tokens=100,
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            if response and response.text:
                return response.text.strip()
        except:
            time.sleep(1)

    return f"{rating}⭐: {review[:40]}..."

def generate_actions(rating, review):
    """Generate action items"""
    prompt = f"""Generate 3 specific action items for this review. Use bullet points (•).

Rating: {rating}/5
Review: {review}

Actions:"""

    for attempt in range(3):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.6,
                    max_output_tokens=300,
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            if response and response.text:
                return response.text.strip()
        except:
            time.sleep(1)

    if rating <= 2:
        return "• Contact customer immediately\n• Investigate issue\n• Implement fixes"
    elif rating >= 4:
        return "• Thank customer\n• Request testimonial\n• Share internally"
    else:
        return "• Review feedback\n• Identify improvements\n• Follow up"

def generate_all_ai_content_parallel(rating, review):
    """Generate all AI content in parallel"""
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
    """Save to Supabase"""
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
    """Get statistics from Supabase"""
    try:
        response = supabase.table('feedback').select('*').execute()
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
    """Reset form state"""
    st.session_state.submission_complete = False
    st.session_state.last_response = None
    st.session_state.last_rating = None
    st.session_state.selected_rating = 5
    st.rerun()

# MAIN UI
st.title("⭐ Customer feedback System")
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
        submitted = st.form_submit_button("Submit feedback", use_container_width=True, type="primary")

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
