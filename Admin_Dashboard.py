import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import pytz  # Added for Indian Timezone
from supabase import create_client, Client

# Page configuration - KEEP SIDEBAR ALWAYS VISIBLE
st.set_page_config(
    page_title="Admin Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"  
)

# Define IST Timezone
IST = pytz.timezone('Asia/Kolkata')

# Enhanced Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }

    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    .admin-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.35);
    }

    .admin-title {
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.2;
    }

    .admin-subtitle {
        font-size: 0.95rem;
        opacity: 0.95;
        margin-top: 0.3rem;
        margin-bottom: 0;
    }

    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
        height: 100%;
    }

    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }

    .metric-label {
        color: #666;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.5rem;
        font-weight: 600;
    }

    /* SIDEBAR - FORCE VISIBLE */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
        box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        display: block !important;
        visibility: visible !important;
    }

    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        padding-top: 2rem;
    }

    /* KEEP SIDEBAR TOGGLE VISIBLE */
    button[kind="header"] {
        display: block !important;
        visibility: visible !important;
        color: #667eea !important;
        background: white !important;
        padding: 0.5rem !important;
        border-radius: 4px !important;
    }

    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {
        color: white !important;
    }

    section[data-testid="stSidebar"] .stMultiSelect label,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stCheckbox label {
        color: white !important;
        font-weight: 600;
    }

    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #2d3748;
        margin: 1rem 0 0.8rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
        display: inline-block;
    }

    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-top: 2rem;
    }

    .empty-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }

    .streamlit-expanderHeader {
        background: white;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.95rem;
    }

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.2);
        color: white;
        border: 2px solid white;
        font-weight: 600;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: white;
        color: #667eea;
        transform: translateY(-2px);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp > header {
        background: transparent;
    }
</style>
""", unsafe_allow_html=True)

# Supabase connection
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Supabase credentials not found")
    st.stop()

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# Initialize session state
if 'date_filter' not in st.session_state:
    st.session_state.date_filter = "All Time"
if 'confirm_clear' not in st.session_state:
    st.session_state.confirm_clear = False

def load_data():
    try:
        response = supabase.table('feedback').select('*').order('timestamp', desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Convert to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # 1. Convert to UTC if timezone naive
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            
            # 2. Convert to Indian Standard Time (IST)
            df['timestamp'] = df['timestamp'].dt.tz_convert(IST)
            
            return df
    except Exception as e:
        st.error(f"Database error: {e}")
    
    # Return empty if error or no data
    return pd.DataFrame(columns=[
        'timestamp', 'rating', 'review', 'ai_response', 
        'ai_summary', 'recommended_actions'
    ])

def get_sentiment(rating):
    if rating >= 4: return "Positive"
    elif rating == 3: return "Neutral"
    else: return "Negative"

def get_priority(rating):
    if rating <= 2: return "High"
    elif rating == 3: return "Medium"
    else: return "Low"

def clear_all_data():
    try:
        # Delete from DB
        supabase.table('feedback').delete().neq('id', 0).execute()
        # Reset Session State
        st.session_state.confirm_clear = False
        # Clear Streamlit cache to ensure UI knows data is gone
        st.cache_resource.clear()
        return True
    except:
        return False

# Header
st.markdown("""
<div class="admin-header">
    <h1 class="admin-title">📊 Admin Analytics Dashboard</h1>
    <p class="admin-subtitle">🔄 Live auto-refresh enabled • Real-time customer feedback insights</p>
</div>
""", unsafe_allow_html=True)

# Load Data
df = load_data()

# ---------------------------------------------------------
# SIDEBAR LOGIC
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color: white; margin-bottom: 1.5rem;'>⚙️ Controls</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1.5rem 0;'>", unsafe_allow_html=True)

    if len(df) > 0:
        df['sentiment'] = df['rating'].apply(get_sentiment)
        df['priority'] = df['rating'].apply(get_priority)
        df['date'] = df['timestamp'].dt.date

        # DATE FILTER
        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>📅 Date Range</h3>", unsafe_allow_html=True)
        date_filter_option = st.radio(
            "period",
            ["All Time", "Last 7 Days", "Last 30 Days", "Custom"],
            index=["All Time", "Last 7 Days", "Last 30 Days", "Custom"].index(st.session_state.date_filter) if st.session_state.date_filter in ["All Time", "Last 7 Days", "Last 30 Days", "Custom"] else 0,
            label_visibility="collapsed",
            key="date_radio"
        )
        st.session_state.date_filter = date_filter_option

        # Calculate current time in IST
        now_ist = datetime.now(IST)

        if date_filter_option == "Custom":
            date_range = st.date_input("range", value=(df['date'].min(), df['date'].max()))
        elif date_filter_option == "Last 7 Days":
            date_range = ((now_ist - timedelta(days=7)).date(), now_ist.date())
        elif date_filter_option == "Last 30 Days":
            date_range = ((now_ist - timedelta(days=30)).date(), now_ist.date())
        else:
            date_range = (df['date'].min(), df['date'].max())

        st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1rem 0;'>", unsafe_allow_html=True)

        # OTHER FILTERS
        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>⭐ Ratings</h3>", unsafe_allow_html=True)
        rating_filter = st.multiselect("ratings", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5], key="rating_filter")

        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>😊 Sentiment</h3>", unsafe_allow_html=True)
        sentiment_filter = st.multiselect("sentiment", ["Positive", "Neutral", "Negative"], default=["Positive", "Neutral", "Negative"], key="sentiment_filter")

        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>🎯 Priority</h3>", unsafe_allow_html=True)
        priority_filter = st.multiselect("priority", ["High", "Medium", "Low"], default=["High", "Medium", "Low"], key="priority_filter")

        st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1.5rem 0;'>", unsafe_allow_html=True)

        # EXPORT
        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>📥 Export Data</h3>", unsafe_allow_html=True)
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"feedback_{now_ist.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1.5rem 0;'>", unsafe_allow_html=True)

        # DANGER ZONE
        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>🗑️ Danger Zone</h3>", unsafe_allow_html=True)

        if not st.session_state.confirm_clear:
            if st.button("🗑️ Clear All Submissions", use_container_width=True, key="clear_btn"):
                st.session_state.confirm_clear = True
                st.rerun()
        else:
            st.warning("⚠️ Are you sure?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes", use_container_width=True, key="confirm_yes"):
                    clear_all_data()
                    # RERUN IMMEDIATELY TO SCROLL UP AND SHOW EMPTY STATE
                    st.rerun()
            with col2:
                if st.button("❌ No", use_container_width=True, key="confirm_no"):
                    st.session_state.confirm_clear = False
                    st.rerun()

# ---------------------------------------------------------
# EMPTY STATE (Shows immediately if df is empty)
# ---------------------------------------------------------
if len(df) == 0:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">📭</div>
        <h2 style="color: #667eea;">No Feedback Yet</h2>
        <p style="color: #666; font-size: 1.05rem;">
            Waiting for submissions...<br>
            🔄 Auto-refreshing every 5 seconds
        </p>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(5)
    st.rerun()

# ---------------------------------------------------------
# DASHBOARD CONTENT (Only runs if data exists)
# ---------------------------------------------------------

# Apply filters
try:
    active_rating = st.session_state.get('rating_filter', [1, 2, 3, 4, 5]) or [1,2,3,4,5]
    active_sentiment = st.session_state.get('sentiment_filter', ["Positive", "Neutral", "Negative"]) or ["Positive", "Neutral", "Negative"]
    active_priority = st.session_state.get('priority_filter', ["High", "Medium", "Low"]) or ["High", "Medium", "Low"]

    if len(date_range) == 2:
        df_filtered = df[(df['date'] >= date_range[0]) & (df['date'] <= date_range[1])]
    else:
        df_filtered = df.copy()

    df_filtered = df_filtered[
        (df_filtered['rating'].isin(active_rating)) &
        (df_filtered['sentiment'].isin(active_sentiment)) &
        (df_filtered['priority'].isin(active_priority))
    ]

    if len(df_filtered) == 0:
        st.warning("🔍 No results match your filters.")
        time.sleep(5)
        st.rerun()

except Exception as e:
    df_filtered = df.copy()

# Metrics
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{len(df_filtered)}</p>
        <p class="metric-label">Filtered</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    avg_rating = df_filtered['rating'].mean()
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{avg_rating:.2f}</p>
        <p class="metric-label">Avg Rating</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    positive_pct = (df_filtered['sentiment'] == 'Positive').sum() / len(df_filtered) * 100
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{positive_pct:.0f}%</p>
        <p class="metric-label">Positive</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    negative_count = (df_filtered['sentiment'] == 'Negative').sum()
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{negative_count}</p>
        <p class="metric-label">Urgent</p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    now_ist_date = datetime.now(IST).date()
    today_count = (df_filtered['date'] == now_ist_date).sum()
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{today_count}</p>
        <p class="metric-label">Today</p>
    </div>
    """, unsafe_allow_html=True)

with col6:
    week_start = (datetime.now(IST) - timedelta(days=7)).date()
    week_count = len(df_filtered[df_filtered['date'] >= week_start])
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{week_count}</p>
        <p class="metric-label">This Week</p>
    </div>
    """, unsafe_allow_html=True)

# Charts
st.markdown("<h2 class='section-header'>📊 Analytics</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1.2])

with col1:
    rating_dist = df_filtered['rating'].value_counts().sort_index()
    fig = px.bar(x=rating_dist.index, y=rating_dist.values,
                 labels={'x': 'Rating', 'y': 'Count'},
                 title='Rating Distribution', text=rating_dist.values,
                 color=rating_dist.index, color_continuous_scale='RdYlGn')
    fig.update_layout(showlegend=False, height=280)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with col2:
    sentiment_counts = df_filtered['sentiment'].value_counts()
    fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index,
                 title='Sentiment',
                 color_discrete_map={'Positive':'#10b981','Neutral':'#f59e0b','Negative':'#ef4444'})
    fig.update_layout(height=280)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with col3:
    if len(df_filtered) > 1:
        daily_stats = df_filtered.groupby('date').agg({'rating': ['mean', 'count']}).reset_index()
        daily_stats.columns = ['date', 'avg_rating', 'count']

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_stats['date'], y=daily_stats['avg_rating'],
            mode='lines+markers', name='Avg Rating',
            line=dict(color='#667eea', width=2), marker=dict(size=8),
            fill='tozeroy', fillcolor='rgba(102, 126, 234, 0.2)'
        ))
        fig.update_layout(title='Rating Trend', yaxis_range=[0, 5], height=280)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# Submissions
st.markdown("<h2 class='section-header'>📝 Submissions</h2>", unsafe_allow_html=True)

tab1, tab2 = st.tabs([f"🔍 Filtered ({len(df_filtered)})", f"📋 All ({len(df)})"])

# Helper function for display
def display_reviews(dataframe):
    dataframe = dataframe.sort_values('timestamp', ascending=False)
    col1, col2 = st.columns(2)
    for idx, row in dataframe.iterrows():
        target_col = col1 if idx % 2 == 0 else col2
        with target_col:
            priority_emoji = "🔴" if row['priority'] == "High" else "🟡" if row['priority'] == "Medium" else "🟢"
            # Formatted IST Time
            time_str = row['timestamp'].strftime('%b %d, %H:%M')
            
            with st.expander(f"{priority_emoji} {'⭐' * int(row['rating'])} • {time_str}", expanded=False):
                st.markdown(f"**📝 Review:** {row['review']}")
                st.info(f"**🤖 Summary:** {row['ai_summary']}")
                st.success(f"**💬 Response:** {row['ai_response']}")
                st.markdown(f"**✅ Actions:**\n{row['recommended_actions']}")

with tab1:
    display_reviews(df_filtered)

with tab2:
    display_reviews(df)

st.markdown("<hr>", unsafe_allow_html=True)
now_str = datetime.now(IST).strftime('%H:%M:%S')
st.caption(f"🕐 {now_str} IST | 📊 {len(df_filtered)}/{len(df)} | 🔄 Auto-refresh: 5s")

time.sleep(5)
st.rerun()
