import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from supabase import create_client, Client

# Page configuration
st.set_page_config(
    page_title="Admin Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

# Enhanced Custom CSS - EXACT SAME AS YOUR ORIGINAL
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

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        box-shadow: 2px 0 10px rgba(0,0,0,0.1);
    }

    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        padding-top: 2rem;
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

    .feedback-item {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #ddd;
        transition: all 0.2s ease;
    }

    .feedback-item:hover {
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        transform: translateX(5px);
    }

    .feedback-item.high-priority {
        border-left-color: #ef4444;
        background: linear-gradient(135deg, #ffffff 0%, #fef2f2 100%);
    }

    .feedback-item.medium-priority {
        border-left-color: #f59e0b;
        background: linear-gradient(135deg, #ffffff 0%, #fffbeb 100%);
    }

    .feedback-item.low-priority {
        border-left-color: #10b981;
        background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
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

    .element-container {
        margin-bottom: 0.5rem;
    }

    h1, h2, h3 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
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

    section[data-testid="stSidebar"] .stDownloadButton > button {
        background: rgba(255, 255, 255, 0.2);
        color: white;
        border: 2px solid white;
        font-weight: 600;
    }

    section[data-testid="stSidebar"] .stDownloadButton > button:hover {
        background: white;
        color: #667eea;
    }

    .stPlotlyChart {
        margin-bottom: 0 !important;
    }

    .info-box {
        background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }

    .warning-box {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #f59e0b;
        margin: 0.5rem 0;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        background: white;
        border-radius: 10px 10px 0 0;
        font-weight: 600;
        color: #667eea;
        border: 2px solid #e0e0e0;
        border-bottom: none;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-color: #667eea;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stMultiSelect [data-baseweb="tag"] {
        margin: 2px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Supabase connection (ONLY NEW CODE!)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Supabase credentials not found in secrets")
    st.stop()

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = get_supabase()

# Initialize session state
if 'date_filter' not in st.session_state:
    st.session_state.date_filter = "All Time"
if 'confirm_clear' not in st.session_state:
    st.session_state.confirm_clear = False

# Load data from Supabase (CHANGED FROM CSV!)
def load_data():
    try:
        response = supabase.table('feedback').select('*').order('timestamp', desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
    except Exception as e:
        st.error(f"Database error: {e}")
    return pd.DataFrame(columns=[
        'timestamp', 'rating', 'review', 'ai_response', 
        'ai_summary', 'recommended_actions'
    ])

def get_sentiment(rating):
    if rating >= 4:
        return "Positive"
    elif rating == 3:
        return "Neutral"
    else:
        return "Negative"

def get_priority(rating):
    if rating <= 2:
        return "High"
    elif rating == 3:
        return "Medium"
    else:
        return "Low"

# Clear data from Supabase (CHANGED FROM CSV!)
def clear_all_data():
    """Clear all submissions from the database"""
    try:
        supabase.table('feedback').delete().neq('id', 0).execute()
    except:
        pass
    st.session_state.confirm_clear = False

# Header - EXACT SAME
st.markdown("""
<div class="admin-header">
    <h1 class="admin-title">📊 Admin Analytics Dashboard</h1>
    <p class="admin-subtitle">🔄 Live auto-refresh enabled • Real-time customer feedback insights • Updates every 5 seconds</p>
</div>
""", unsafe_allow_html=True)

# Load data
df = load_data()

# Sidebar - EXACT SAME
with st.sidebar:
    st.markdown("<h2 style='color: white; margin-bottom: 1.5rem;'>⚙️ Controls</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1.5rem 0;'>", unsafe_allow_html=True)

    if len(df) > 0:
        df['sentiment'] = df['rating'].apply(get_sentiment)
        df['priority'] = df['rating'].apply(get_priority)
        df['date'] = df['timestamp'].dt.date

        # Date filter
        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>📅 Date Range</h3>", unsafe_allow_html=True)
        date_filter_option = st.radio(
            "period",
            ["All Time", "Last 7 Days", "Last 30 Days", "Custom"],
            index=["All Time", "Last 7 Days", "Last 30 Days", "Custom"].index(st.session_state.date_filter) if st.session_state.date_filter in ["All Time", "Last 7 Days", "Last 30 Days", "Custom"] else 0,
            label_visibility="collapsed",
            key="date_radio"
        )
        st.session_state.date_filter = date_filter_option

        if date_filter_option == "Custom":
            date_range = st.date_input(
                "range",
                value=(df['date'].min(), df['date'].max()),
                min_value=df['date'].min(),
                max_value=df['date'].max(),
                label_visibility="collapsed"
            )
        elif date_filter_option == "Last 7 Days":
            date_range = ((datetime.now() - timedelta(days=7)).date(), datetime.now().date())
        elif date_filter_option == "Last 30 Days":
            date_range = ((datetime.now() - timedelta(days=30)).date(), datetime.now().date())
        else:
            date_range = (df['date'].min(), df['date'].max())

        st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1rem 0;'>", unsafe_allow_html=True)

        # Rating filter
        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>⭐ Ratings</h3>", unsafe_allow_html=True)
        rating_filter = st.multiselect(
            "ratings",
            options=[1, 2, 3, 4, 5],
            default=[1, 2, 3, 4, 5],
            format_func=lambda x: "⭐" * x + f" ({x})",
            label_visibility="collapsed",
            key="rating_filter"
        )

        st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1rem 0;'>", unsafe_allow_html=True)

        # Sentiment filter
        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>😊 Sentiment</h3>", unsafe_allow_html=True)
        sentiment_filter = st.multiselect(
            "sentiment",
            options=["Positive", "Neutral", "Negative"],
            default=["Positive", "Neutral", "Negative"],
            format_func=lambda x: f"{'😊' if x=='Positive' else '😐' if x=='Neutral' else '😞'} {x}",
            label_visibility="collapsed",
            key="sentiment_filter"
        )

        st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1rem 0;'>", unsafe_allow_html=True)

        # Priority filter
        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>🎯 Priority</h3>", unsafe_allow_html=True)
        priority_filter = st.multiselect(
            "priority",
            options=["High", "Medium", "Low"],
            default=["High", "Medium", "Low"],
            format_func=lambda x: f"{'🔴' if x=='High' else '🟡' if x=='Medium' else '🟢'} {x}",
            label_visibility="collapsed",
            key="priority_filter"
        )

        st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1.5rem 0;'>", unsafe_allow_html=True)

        # Quick stats
        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>📊 Quick Stats</h3>", unsafe_allow_html=True)
        high_priority = (df['priority'] == 'High').sum()
        medium_priority = (df['priority'] == 'Medium').sum()
        low_priority = (df['priority'] == 'Low').sum()

        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-top: 0.5rem;'>
            <p style='margin: 0.3rem 0; color: white;'>🔴 High: <strong>{high_priority}</strong></p>
            <p style='margin: 0.3rem 0; color: white;'>🟡 Medium: <strong>{medium_priority}</strong></p>
            <p style='margin: 0.3rem 0; color: white;'>🟢 Low: <strong>{low_priority}</strong></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1.5rem 0;'>", unsafe_allow_html=True)

        # Export section
        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>📥 Export Data</h3>", unsafe_allow_html=True)
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1.5rem 0;'>", unsafe_allow_html=True)

        # Clear all data section
        st.markdown("<h3 style='color: white; font-size: 1.1rem;'>🗑️ Danger Zone</h3>", unsafe_allow_html=True)

        if not st.session_state.confirm_clear:
            st.markdown("<p style='color: rgba(255,255,255,0.8); font-size: 0.85rem; margin-bottom: 0.5rem;'>Delete all submissions permanently</p>", unsafe_allow_html=True)
            if st.button("🗑️ Clear All Submissions", use_container_width=True, key="clear_btn"):
                st.session_state.confirm_clear = True
                st.rerun()
        else:
            st.warning("⚠️ Are you sure? This cannot be undone!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Delete", use_container_width=True, key="confirm_yes"):
                    clear_all_data()
                    st.success("✅ All data cleared!")
                    time.sleep(1)
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", use_container_width=True, key="confirm_no"):
                    st.session_state.confirm_clear = False
                    st.rerun()

# Handle empty state
if len(df) == 0:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">📭</div>
        <h2 style="color: #667eea;">No Feedback Yet</h2>
        <p style="color: #666; font-size: 1.05rem; margin: 1rem 0;">
            Waiting for customers to submit their first review.<br>
            Share the feedback form to start collecting insights!
        </p>
        <p style="color: #999; font-size: 0.9rem;">🔄 Auto-refreshing every 5 seconds...</p>
    </div>
    """, unsafe_allow_html=True)

    time.sleep(5)
    st.rerun()

# Apply filters
try:
    active_rating_filter = st.session_state.get('rating_filter', [1, 2, 3, 4, 5])
    active_sentiment_filter = st.session_state.get('sentiment_filter', ["Positive", "Neutral", "Negative"])
    active_priority_filter = st.session_state.get('priority_filter', ["High", "Medium", "Low"])

    if not active_rating_filter:
        active_rating_filter = [1, 2, 3, 4, 5]
    if not active_sentiment_filter:
        active_sentiment_filter = ["Positive", "Neutral", "Negative"]
    if not active_priority_filter:
        active_priority_filter = ["High", "Medium", "Low"]

    if len(date_range) == 2:
        df_filtered = df[
            (df['date'] >= date_range[0]) & 
            (df['date'] <= date_range[1])
        ]
    else:
        df_filtered = df.copy()

    df_filtered = df_filtered[
        (df_filtered['rating'].isin(active_rating_filter)) &
        (df_filtered['sentiment'].isin(active_sentiment_filter)) &
        (df_filtered['priority'].isin(active_priority_filter))
    ]

    if len(df_filtered) == 0:
        st.markdown("""
        <div class="warning-box">
            <h3 style="margin: 0 0 0.5rem 0;">🔍 No Results Found</h3>
            <p style="margin: 0; color: #666;">
                No submissions match your current filters. Try broadening your search criteria or clear individual filters using the X button.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Available", len(df))
        with col2:
            st.metric("Filtered Out", len(df))

        time.sleep(5)
        st.rerun()

except Exception as e:
    st.error(f"⚠️ Error applying filters: {str(e)}")
    df_filtered = df.copy()

# Metrics - EXACT SAME
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
    today_count = (df_filtered['date'] == datetime.now().date()).sum()
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{today_count}</p>
        <p class="metric-label">Today</p>
    </div>
    """, unsafe_allow_html=True)

with col6:
    week_count = len(df_filtered[df_filtered['date'] >= (datetime.now() - timedelta(days=7)).date()])
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{week_count}</p>
        <p class="metric-label">This Week</p>
    </div>
    """, unsafe_allow_html=True)

# Charts - EXACT SAME
st.markdown("<h2 class='section-header'>📊 Analytics Overview</h2>", unsafe_allow_html=True)

chart_col1, chart_col2, chart_col3 = st.columns([1, 1, 1.2])

with chart_col1:
    rating_dist = df_filtered['rating'].value_counts().sort_index()
    fig_rating = px.bar(
        x=rating_dist.index,
        y=rating_dist.values,
        labels={'x': 'Rating', 'y': 'Count'},
        title='Rating Distribution',
        color=rating_dist.index,
        color_continuous_scale='RdYlGn',
        text=rating_dist.values
    )
    fig_rating.update_layout(
        showlegend=False, 
        height=280,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=10)
    )
    fig_rating.update_traces(textposition='outside')
    st.plotly_chart(fig_rating, use_container_width=True, config={'displayModeBar': False})

with chart_col2:
    sentiment_counts = df_filtered['sentiment'].value_counts()
    fig_sentiment = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        title='Sentiment Split',
        color=sentiment_counts.index,
        color_discrete_map={
            'Positive': '#10b981',
            'Neutral': '#f59e0b', 
            'Negative': '#ef4444'
        }
    )
    fig_sentiment.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(size=10)
    )
    fig_sentiment.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_sentiment, use_container_width=True, config={'displayModeBar': False})

with chart_col3:
    if len(df_filtered) > 1:
        daily_stats = df_filtered.groupby('date').agg({
            'rating': ['mean', 'count']
        }).reset_index()
        daily_stats.columns = ['date', 'avg_rating', 'count']

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['avg_rating'],
            mode='lines+markers',
            name='Avg Rating',
            line=dict(color='#667eea', width=2),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.2)'
        ))
        fig_trend.update_layout(
            title='Rating Trend',
            xaxis_title='',
            yaxis_title='Rating',
            yaxis_range=[0, 5],
            height=280,
            margin=dict(l=20, r=20, t=40, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=10)
        )
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

# Submissions with TABS - EXACT SAME
st.markdown("<h2 class='section-header'>📝 Submissions</h2>", unsafe_allow_html=True)

tab1, tab2 = st.tabs([
    f"🔍 Filtered Results ({len(df_filtered)})",
    f"📋 All Submissions ({len(df)})"
])

with tab1:
    if len(df_filtered) == 0:
        st.info("No submissions match the current filters.")
    else:
        df_display_filtered = df_filtered.sort_values('timestamp', ascending=False).reset_index(drop=True)

        submission_col1, submission_col2 = st.columns(2)

        for idx, row in df_display_filtered.iterrows():
            target_col = submission_col1 if idx % 2 == 0 else submission_col2

            with target_col:
                priority_emoji = "🔴" if row['priority'] == "High" else "🟡" if row['priority'] == "Medium" else "🟢"

                with st.expander(
                    f"{priority_emoji} {'⭐' * int(row['rating'])} • {row['timestamp'].strftime('%b %d, %H:%M')}",
                    expanded=False
                ):
                    st.markdown(f"**📝 Review:**")
                    st.write(row['review'])

                    st.markdown(f"**🤖 AI Summary:**")
                    st.info(row['ai_summary'])

                    st.markdown(f"**💬 Response:**")
                    st.success(row['ai_response'])

                    st.markdown(f"**✅ Actions:**")
                    st.markdown(row['recommended_actions'])

                    st.caption(f"Priority: {priority_emoji} {row['priority']} | Sentiment: {row['sentiment']}")

with tab2:
    df_display_all = df.sort_values('timestamp', ascending=False).reset_index(drop=True)

    submission_col1, submission_col2 = st.columns(2)

    for idx, row in df_display_all.iterrows():
        target_col = submission_col1 if idx % 2 == 0 else submission_col2

        with target_col:
            priority_emoji = "🔴" if row['priority'] == "High" else "🟡" if row['priority'] == "Medium" else "🟢"

            with st.expander(
                f"{priority_emoji} {'⭐' * int(row['rating'])} • {row['timestamp'].strftime('%b %d, %H:%M')}",
                expanded=False
            ):
                st.markdown(f"**📝 Review:**")
                st.write(row['review'])

                st.markdown(f"**🤖 AI Summary:**")
                st.info(row['ai_summary'])

                st.markdown(f"**💬 Response:**")
                st.success(row['ai_response'])

                st.markdown(f"**✅ Actions:**")
                st.markdown(row['recommended_actions'])

                st.caption(f"Priority: {priority_emoji} {row['priority']} | Sentiment: {row['sentiment']}")

# Footer - EXACT SAME
st.markdown("<hr style='margin: 1rem 0; border: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
current_time = datetime.now().strftime('%H:%M:%S')
st.caption(f"🕐 Updated: {current_time} | 📊 Showing {len(df_filtered)} filtered / {len(df)} total | 🔄 Live refresh: Active (every 5s)")

# AUTO-REFRESH
time.sleep(5)
st.rerun()
