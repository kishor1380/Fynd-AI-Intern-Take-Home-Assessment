# Fynd AI Intern Assessment - Task 2: Two-Dashboard AI Feedback System

## 🎯 Overview
A web-based feedback system with two dashboards:
1. **User Dashboard** - Public-facing feedback submission
2. **Admin Dashboard** - Internal analytics and monitoring

Both dashboards share a common CSV database and use Gemini AI for intelligent responses, summaries, and action recommendations.

## 🏗️ Architecture

```
┌─────────────────────┐
│  User Dashboard     │ ──> Submit feedback
│  (app_user.py)      │ <── Get AI response
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ feedback.csv │ (Shared Data)
    └──────────────┘
           ▲
           │
┌──────────┴──────────┐
│  Admin Dashboard    │ ──> View all submissions
│  (app_admin.py)     │ <── AI summaries & actions
└─────────────────────┘
```

## ✨ Features

### User Dashboard
- ⭐ Interactive star rating selector (1-5)
- 📝 Text area for detailed reviews
- 🤖 AI-generated personalized response
- ✅ Real-time submission confirmation
- 📊 Live stats display (total reviews, average rating)

### Admin Dashboard
- 📈 Real-time metrics overview
- 📊 Interactive charts (rating distribution, sentiment breakdown, trends)
- 🔍 Advanced filtering (date range, rating, sentiment)
- 🎯 Priority-based alerts (high/medium/low)
- 💡 AI-generated summaries and recommended actions
- 📥 CSV export functionality
- 🔄 Auto-refresh option for live monitoring

### AI Features (Powered by Gemini)
- **User Response**: Empathetic, personalized responses to customers
- **Summary**: Concise one-line summaries for quick admin review
- **Recommended Actions**: Specific, actionable next steps based on feedback

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Gemini API Key (free from https://makersuite.google.com/app/apikey)

### Local Development

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure API Key**
Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your_actual_api_key_here"
```

3. **Run User Dashboard**
```bash
streamlit run app_user.py
```
Opens at: http://localhost:8501

4. **Run Admin Dashboard** (in a new terminal)
```bash
streamlit run app_admin.py --server.port 8502
```
Opens at: http://localhost:8502

## 🌐 Deployment to Streamlit Cloud

### Step 1: Create GitHub Repository
```bash
git init
git add .
git commit -m "Initial commit: Task 2 - Feedback System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fynd-feedback-system.git
git push -u origin main
```

### Step 2: Deploy User Dashboard

1. Go to https://share.streamlit.io/
2. Click "New app"
3. Select your repository
4. Set **Main file path**: `app_user.py`
5. Click "Advanced settings"
6. Add secrets:
   ```toml
   GEMINI_API_KEY = "your_api_key_here"
   ```
7. Click "Deploy"
8. Save the URL (e.g., https://your-app-user.streamlit.app)

### Step 3: Deploy Admin Dashboard

1. Click "New app" again
2. Select same repository
3. Set **Main file path**: `app_admin.py`
4. Add same secrets
5. Click "Deploy"
6. Save the URL (e.g., https://your-app-admin.streamlit.app)

### Step 4: Shared Data Storage

**Important**: For production with Streamlit Cloud, both apps share the same repository, so they automatically share the `feedback_data.csv` file.

**Note**: For better production use, consider:
- Google Sheets (via `gspread`)
- Supabase (free PostgreSQL)
- MongoDB Atlas (free tier)

## 📁 File Structure

```
task2/
├── app_user.py                    # User dashboard
├── app_admin.py                   # Admin dashboard
├── requirements.txt               # Python dependencies
├── .streamlit/
│   ├── config.toml               # Streamlit configuration
│   └── secrets.toml.template     # Template for API keys
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
└── feedback_data.csv             # Generated: shared database
```

## 🎨 User Dashboard Features

### Rating Submission
- Star slider with visual feedback (⭐⭐⭐⭐⭐)
- Character limit (500) to keep reviews focused
- Validation for minimum review length

### AI Response
- Personalized based on rating and content
- Empathetic tone adjustment:
  - 5⭐: Enthusiastic gratitude
  - 4⭐: Warm appreciation
  - 3⭐: Constructive acknowledgment
  - 1-2⭐: Apologetic and solution-focused

### Engagement
- Balloons animation for positive reviews
- Clear success/error messages
- Live stats to show community engagement

## 📊 Admin Dashboard Features

### Metrics Overview
- Total submissions
- Average rating
- Positive percentage
- Negative review count (with alerts)
- Today's submissions

### Analytics Charts
1. **Rating Distribution**: Bar chart showing frequency of each rating
2. **Sentiment Breakdown**: Pie chart (Positive/Neutral/Negative)
3. **Trend Analysis**: Line graph of average ratings over time

### Priority System
- 🔴 High Priority: 1-2 stars (immediate attention needed)
- 🟡 Medium Priority: 3 stars (improvement opportunity)
- 🟢 Low Priority: 4-5 stars (maintenance & appreciation)

### Filtering & Search
- Date range selector
- Multi-select rating filter
- Sentiment filter
- Real-time data refresh

### Export Options
- Download filtered data as CSV
- Timestamped filename
- Preserves all fields including AI outputs

## 🧪 Testing

### Test User Dashboard
1. Submit a 5-star review: "Excellent service!"
   - Expect: Enthusiastic AI response, balloons animation
2. Submit a 1-star review: "Terrible experience, very disappointed."
   - Expect: Apologetic AI response, no balloons
3. Submit a 3-star review: "It was okay, could be better."
   - Expect: Balanced AI response

### Test Admin Dashboard
1. Verify all submissions appear in chronological order
2. Check metrics update correctly
3. Test filters (date, rating, sentiment)
4. Verify AI summaries are concise
5. Check recommended actions are specific and actionable
6. Test CSV export

## 🔧 Customization

### Modify AI Prompts
Edit functions in `app_user.py`:
- `generate_user_response()` - Customer-facing response tone
- `generate_summary()` - Summary length/style
- `generate_actions()` - Action specificity

### Change Styling
Edit `.streamlit/config.toml`:
- `primaryColor` - Accent color
- `backgroundColor` - Main background
- `secondaryBackgroundColor` - Sidebar/containers

### Add New Features
Ideas for enhancement:
- Email notifications for negative reviews
- Sentiment trend alerts
- Word cloud from reviews
- Response templates
- Multi-language support

## 📈 Performance Optimization

### API Rate Limiting
- Gemini free tier: 60 requests/minute
- Current implementation: ~3 API calls per submission
- Can handle ~20 submissions/minute

### Caching
- Admin dashboard uses `@st.cache_data(ttl=5)` for live updates
- Reduces file I/O operations

### Scaling Considerations
For >1000 submissions:
- Migrate to proper database (PostgreSQL, MongoDB)
- Implement pagination in admin dashboard
- Add search functionality
- Use async API calls

## 🐛 Troubleshooting

### Issue: "API key not configured"
**Solution**: Ensure `.streamlit/secrets.toml` exists with correct API key

### Issue: Data not syncing between dashboards
**Solution**: Both apps must access same `feedback_data.csv` file. On Streamlit Cloud, ensure both apps are in same repo.

### Issue: Charts not displaying
**Solution**: Ensure `plotly` is installed: `pip install plotly`

### Issue: CSV file corruption
**Solution**: Delete `feedback_data.csv` and restart. File will be recreated.

## 📝 Submission Checklist

- [ ] Both dashboards running locally
- [ ] API key configured
- [ ] Test submissions working
- [ ] AI responses generating correctly
- [ ] Admin dashboard showing submissions
- [ ] Charts rendering properly
- [ ] GitHub repository created
- [ ] User dashboard deployed on Streamlit Cloud
- [ ] Admin dashboard deployed on Streamlit Cloud
- [ ] Both deployment URLs saved
- [ ] README updated with deployment URLs
- [ ] Code pushed to GitHub

## 🔗 Deployment URLs

After deployment, update this section:

- **User Dashboard**: `https://your-user-dashboard.streamlit.app`
- **Admin Dashboard**: `https://your-admin-dashboard.streamlit.app`
- **GitHub Repository**: `https://github.com/YOUR_USERNAME/fynd-feedback-system`

## 🎓 Learning Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Gemini API Guide](https://ai.google.dev/docs)
- [Plotly Charts](https://plotly.com/python/)
- [Streamlit Cloud Deployment](https://docs.streamlit.io/streamlit-community-cloud)

## 📄 License

This project is part of the Fynd AI Intern Assessment.

---

**Built with ❤️ using Streamlit and Gemini AI**
