import streamlit as st  # ← FIXED TYPO
import pandas as pd
from openai import OpenAI
from datetime import datetime
import os
import time
from supabase import create_client, Client
import requests
import json

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
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem;
        max-width: 800px;
    }
    header {visibility: hidden !important;}
    footer {visibility: hidden;}
    h1 {
        margin-top: -20px !important;
        padding-top: 0px !important;
        margin-bottom: 0px !important;
    }
    .stElementContainer {
        margin-bottom: -0.5rem !important; 
    }
    div[data-testid="column"] {
        padding: 0px !important;
    }
    .stButton button {
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. SETUP CREDENTIALS
# ---------------------------------------------------------
try:
    OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not OPENROUTER_API_KEY or not SUPABASE_URL:
    st.error("⚠️ Missing API Keys. Check .streamlit/secrets.toml")
    st.stop()

# VALID FREE MODEL ON OPENROUTER
MODEL_NAME = "google/gemma-2-9b-it:free" 

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
# 5. AI FUNCTIONS - OPENROUTER VIA REQUESTS
# ---------------------------------------------------------
def call_openrouter(messages, max_tokens=500, temperature=0.9):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-app-url.streamlit.app/", 
        "X-Title": "Customer Feedback System"
    }

    body = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(body))

        if response.status_code != 200:
            st.error(f"OpenRouter Error {response.status_code}: {response.text}")
            return None

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        st.error(f"Request Failed: {e}")
        return None

def generate_user_response(rating, review):
    messages = [
        {"role": "user", "content": f"""You are an empathetic customer service manager.
Write a natural, human-sounding reply (3–4 sentences) to this review.
Rating: {rating}/5 stars
Review: "{review}"
If negative, apologize and offer help. If positive, thank them warmly."""}
    ]
    
    # Retry logic
    for _ in range(3):
        result = call_openrouter(messages, max_tokens=500, temperature=0.9)
        if result: return result
        time.sleep(1)
    
    # Fallback
    return "Thank you for your feedback! We appreciate you taking the time to share your thoughts."

def generate_summary(rating, review):
    messages = [
        {"role": "user", "content": f"""Summarize this review in 15 words:
Rating: {rating}/5
Review: "{review}" """}
    ]
    for _ in range(3):
        result = call_openrouter(messages, max_tokens=100, temperature=0.7)
        if result: return result
        time.sleep(1)
    return f"{rating}⭐ review: {review[:50]}..."

def generate_actions(rating, review):
    messages = [
        {"role": "user", "content": f"""Generate 3 short bullet points for recommended actions based on this review:
Rating: {rating}/5
Review: "{review}" """}
    ]
    for _ in range(3):
        result = call_openrouter(messages, max_tokens=300, temperature=0.8)
        if result: return result
        time.sleep(1)
    return "• Review feedback internally\n• Contact customer if needed"

# ---------------------------------------------------------
# 6. DATABASE & UI LOGIC (UNCHANGED)
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
            return len(df), df['rating'].mean(), len(df[df['timestamp'] >= (datetime.now() - pd.Timedelta(days=7))])
    except:
        pass
    return 0, 0, 0

def reset_form():
    st.session_state.submission_complete = False
    st.rerun()

# ---------------------------------------------------------
# 7. MAIN UI
# ---------------------------------------------------------
st.title("⭐ Customer Feedback System")

if st.session_state.submission_complete:
    st.success("✅ Feedback submitted!")
    if st.session_state.last_rating >= 4: st.balloons()
    st.info(st.session_state.last_response)
    if st.button("Submit Another"): reset_form()
else:
    cols = st.columns(5)
    for i in range(5):
        if cols[i].button("⭐" if i < st.session_state.selected_rating else "☆", key=f"s{i}"):
            st.session_state.selected_rating = i + 1
            st.rerun()
            
    with st.form("f"):
        review = st.text_area("Review", height=100)
        if st.form_submit_button("Submit"):
            if len(review) < 5:
                st.error("Please write more.")
            else:
                with st.spinner("Processing..."):
                    resp = generate_user_response(st.session_state.selected_rating, review)
                    summ = generate_summary(st.session_state.selected_rating, review)
                    act = generate_actions(st.session_state.selected_rating, review)
                    
                    if save_feedback(st.session_state.selected_rating, review, resp, summ, act):
                        st.session_state.submission_complete = True
                        st.session_state.last_response = resp
                        st.session_state.last_rating = st.session_state.selected_rating
                        st.rerun()
