# 🤖 Connecta

A comprehensive personal AI assistant that integrates with Gmail, GitHub, Calendar, and Google Drive to help you stay organized and productive. Now with **file content reading** and **local AI capabilities** via LM Studio - read Google Docs, Sheets, and text files directly in your terminal, and get AI-powered email summaries without cloud dependencies!

## ✨ Features

### 📧 Email Management
- Check unread email count
- Search emails by sender or keyword
- Get recent emails overview
- **🤖 AI-powered email summarization** (with LM Studio or OpenAI)

### 🔄 GitHub Integration
- Review pull requests that need your attention
- Track issues assigned to you
- Monitor recent commits
- Repository statistics and insights

### 📅 Calendar Integration
- Daily schedule overview
- Upcoming meetings and events
- Free time identification
- Tomorrow and weekly schedule views
- Smart calendar insights

### 📄 Google Drive Integration
- **📖 Read file content directly in terminal** (Google Docs, Sheets, Slides, text files)
- Browse and search files by type (Docs, Sheets, Slides, PDFs, Images)
- File search by name and content with content preview
- View shared files and collaborations
- Storage usage monitoring
- Folder navigation and organization
- Recent files access
- Smart file size handling and error messages

### 🤖 AI Features
- **Local AI with LM Studio** - Privacy-focused AI processing on your machine
- **Cloud AI with OpenAI** - Alternative AI provider support
- **Email summarization** - Get structured summaries with key topics and action items
- **Daily summaries** - AI-enhanced productivity overviews
- Natural language query processing
- Cross-service insights and automation

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd personal-ai-assistant
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. AI Setup (Choose One)

#### Option A: Local AI with LM Studio (Recommended)
1. Download and install [LM Studio](https://lmstudio.ai/)
2. Download a model (recommended: **Google Gemma 3-4B** for best performance)
3. Start the LM Studio server on `http://localhost:1234`
4. The assistant will automatically use local AI (configured by default)

#### Option B: Cloud AI with OpenAI
1. Get an OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add it to your `.env` file
3. Change `ai_provider` to `"openai"` in `config/settings.yaml`

### 5. Initial Setup

```bash
python main.py setup
```

This will:
- Create a `.env` file template
- Guide you through API credential setup
- Check your configuration

### 6. Configure API Credentials

Edit the `.env` file with your API credentials:

```env
# OpenAI (Optional - only needed if using OpenAI instead of LM Studio)
OPENAI_API_KEY=your_openai_api_key_here

# GitHub (Required for GitHub features)  
GITHUB_TOKEN=your_github_personal_access_token

# Google APIs (Gmail, Calendar)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### 7. Start Using

```bash
# Interactive mode
python main.py interactive

# Single queries
python main.py query "How many unread emails?"
python main.py query "Summarize emails from john@company.com"
python main.py query "What PRs need review?"

# Check system status
python main.py status
```

## 📖 Usage Examples

### Email Commands
```bash
python main.py query "How many unread emails?"
python main.py query "Show emails from john@company.com"
python main.py query "Recent emails"
python main.py query "Emails about project update"

# 🤖 AI-Powered Email Summarization
python main.py query "summarize emails from hello@n8n.io"
python main.py query "summarize emails from no-reply@github.com"
python main.py query "summary of emails from support@company.com"
```

### AI Summary Features
The AI email summarization provides:
- **Key Topics & Themes** - Main subjects and discussion points
- **Important Action Items** - Tasks and follow-ups required
- **Urgent Matters** - Time-sensitive items that need attention
- **Overall Tone** - Communication style and urgency level
- **Structured Format** - Easy-to-read bullet points and categories

Example output:
```
📧 AI Summary for emails from hello@n8n.io:

• Key Topics & Themes:
  • Introduction to n8n workflow automation platform
  • Platform overview and capabilities for technical teams

• Important Action Items:
  • Explore n8n platform features
  • Consider workflow automation opportunities

• Overall Tone: Welcoming and informative introduction
```

### GitHub Commands
```bash
python main.py query "What PRs need review?"
python main.py query "Show my recent commits"
python main.py query "Issues assigned to me"
python main.py query "Repository statistics"
```

### Calendar Commands
```bash
python main.py query "What's my schedule today?"
python main.py query "Schedule for tomorrow"
python main.py query "This week's calendar"
python main.py query "Next meeting"
python main.py query "Free time today"
```

### Google Drive Commands
```bash
# File Type Browsing
python main.py query "show my google docs"
python main.py query "show my google sheets"
python main.py query "show my google slides"
python main.py query "show my folders"
python main.py query "show my PDFs"
python main.py query "show my images"

# File Search
python main.py query "search files for project"
python main.py query "search files for budget"
python main.py query "find files about presentation"

# File Reading & Content Access
python main.py query "read file my-document"
python main.py query "read file prof yotov logger"      # Read Google Doc content
python main.py query "read file project-notes.txt"      # Read text files
python main.py query "show content of file"             # Interactive file selection
python main.py query "search and read files for meeting"  # Search and read content

# File Reading Features:
# ✅ Reads and displays file content directly in terminal
# ✅ Shows file metadata (type, size, character count)
# ✅ Smart file size limits (10MB max, 2KB preview for large files)
# ✅ Handles multiple files with same name (shows alternatives)
# ✅ Helpful error messages for unsupported file types

# Supported file types for reading:
# • Google Docs (exported as plain text)
# • Google Sheets (exported as CSV format)
# • Google Slides (exported as plain text)
# • Text files (.txt, .md, .py, .js, .html, .css, etc.)
# • Data files (JSON, XML, CSV)
# • Code files (most programming languages)

# Unsupported file types (with helpful error messages):
# • PDF files (use Google Drive web interface)
# • Images, videos, audio files
# • Binary and encrypted files

# Storage & Sharing
python main.py query "show shared files"
python main.py query "what's my drive storage usage"
python main.py query "show recent files"
```

### General Commands
```bash
python main.py query "Daily summary"
python main.py query "System status"
python main.py query "Help"
```

### Handling Unsupported Files
```bash
# Example: Trying to read a PDF (shows helpful error)
python main.py query "read file futeur-contract"
```

### Interactive File Selection
```bash
python main.py query "show content of file"
```

### Key File Reading Features

✅ **Smart Content Display**
- Full content for small files (< 2KB)
- Preview with truncation for large files (> 2KB)
- Character count and file size information

✅ **File Type Support**
- Google Docs → Plain text export
- Google Sheets → CSV format export
- Google Slides → Plain text export
- Text files → Direct reading
- Code files → Syntax preserved

✅ **Error Handling**
- Clear error messages for unsupported files (PDFs, images)
- Alternative file suggestions when multiple matches found
- File size limit protection (10MB max)

✅ **Search Integration**
- Search for files and read content in one command
- Content preview in search results
- Combined metadata and content display

## 🔧 API Setup Guides

### LM Studio (Local AI - Recommended)
1. Download [LM Studio](https://lmstudio.ai/) for your operating system
2. Install and launch LM Studio
3. **Download a model** (recommended models):
   - **Google Gemma 3-4B** (best balance of speed and quality)
   - Llama 3.2 3B (alternative option)
   - Phi-3 Mini (lightweight option)
4. **Start the server**:
   - Click "Start Server" in LM Studio
   - Ensure it's running on `http://localhost:1234`
   - Load your chosen model
5. **Test connection**:
   ```bash
   curl http://localhost:1234/v1/models
   ```
6. The assistant will automatically detect and use your loaded model

**Benefits of LM Studio:**
- 🔒 **Privacy** - All processing happens locally
- ⚡ **Speed** - Fast responses (0.2-0.5 seconds with Gemma)
- 💰 **Cost** - No API fees or usage limits
- 🌐 **Offline** - Works without internet connection

### OpenAI API Key (Cloud AI - Alternative)
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy the key to your `.env` file
4. Change `ai_provider` to `"openai"` in `config/settings.yaml`

### GitHub Personal Access Token
1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:user`, `read:org`
4. Copy the token to your `.env` file

### Google APIs (Gmail, Calendar, Drive)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API, Calendar API, and Drive API
4. Create OAuth 2.0 credentials
5. Add your credentials to `.env` file

**Important**: For Drive integration, make sure to enable the Google Drive API in addition to Gmail and Calendar APIs.

## 🏗️ Architecture

```
personal-assistant/
├── src/
│   ├── integrations/          # Service integrations
│   │   ├── gmail/            # Gmail API integration
│   │   ├── github/           # GitHub API integration
│   │   ├── calendar/         # Google Calendar integration
│   │   ├── drive/            # Google Drive integration
│   │   └── base/             # Base integration classes
│   ├── ai/                   # AI and NLP components
│   │   ├── lmstudio_client.py # LM Studio local AI client
│   │   ├── query_parser.py   # Natural language understanding
│   │   └── response_generator.py # AI-enhanced response generation
│   ├── cli/                  # Command line interface
│   │   └── interface.py
│   ├── assistant.py          # Main assistant orchestrator
│   └── config.py             # Configuration management
├── config/
│   └── settings.yaml         # Default settings (AI provider config)
├── requirements.txt          # Python dependencies
├── main.py                   # Application entry point
└── README.md
```

## 🔌 Integrations

### ✅ Currently Available
- **Gmail**: Email management, search, **AI-powered summarization**
- **GitHub**: PR reviews, issues, commits, stats
- **Google Calendar**: Schedule management, meetings, free time
- **Google Drive**: File browsing, search, **content reading**, storage management, collaboration
- **Local AI**: LM Studio integration for privacy-focused AI processing
- **Cloud AI**: OpenAI integration for cloud-based AI capabilities

### 🚧 Coming Soon
- **Trello**: Task and project tracking
- **Slack**: Team communication insights
- **Notion**: Note and knowledge management
- **Enhanced AI Features**: More AI-powered insights across all integrations

## 🎨 CLI Interface

The assistant features a beautiful terminal interface with:
- 🌈 Rich formatting and colors
- 📊 Tables and panels for data display
- ⏳ Loading spinners and progress indicators
- 💬 Interactive prompts and help

## 🛠️ Development

### Adding New Integrations

1. Create a new integration class in `src/integrations/`
2. Inherit from `BaseIntegration`
3. Implement required methods: `authenticate()`, `test_connection()`
4. Add integration patterns to `QueryParser`
5. Update `ResponseGenerator` for formatting

### Example Integration Structure

```python
class NewServiceIntegration(BaseIntegration):
    def __init__(self, cache_duration: int = 300):
        super().__init__("NewService", cache_duration)
    
    async def authenticate(self) -> bool:
        # Implement authentication logic
        pass
    
    async def test_connection(self) -> bool:
        # Test service connection
        pass
    
    async def get_data(self) -> Dict[str, Any]:
        # Implement data retrieval
        pass
```

## 📋 Requirements

- Python 3.9+
- Internet connection for API calls
- API credentials for desired services

## 🔒 Security

- API credentials stored in environment variables
- No sensitive data logged or cached permanently
- Secure token handling for OAuth flows

## 🐛 Troubleshooting

### Common Issues

**Import Errors**
```bash
pip install -r requirements.txt
```

**Authentication Failures**
- Check API credentials in `.env` file
- Verify API key permissions and scopes
- Check internet connection

**LM Studio Connection Issues**
- Ensure LM Studio is running on `http://localhost:1234`
- Load a model in LM Studio before starting the assistant
- Check if the server is started in LM Studio interface
- Test connection: `curl http://localhost:1234/v1/models`
- Try restarting LM Studio if models aren't detected

**AI Summarization Not Working**
- For LM Studio: Check if server is running and model is loaded
- For OpenAI: Verify API key is correct and has available credits
- Check `ai_provider` setting in `config/settings.yaml`
- Review logs for specific error messages

**No Data Returned**
- Ensure services have data to return
- Check API rate limits
- Review logs in `logs/assistant.log`

### Debug Mode

Enable debug logging:
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your integration or feature
4. Test thoroughly
5. Submit a pull request

## 📞 Support

- 📖 Check the [documentation](README.md)
- 🐛 Report issues on GitHub
- 💡 Request features via GitHub issues

---

**Made with ❤️ for productivity enthusiasts**
