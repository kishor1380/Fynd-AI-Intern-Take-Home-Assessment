import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import os
import concurrent.futures
import time

st.set_page_config(page_title="User Feedback", page_icon="👤", layout="centered")

# Load API key
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    st.error("⚠️ Gemini API key not configured.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

DATA_FILE = "feedback_data.csv"

# Session state
if 'submission_complete' not in st.session_state:
    st.session_state.submission_complete = False
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'last_rating' not in st.session_state:
    st.session_state.last_rating = None
if 'selected_rating' not in st.session_state:
    st.session_state.selected_rating = 5

def init_data_file():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            'timestamp', 'rating', 'review', 'ai_response', 
            'ai_summary', 'recommended_actions'
        ])
        df.to_csv(DATA_FILE, index=False)

def generate_user_response(rating, review):
    prompt = f"""You are an empathetic customer service manager.

Rating: {rating}/5
Review: "{review}"

Write a warm, personalized response (3-4 sentences) that specifically mentions what the customer talked about.

Response:"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return f"Thank you for your {rating}-star review! We appreciate your feedback."

def generate_summary(rating, review):
    prompt = f"""Create a 15-25 word admin summary.

Rating: {rating}/5
Review: "{review}"

Summary:"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return f"{rating}-star: {review[:50]}..."

def generate_actions(rating, review):
    prompt = f"""Generate 3-4 specific action items.

Rating: {rating}/5
Review: "{review}"

Format as bullet points (use •).

Actions:"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "• Follow up\n• Review feedback\n• Implement improvements"

def generate_all_ai_content_parallel(rating, review):
    results = {}

    def call_user_response():
        results['user_response'] = generate_user_response(rating, review)
    def call_summary():
        results['summary'] = generate_summary(rating, review)
    def call_actions():
        results['actions'] = generate_actions(rating, review)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(call_user_response),
            executor.submit(call_summary),
            executor.submit(call_actions)
        ]
        concurrent.futures.wait(futures)

    return results['user_response'], results['summary'], results['actions']

def save_feedback(rating, review, ai_response, ai_summary, recommended_actions):
    init_data_file()
    new_data = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'rating': rating,
        'review': review,
        'ai_response': ai_response,
        'ai_summary': ai_summary,
        'recommended_actions': recommended_actions
    }
    df = pd.read_csv(DATA_FILE)
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

def reset_form():
    st.session_state.submission_complete = False
    st.session_state.last_response = None
    st.session_state.last_rating = None
    st.session_state.selected_rating = 5
    st.rerun()

# Main UI
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
            st.error("⚠️ Please write a review before submitting.")
        elif len(review.strip()) < 10:
            st.error("⚠️ Please provide more detailed feedback (at least 10 characters).")
        else:
            with st.spinner("🤖 Processing your feedback..."):
                try:
                    ai_response, ai_summary, recommended_actions = generate_all_ai_content_parallel(
                        st.session_state.selected_rating, review
                    )

                    save_feedback(st.session_state.selected_rating, review, ai_response, ai_summary, recommended_actions)

                    st.session_state.submission_complete = True
                    st.session_state.last_response = ai_response
                    st.session_state.last_rating = st.session_state.selected_rating
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

st.markdown("---")
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    if len(df) > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Reviews", len(df))
        with col2:
            avg_rating = df['rating'].mean()
            st.metric("Average Rating", f"{avg_rating:.1f}⭐")
        with col3:
            recent = len(df[df['timestamp'] >= (datetime.now() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")])
            st.metric("This Week", recent)

st.caption("Your feedback helps us improve our service. Thank you!")
