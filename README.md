🏙️ CityPulse AI - Intelligent Civic Complaint Management System

An AI-powered civic complaint management system built for AI-for-Good hackathons. Uses Groq's LLaMA 3 for intelligent complaint analysis, prioritization, and clustering.

## 🌟 Features

### For Citizens
- 📱 **Simple Login** - Mobile OTP-based authentication
- 📝 **Easy Complaint Submission** - Describe issues in natural language
- 🤖 **AI Auto-Classification** - Automatically categorizes complaints
- 📸 **Image Upload & Validation** - AI verifies image matches complaint
- 🎯 **Smart Follow-up Questions** - Category-specific questions for better context
- 📊 **Real-time AI Analysis** - Instant priority and impact assessment

### For Administrators
- 📊 **Comprehensive Dashboard** - Key metrics and analytics at a glance
- 🎯 **Priority Clusters** - AI groups similar complaints by location and category
- 🔮 **Predictive Insights** - AI forecasts potential civic crises
- 📈 **Trend Analysis** - 7-day complaint trends with visualizations
- 🔄 **Complaint Lifecycle** - Track from submission to resolution
- 💡 **Resource Allocation** - AI suggests optimal resource deployment

### AI Capabilities
- **Category Detection** - Garbage, Roads, Water, Electricity, Parks, Noise, Streetlights
- **Priority Scoring** - 1-100 scale with High/Medium/Low classification
- **Severity Assessment** - Critical, Moderate, Minor
- **Impact Estimation** - Number of citizens affected
- **Cluster Formation** - Groups complaints by area and type
- **Predictive Alerts** - Warns about emerging patterns

## 🏗️ Architecture

```
citypulse-ai/
├── backend/
│   ├── server.py              # FastAPI main server
│   ├── ai_engine.py           # Groq AI integration
│   ├── complaint_manager.py   # SQLite database operations
│   ├── priority_engine.py     # Clustering & insights
│   └── image_validator.py     # Image verification
├── frontend/
│   ├── login.html             # Citizen login page
│   ├── complaint.html         # Complaint submission
│   ├── dashboard.html         # Admin dashboard
│   └── styles.css             # Modern UI styling
├── data/
│   └── complaints.db          # SQLite database (auto-created)
├── uploads/
│   └── images/                # Uploaded images (auto-created)
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Groq API Key (free tier works!)

### Installation

1. **Clone or Download** the project

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Set Groq API Key** (Optional - works in mock mode without it)
```bash
# Linux/Mac
export GROQ_API_KEY="your_groq_api_key_here"

# Windows (CMD)
set GROQ_API_KEY=your_groq_api_key_here

# Windows (PowerShell)
$env:GROQ_API_KEY="your_groq_api_key_here"
```

**Get your free Groq API key:** https://console.groq.com/keys

4. **Run the Server**
```bash
# Method 1: Using uvicorn directly
uvicorn backend.server:app --reload --host 0.0.0.0 --port 8000

# Method 2: Using Python
python -m uvicorn backend.server:app --reload
```

5. **Access the Application**
- **Citizen Portal:** http://localhost:8000
- **Admin Dashboard:** http://localhost:8000/dashboard.html
- **API Docs:** http://localhost:8000/docs

## 📱 How to Use

### Citizen Flow
1. **Login** - Enter mobile number → Get OTP (displayed on screen for demo) → Verify
2. **Submit Complaint**:
   - Select category or let AI auto-detect
   - Describe the issue
   - Enter location
   - Answer smart follow-up questions
   - Upload image (optional)
3. **Get AI Analysis** - See category, priority, impact, and resolution timeline
4. **Track Status** - View in recent complaints sidebar

### Admin Flow
1. **Open Dashboard** - View all metrics and insights
2. **Review AI Insights** - Check predictive alerts
3. **Examine Clusters** - See grouped complaints by area
4. **Update Status** - Click "Update" on any complaint
5. **Track Trends** - Monitor 7-day complaint patterns

## 🤖 AI Models Used

### Primary Model (Groq)
- **Model:** `llama-3.1-8b-instant`
- **Purpose:** Complaint analysis, classification, prioritization
- **Why:** Fast, accurate, optimized for free tier

### Image Validation (Optional)
- **Model:** `llava-v1.5-7b-4096-preview`
- **Purpose:** Verify images match complaint category
- **Fallback:** Mock validation if API unavailable

### Mock Mode
- Works **without** Groq API key
- Uses intelligent keyword-based analysis
- Perfect for demos and testing
- Automatically activates if no API key set

## 🎯 Key Differentiators

1. **Free Tier Optimized** 
   - Efficient API usage with caching
   - Works in mock mode for unlimited demos
   - SQLite - no database setup needed

2. **Smart Follow-up System**
   - Category-specific questions
   - Better AI context → Better prioritization
   - Example: Garbage complaints ask about smell, duration, residential proximity

3. **Cluster Intelligence**
   - Groups 3+ similar complaints by location
   - Suggests resource allocation
   - Example: "Deploy 2 garbage trucks to Whitefield"

4. **Predictive Insights**
   - Trend detection
   - Crisis forecasting
   - Example: "Garbage complaints increasing 50% - potential crisis in 72hrs"

5. **Image Validation**
   - AI checks if photo matches complaint
   - Prevents misclassification
   - Builds trust in the system

## 🔧 Configuration

### Environment Variables
```bash
GROQ_API_KEY=your_key_here  # Optional - works without it
```

### Database
- **Type:** SQLite
- **Location:** `data/complaints.db`
- **Auto-created** on first run
- **Reset:** Delete `data/complaints.db` file

### Port Configuration
Change port in startup command:
```bash
uvicorn backend.server:app --reload --port 8080
```

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | OTP login |
| POST | `/api/submit-complaint` | Submit new complaint |
| GET | `/api/complaints` | Get all complaints |
| GET | `/api/recent-complaints` | Get recent complaints |
| GET | `/api/dashboard-analytics` | Dashboard data |
| POST | `/api/update-status` | Update complaint status |
| POST | `/api/reraise` | Reraise resolved complaint |
| GET | `/api/get-followup-questions` | Get category questions |

## 🎨 UI Features

- **Modern Gradient Design** - Eye-catching, professional
- **Responsive Layout** - Works on mobile, tablet, desktop
- **Real-time Charts** - Category distribution, 7-day trends
- **Status Badges** - Color-coded for quick scanning
- **Priority Indicators** - Visual alerts for urgent issues
- **Dark Mode Ready** - Admin dashboard uses dark theme

##  Troubleshooting

### "Module not found" error
```bash
# Make sure you're in the project root directory
cd citypulse-ai

# Run with module syntax
python -m uvicorn backend.server:app --reload
```

### Database locked error
```bash
# Delete and recreate database
rm data/complaints.db
# Restart server
```

### Groq API rate limit
- System auto-falls back to mock mode
- Uses caching to reduce API calls
- Free tier: 30 requests/minute (should be enough)

### Port already in use
```bash
# Use different port
uvicorn backend.server:app --reload --port 8080
