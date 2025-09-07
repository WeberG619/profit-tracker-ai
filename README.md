# Profit Tracker AI

![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v3.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-live-success.svg)
[![Deployed on Render](https://img.shields.io/badge/deployed%20on-Render-46E3B7.svg)](https://profit-tracker-ai.onrender.com)

> Stop losing money on jobs. AI-powered receipt tracking for trade professionals.

## 🚀 Live Demo

**Try it now:** [profit-tracker-ai.onrender.com](https://profit-tracker-ai.onrender.com)
- Username: `admin`
- Password: `admin123`

## 💼 The Problem It Solves

Local trade professionals (plumbers, electricians, contractors) lose $2,000-5,000 monthly on underpriced jobs because they don't track material costs accurately. This tool uses AI to instantly extract receipt data and track profit margins in real-time.

## ✨ Features

### Working Now
- ✅ **PDF & Image Upload** - Drag-and-drop receipts in any format
- ✅ **AI Receipt Processing** - Claude 3.5 extracts vendor, total, date, line items
- ✅ **Job Assignment** - Link receipts to specific jobs
- ✅ **Professional Interface** - Clean, modern design with image preview
- ✅ **Multi-User Support** - Company-based data isolation
- ✅ **PostgreSQL Database** - Reliable data persistence

### Coming Soon
- 📱 **SMS Receipt Upload** - Text photos to track expenses
- 📊 **Profit Analytics** - Real-time margin tracking per job
- 💡 **Price Recommendations** - AI-suggested pricing based on history
- 📥 **Export Features** - CSV, PDF, QuickBooks integration
- 🎯 **Pattern Detection** - Identify money-losing job types
- 📧 **Email Reports** - Weekly profit/loss summaries

## 🚀 Quick Start

### Deploy to Render (Recommended)

1. **Fork this repository** to your GitHub account

2. **Deploy to Render**:
   - Sign up at [render.com](https://render.com)
   - Create a new PostgreSQL database (free tier)
   - Create a new Web Service from your forked repo
   - Add environment variables:
     - `DATABASE_URL` - From your PostgreSQL database
     - `ANTHROPIC_API_KEY` - From [anthropic.com](https://anthropic.com)
     - `SECRET_KEY` - Any random string
     - `TWILIO_*` - Optional, for SMS features

3. **Initialize Database**:
   - Visit `https://your-app.onrender.com/init-db-emergency`
   - Creates tables and admin user (admin/admin123)

### Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/WeberG619/profit-tracker-ai)

1. Click the button above
2. Enter your Anthropic API key
3. Optional: Add Twilio credentials for SMS
4. Deploy and start tracking profits!

### Local Development

```bash
# Clone the repository
git clone https://github.com/WeberG619/profit-tracker-ai.git
cd profit-tracker-ai

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python -c "from app.app_factory import create_app; app = create_app(); app.app_context().push(); from app.models import db; db.create_all()"

# Run the application
python app/app.py
```

## 🛠️ How It Works

1. **📸 Capture** - Take photo of receipt or text it to your Twilio number
2. **🤖 Process** - AI extracts vendor, total, line items automatically
3. **✏️ Review** - Quick edit if needed (AI is 95% accurate)
4. **📊 Track** - See real-time profit margins per job
5. **🎯 Learn** - Get alerts when jobs approach budget limits

## 💻 Tech Stack

- **Backend**: Python 3.9+, Flask 3.0
- **AI**: Anthropic Claude 3.5 Vision API
- **Database**: PostgreSQL (production), SQLite (development)
- **SMS**: Twilio API
- **Frontend**: Tailwind CSS, Chart.js
- **Deployment**: Render, Heroku, Docker

## 📸 How It Works

1. **Upload Receipt** - Drag & drop PDF or image
2. **AI Processes** - Claude extracts all data automatically
3. **Review & Edit** - Verify extracted information
4. **Assign to Job** - Link to specific customer job
5. **Track Profits** - Monitor margins in real-time

## 🔧 Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL (for production)
- OpenAI API key
- Twilio account (optional, for SMS)

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:pass@localhost/dbname
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
```

### Database Setup

```bash
# Run migrations
python app/migrations.py

# Generate sample data (optional)
python scripts/sample_data.py
```

## 📚 API Documentation

See [docs/API.md](docs/API.md) for complete API reference.

### Quick Examples

```bash
# Upload receipt
curl -X POST http://localhost:5000/api/upload \
  -F "file=@receipt.jpg" \
  -F "job_id=1001"

# Get profit insights
curl http://localhost:5000/api/insights/patterns

# Export to QuickBooks
curl http://localhost:5000/api/export/quickbooks?start=2024-01-01
```

## 🤝 Contributing

We love contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ in Sandpoint, Idaho
- Inspired by conversations with local trade professionals
- Special thanks to the plumbers and electricians who shared their pain points

## 📞 Support

- 📧 Email: support@profittrackerai.com
- 📖 Documentation: [Full Docs](docs/README.md)
- 🐛 Issues: [GitHub Issues](https://github.com/WeberG619/profit-tracker-ai/issues)

---

**Made with 🔨 by [Weber Garcia](https://github.com/WeberG619)**

*If this tool saves your business money, consider [buying me a coffee](https://buymeacoffee.com/webergarcia) ☕*