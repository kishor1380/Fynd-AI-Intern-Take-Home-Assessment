import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import os
import json
import concurrent.futures
import time

# Page configuration
st.set_page_config(
    page_title="Customer Feedback System",
    page_icon="⭐",
    layout="centered"
)

# Load API key from secrets or environment
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.error("⚠️ Gemini API key not configured. Please add it to secrets.")
    st.stop()

# Data file path
DATA_FILE = "feedback_data.csv"

# Initialize session state for form management
if 'submission_complete' not in st.session_state:
    st.session_state.submission_complete = False
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'last_rating' not in st.session_state:
    st.session_state.last_rating = None
if 'selected_rating' not in st.session_state:
    st.session_state.selected_rating = 5  # Default to 5 stars

# Initialize data file if it doesn't exist
def init_data_file():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            'timestamp', 'rating', 'review', 'ai_response', 
            'ai_summary', 'recommended_actions'
        ])
        df.to_csv(DATA_FILE, index=False)

# Generate AI response for user
def generate_user_response(rating, review):
    """Generate a friendly, empathetic response to the user review."""
    prompt = f"""You are an empathetic customer service manager personally responding to this customer review.

Rating: {rating}/5 stars
Review: "{review}"

Write a warm, personalized response (3-4 sentences) that:
1. SPECIFICALLY mentions what the customer talked about - use their exact words and context
2. Shows genuine emotion appropriate to their rating
3. If negative (1-2 stars): 
   - Apologize SPECIFICALLY for what went wrong (mention the exact issue they raised)
   - Offer a concrete solution or next step
4. If positive (4-5 stars): 
   - Express genuine excitement about the SPECIFIC things they praised
   - Mention those specific details back to them
5. If neutral (3 stars): 
   - Acknowledge the mixed feelings about SPECIFIC aspects they mentioned
   - Commit to improving the exact things they found lacking

CRITICAL: Be conversational, warm, and reference SPECIFIC details from their review.

Response (directly to customer, no preamble):"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Thank you for your {rating}-star review! We appreciate your feedback and will use it to improve our service."

# Generate AI summary for admin
def generate_summary(rating, review):
    """Generate a concise summary for admin dashboard."""
    prompt = f"""Create a detailed admin summary (20 to 25 words) that captures the KEY SPECIFIC POINTS from this customer review.

Rating: {rating}/5 stars
Review: "{review}"

Focus on WHAT SPECIFICALLY they mentioned. Be concrete, informative, and actionable.

Summary (15-25 words):"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"{rating}-star review: {review[:50]}..."

# Generate recommended actions for admin
def generate_actions(rating, review):
    """Generate recommended next actions based on feedback."""
    prompt = f"""You are a business consultant analyzing this customer feedback. Generate 3-4 CONCRETE, SPECIFIC action items.

Rating: {rating}/5 stars
Review: "{review}"

Requirements:
1. Reference SPECIFIC issues or praises from the review
2. Give actionable steps with WHAT to do and HOW
3. Use action verbs: Contact, Investigate, Train, Implement, etc.

Format as bullet points (use • not -).
Each action should be 1-2 lines maximum.

Recommended Actions:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        if rating <= 2:
            return "• Contact customer for service recovery\n• Investigate reported issues\n• Implement corrective measures"
        elif rating >= 4:
            return "• Thank customer for positive feedback\n• Share testimonial (with permission)\n• Continue excellent service"
        else:
            return "• Acknowledge feedback\n• Identify improvement areas\n• Monitor similar issues"

# PARALLEL API CALLS - 3X FASTER!
def generate_all_ai_content_parallel(rating, review):
    """Generate all 3 AI responses in PARALLEL using threading."""
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

# Save feedback to CSV
def save_feedback(rating, review, ai_response, ai_summary, recommended_actions):
    """Save feedback data to CSV file."""
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

# Function to reset form
def reset_form():
    """Reset the submission state to allow new review."""
    st.session_state.submission_complete = False
    st.session_state.last_response = None
    st.session_state.last_rating = None
    st.session_state.selected_rating = 5  # Reset to default
    st.rerun()

# Main UI
st.title("⭐ Customer Feedback System")
st.markdown("We value your feedback! Please share your experience with us.")

# If submission is complete, show response and "Submit Another" button
if st.session_state.submission_complete:
    st.success("✅ Thank you! Your feedback has been submitted.")

    # Display AI response
    st.markdown("---")
    st.subheader("Our Response")
    st.info(st.session_state.last_response)

    # Show celebration for positive reviews
    if st.session_state.last_rating >= 4:
        st.balloons()
        st.markdown("🎉 **We're thrilled you had a great experience!**")
    elif st.session_state.last_rating <= 2:
        st.markdown("🙏 **We're sorry to hear about your experience. We'll work to make it right.**")

    # Button to submit another review
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📝 Submit Another Review", use_container_width=True, type="primary"):
            reset_form()

else:
    # Show the rating section FIRST (before form)
    st.subheader("Rate Your Experience")

    # CLICKABLE STAR RATING - ABOVE FORM!
    st.markdown("**Click to select rating:**")

    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            star_emoji = "⭐" if i < st.session_state.selected_rating else "☆"
            if st.button(star_emoji, key=f"star_{i+1}", use_container_width=True):
                st.session_state.selected_rating = i + 1
                st.rerun()

    # Display current selection
    star_display = "⭐" * st.session_state.selected_rating + "☆" * (5 - st.session_state.selected_rating)
    st.markdown(f"<p style='text-align: center; font-size: 2rem; margin: 0.5rem 0;'>{star_display}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #666; margin-bottom: 1.5rem;'>{st.session_state.selected_rating}/5 stars selected</p>", unsafe_allow_html=True)

    st.markdown("---")

    # Show the feedback form (text area and submit button)
    with st.form("feedback_form", clear_on_submit=True):
        # Review text
        review = st.text_area(
            "Tell us more about your experience:",
            placeholder="What did you like? What could we improve?",
            height=150,
            max_chars=500
        )

        # Submit button
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True, type="primary")

    # Handle submission
    if submitted:
        if not review.strip():
            st.error("⚠️ Please write a review before submitting.")
        elif len(review.strip()) < 10:
            st.error("⚠️ Please provide more detailed feedback (at least 10 characters).")
        else:
            with st.spinner("🤖 Processing your feedback... (this may take a few seconds)"):
                start_time = time.time()

                try:
                    # PARALLEL API CALLS - 3X FASTER!
                    ai_response, ai_summary, recommended_actions = generate_all_ai_content_parallel(
                        st.session_state.selected_rating, review
                    )

                    # Save to database
                    save_feedback(st.session_state.selected_rating, review, ai_response, ai_summary, recommended_actions)

                    elapsed_time = time.time() - start_time
                    st.success(f"✅ Processed in {elapsed_time:.1f} seconds!")

                    # Store in session state
                    st.session_state.submission_complete = True
                    st.session_state.last_response = ai_response
                    st.session_state.last_rating = st.session_state.selected_rating

                    # Rerun to show the response screen
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("💡 Please check your API key and try again.")

# Footer with stats
st.markdown("---")

# Display some stats (optional - makes it more engaging)
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
            recent_reviews = len(df[df['timestamp'] >= (datetime.now() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")])
            st.metric("This Week", recent_reviews)

st.caption("Your feedback helps us improve our service. Thank you for taking the time to share!")