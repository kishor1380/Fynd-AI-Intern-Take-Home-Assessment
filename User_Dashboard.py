import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import os
import json
import concurrent.futures
import time
from supabase import create_client, Client

# Page configuration
st.set_page_config(
    page_title="Customer feedback System",
    page_icon="⭐",
    layout="centered"
)

# ADD CSS TO REMOVE TOP PADDING
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Load API keys
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Use faster model
else:
    st.error("⚠️ Gemini API key not configured.")
    st.stop()

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = get_supabase()

# Session state
if 'submission_complete' not in st.session_state:
    st.session_state.submission_complete = False
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'last_rating' not in st.session_state:
    st.session_state.last_rating = None
if 'selected_rating' not in st.session_state:
    st.session_state.selected_rating = 5

# AI FUNCTIONS WITH RETRY LOGIC (FIX #3)
def generate_user_response(rating, review):
    prompt = f"""You are an empathetic customer service manager.

Rating: {rating}/5 stars
Review: "{review}"

Write a warm, personalized response (3-4 sentences) that:
1. SPECIFICALLY mentions what the customer talked about
2. Shows genuine emotion appropriate to their rating
3. If negative (1-2 stars): Apologize specifically and offer solution
4. If positive (4-5 stars): Express excitement about specific things they praised
5. If neutral (3 stars): Acknowledge mixed feelings and commit to improvement

Response (directly to customer):"""

    # TRY MULTIPLE TIMES TO GET AI RESPONSE
    for attempt in range(3):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.95,
                    'max_output_tokens': 500,
                }
            )
            if response.text and len(response.text.strip()) > 10:
                return response.text.strip()
        except Exception as e:
            if attempt == 2:  # Last attempt
                st.warning(f"AI generation attempt {attempt+1} failed: {e}")
            time.sleep(1)  # Wait before retry

    # Only use fallback if ALL attempts fail
    return f"Thank you for your {rating}-star review! We truly appreciate you taking the time to share your experience with us. Your feedback helps us improve our service."

def generate_summary(rating, review):
    prompt = f"""Create a detailed admin summary (15-25 words) capturing KEY SPECIFIC POINTS.

Rating: {rating}/5
Review: "{review}"

Summary (15-25 words):"""

    for attempt in range(3):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.5,
                    'max_output_tokens': 100,
                }
            )
            if response.text and len(response.text.strip()) > 10:
                return response.text.strip()
        except:
            time.sleep(1)

    return f"{rating}-star review: {review[:50]}..."

def generate_actions(rating, review):
    prompt = f"""Generate 3-4 CONCRETE, SPECIFIC action items.

Rating: {rating}/5
Review: "{review}"

Requirements:
1. Reference SPECIFIC issues or praises
2. Give actionable steps
3. Use action verbs

Format as bullet points (use •).

Actions:"""

    for attempt in range(3):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.6,
                    'max_output_tokens': 300,
                }
            )
            if response.text and len(response.text.strip()) > 10:
                return response.text.strip()
        except:
            time.sleep(1)

    if rating <= 2:
        return "• Contact customer for service recovery\n• Investigate reported issues\n• Implement corrective measures"
    elif rating >= 4:
        return "• Thank customer for positive feedback\n• Share testimonial (with permission)\n• Continue excellent service"
    else:
        return "• Acknowledge feedback\n• Identify improvement areas\n• Monitor similar issues"

def generate_all_ai_content_parallel(rating, review):
    results = {}

    def call_user_response():
        results['user_response'] = generate_user_response(rating, review)

    def call_summary():
        results['summary'] = generate_summary(rating, review)

    def call_actions():
        results['actions'] = generate_actions(rating, review)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_user = executor.submit(call_user_response)
        future_summary = executor.submit(call_summary)
        future_actions = executor.submit(call_actions)

        concurrent.futures.wait([future_user, future_summary, future_actions])

    return results['user_response'], results['summary'], results['actions']

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

# Main UI
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
            st.error("⚠️ Please write a review before submitting.")
        elif len(review.strip()) < 10:
            st.error("⚠️ Please provide more detailed feedback (at least 10 characters).")
        else:
            with st.spinner("🤖 Processing your feedback... (this may take a few seconds)"):
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
                    st.info("💡 Please check your API key and try again.")

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

st.caption("Your feedback helps us improve our service. Thank you for taking the time to share!")
