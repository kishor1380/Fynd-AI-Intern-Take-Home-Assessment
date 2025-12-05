import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import time

st.set_page_config(page_title="Admin Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .admin-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.35);
    }
    .metric-card {
        background: white;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = "feedback_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if len(df) > 0:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
    return pd.DataFrame(columns=['timestamp', 'rating', 'review', 'ai_response', 'ai_summary', 'recommended_actions'])

def get_sentiment(rating):
    return "Positive" if rating >= 4 else "Neutral" if rating == 3 else "Negative"

def get_priority(rating):
    return "High" if rating <= 2 else "Medium" if rating == 3 else "Low"

def clear_all_data():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

# Header
st.markdown("""
<div class="admin-header">
    <h1 style="margin:0;">📊 Admin Analytics Dashboard</h1>
    <p style="margin:0.5rem 0 0 0;">🔄 Live auto-refresh • Updates every 5 seconds</p>
</div>
""", unsafe_allow_html=True)

df = load_data()

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Controls")

    if len(df) > 0:
        st.markdown("#### 📥 Export")
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "⬇️ Download CSV",
            data=csv,
            file_name=f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("#### 🗑️ Danger Zone")
        if st.button("Clear All Data", use_container_width=True):
            if st.button("⚠️ Confirm?", use_container_width=True):
                clear_all_data()
                st.success("Cleared!")
                time.sleep(1)
                st.rerun()

if len(df) == 0:
    st.markdown("""
    <div style="text-align:center; padding:3rem; background:white; border-radius:15px;">
        <div style="font-size:4rem;">📭</div>
        <h2 style="color:#667eea;">No Feedback Yet</h2>
        <p style="color:#666;">Waiting for customer submissions...</p>
        <p style="color:#999;">🔄 Auto-refreshing every 5 seconds</p>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(5)
    st.rerun()

# Add sentiment and priority
df['sentiment'] = df['rating'].apply(get_sentiment)
df['priority'] = df['rating'].apply(get_priority)

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{len(df)}</p>
        <p style="color:#666; font-size:0.8rem;">TOTAL REVIEWS</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    avg_rating = df['rating'].mean()
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{avg_rating:.2f}</p>
        <p style="color:#666; font-size:0.8rem;">AVG RATING</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    positive = (df['rating'] >= 4).sum()
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{positive}</p>
        <p style="color:#666; font-size:0.8rem;">POSITIVE</p>
    </div>
    """, unsafe_allow_html=True)
with col4:
    negative = (df['rating'] <= 2).sum()
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{negative}</p>
        <p style="color:#666; font-size:0.8rem;">URGENT</p>
    </div>
    """, unsafe_allow_html=True)

# Charts
st.markdown("### 📊 Analytics Overview")
col1, col2 = st.columns(2)

with col1:
    rating_dist = df['rating'].value_counts().sort_index()
    fig = px.bar(x=rating_dist.index, y=rating_dist.values,
                 labels={'x': 'Rating', 'y': 'Count'},
                 title='Rating Distribution', text=rating_dist.values)
    fig.update_traces(textposition='outside')
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    sentiment_counts = df['sentiment'].value_counts()
    fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index,
                 title='Sentiment Split',
                 color_discrete_map={'Positive':'#10b981','Neutral':'#f59e0b','Negative':'#ef4444'})
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

# Reviews
st.markdown("### 📝 Recent Submissions")
df_sorted = df.sort_values('timestamp', ascending=False).head(20)

col1, col2 = st.columns(2)
for idx, row in df_sorted.iterrows():
    target_col = col1 if idx % 2 == 0 else col2
    with target_col:
        priority_emoji = "🔴" if row['rating'] <= 2 else "🟡" if row['rating'] == 3 else "🟢"
        with st.expander(f"{priority_emoji} {'⭐' * int(row['rating'])} • {row['timestamp'].strftime('%b %d, %H:%M')}", expanded=False):
            st.markdown(f"**📝 Review:** {row['review']}")
            st.info(f"**🤖 Summary:** {row['ai_summary']}")
            st.success(f"**💬 Response:** {row['ai_response']}")
            st.markdown(f"**✅ Actions:**\n{row['recommended_actions']}")

st.markdown("---")
st.caption(f"🕐 Updated: {datetime.now().strftime('%H:%M:%S')} | 📊 Total: {len(df)} reviews | 🔄 Auto-refresh: Active")

# Auto-refresh
time.sleep(5)
st.rerun()
