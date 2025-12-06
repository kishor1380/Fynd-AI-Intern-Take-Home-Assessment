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
    page_title="Customer Feedback System",
    page_icon="⭐",
    layout="centered"
)

# CSS - COMPACT UI & FORCE UP
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
        margin-bottom: -0.5rem !important; /* Pulls elements closer together */
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

# Load secrets with better error handling
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Validate credentials
if not GEMINI_API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Missing credentials. Please check secrets.")
    st.stop()

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    model = genai.GenerativeModel('gemini-pro')

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

# --- UPDATED AI FUNCTIONS WITH DETAILED PROMPTS ---

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

    # Retry logic
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            if response and response.text: return response.text.strip()
        except: 
            time.sleep(1)
            
    return f"Thank you for your {rating}-star review! We appreciate your feedback."

def generate_summary(rating, review):
    """Generate a concise summary for admin dashboard."""
    prompt = f"""Create a detailed admin summary (20 to 25 words) that captures the KEY SPECIFIC POINTS from this customer review.

Rating: {rating}/5 stars
Review: "{review}"

Focus on WHAT SPECIFICALLY they mentioned. Be concrete, informative, and actionable.

Summary (15-25 words):"""

    # Retry logic
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            if response and response.text: return response.text.strip()
        except: 
            time.sleep(1)
            
    return f"{rating}-star review: {review[:50]}..."

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

    # Retry logic
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            if response and response.text: return response.text.strip()
        except: 
            time.sleep(1)
            
    # Fallback actions based on rating
    if rating <= 2:
        return "• Contact customer for service recovery\n• Investigate reported issues"
    return "• Thank customer for feedback\n• Monitor for similar trends"

# --- END AI FUNCTIONS ---

def generate_all_ai_content_parallel(rating, review):
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
        # Insert into Supabase 'feedback' table
        supabase.table('feedback').insert(data).execute()
        return True
    except Exception as e: 
        print(f"Supabase Error: {e}")
        return False

def get_stats():
    try:
        # Fetch data from Supabase for stats
        response = supabase.table('feedback').select('rating, timestamp').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Basic calculations
            total_reviews = len(df)
            avg_rating = df['rating'].mean() if total_reviews > 0 else 0
            
            # Recent reviews (last 7 days)
            # Ensure timestamp is datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            recent_count = len(df[df['timestamp'] >= (datetime.now() - pd.Timedelta(days=7))])
            
            return total_reviews, avg_rating, recent_count
    except: 
        pass
    return 0, 0, 0

def reset_form():
    st.session_state.submission_complete = False
    st.session_state.last_response = None
    st.session_state.selected_rating = 5
    st.rerun()

# MAIN UI START
st.title("⭐ Customer Feedback System")
st.markdown("We value your feedback! Please share your experience with us.", help=None)

# Added a spacer to separate title from content slightly without being huge
st.write("") 

if st.session_state.submission_complete:
    st.success("✅ Feedback submitted!")
    
    # Show celebration for positive reviews
    if st.session_state.last_rating >= 4:
        st.balloons()
    
    st.subheader("Our Response")
    st.info(st.session_state.last_response)
    
    if st.button("📝 Submit Another Review", use_container_width=True, type="primary"):
        reset_form()

else:
    # COMPACT HEADER
    st.markdown("### Rate Your Experience")
    
    # Stars Section
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            star_emoji = "⭐" if i < st.session_state.selected_rating else "☆"
            if st.button(star_emoji, key=f"star_{i+1}", use_container_width=True):
                st.session_state.selected_rating = i + 1
                st.rerun()

    # REDUCED MARGINS
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
        # Added margin-top to separate button from text area cleanly
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True, type="primary")

    if submitted:
        if not review.strip():
            st.error("⚠️ Please write a review.")
        elif len(review.strip()) < 10:
            st.error("⚠️ At least 10 characters please.")
        else:
            with st.spinner("🤖 Generative AI Analysis..."):
                try:
                    # Parallel generation
                    ai_response, ai_summary, recommended_actions = generate_all_ai_content_parallel(
                        st.session_state.selected_rating, review
                    )
                    
                    # Save to Supabase
                    if save_feedback(st.session_state.selected_rating, review, ai_response, ai_summary, recommended_actions):
                        st.session_state.submission_complete = True
                        st.session_state.last_response = ai_response
                        st.session_state.last_rating = st.session_state.selected_rating
                        st.rerun()
                    else:
                        st.error("❌ Failed to save to database. Please try again.")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Footer stats - Compacted
st.markdown("---")
total, avg_rating, recent = get_stats()
if total > 0:
    c1, c2, c3 = st.columns(3)
    c1.metric("Reviews", total)
    c2.metric("Avg", f"{avg_rating:.1f}⭐")
    c3.metric("Week", recent)
