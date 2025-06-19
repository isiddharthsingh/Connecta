# 🤖 Connecta

A comprehensive personal AI assistant that integrates with Gmail, GitHub, Calendar, and Google Drive to help you stay organized and productive. Now with **file content reading** - read Google Docs, Sheets, and text files directly in your terminal!

## ✨ Features

### 📧 Email Management
- Check unread email count
- Search emails by sender or keyword
- Get recent emails overview
- Email summarization (coming soon)

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

### 🎯 Smart Features
- Natural language query processing
- Daily productivity summaries
- Cross-service insights
- **File content reading and search** across Google Drive
- Smart file type detection and error handling
- Proactive notifications

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

### 4. Initial Setup

```bash
python main.py setup
```

This will:
- Create a `.env` file template
- Guide you through API credential setup
- Check your configuration

### 5. Configure API Credentials

Edit the `.env` file with your API credentials:

```env
# OpenAI (Required for AI features)
OPENAI_API_KEY=your_openai_api_key_here

# GitHub (Required for GitHub features)  
GITHUB_TOKEN=your_github_personal_access_token

# Google APIs (Gmail, Calendar)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### 6. Start Using

```bash
# Interactive mode
python main.py interactive

# Single queries
python main.py query "How many unread emails?"
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

### OpenAI API Key
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy the key to your `.env` file

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
│   │   ├── query_parser.py   # Natural language understanding
│   │   └── response_generator.py
│   ├── cli/                  # Command line interface
│   │   └── interface.py
│   ├── assistant.py          # Main assistant orchestrator
│   └── config.py             # Configuration management
├── config/
│   └── settings.yaml         # Default settings
├── requirements.txt          # Python dependencies
├── main.py                   # Application entry point
└── README.md
```

## 🔌 Integrations

### ✅ Currently Available
- **Gmail**: Email management and search
- **GitHub**: PR reviews, issues, commits, stats
- **Google Calendar**: Schedule management, meetings, free time
- **Google Drive**: File browsing, search, **content reading**, storage management, collaboration

### 🚧 Coming Soon
- **Trello**: Task and project tracking
- **Slack**: Team communication insights
- **Notion**: Note and knowledge management

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
