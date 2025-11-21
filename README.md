# 📝 Smart Meeting & Task Assistant

A full-stack web application that helps engineering teams organize meetings, extract action items using AI, and ask questions about past discussions.

## 🚀 Features

- **Meeting Management**: Create, edit, and view meetings with participants, dates, and detailed notes
- **AI-Powered Summarization**: Automatically generate concise summaries of meeting notes using Google Gemini
- **Action Item Extraction**: Intelligently extract action items with owners and due dates from meeting notes
- **Automatic Tag Generation**: Generate relevant tags to categorize and organize meetings
- **Smart Q&A**: Ask questions about past meetings and get AI-powered answers based on keyword search
- **Action Item Tracking**: View and manage all action items with status updates (pending, in progress, completed)
- **Keyword-Based Search**: Efficient hashmap-based indexing for fast meeting retrieval

## 🛠️ Tech Stack

### Frontend
- **Streamlit**: Interactive web interface for meeting management
- **Python Requests**: API communication with FastAPI backend

### Backend
- **FastAPI**: Modern, high-performance REST API framework
- **Uvicorn**: ASGI server for running FastAPI
- **SQLAlchemy**: SQL toolkit and ORM for database operations
- **SQLite**: Lightweight, serverless database

### AI & Agent
- **Google Gemini API**: Advanced language model for summarization, extraction, and Q&A
- **Langgraph**: Framework for building AI applications
- **Custom Keyword Indexer**: Hashmap-based search for efficient meeting retrieval

## 📋 Prerequisites

- Python 3.11+
- Google Gemini API Key (get one at https://aistudio.google.com/apikey)

## ⚙️ Setup & Installation

1. **Clone or access the project**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   The application requires a `GEMINI_API_KEY` environment variable. On Replit, this is automatically managed through Secrets. For local development, create a `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   DATABASE_URL=sqlite:///./meetings.db
   BACKEND_URL=http://localhost:8000
   ```

4. **Initialize the database**:
   The database is automatically initialized when the backend starts for the first time.

## 🏃 Running the Application

### Running Both Services

The application consists of two services that run simultaneously:

1. **Start the Backend API**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start the Streamlit Frontend** (in a separate terminal):
   ```bash
   streamlit run frontend/app.py --server.port 5000 --server.address 0.0.0.0
   ```

3. **Access the application**:
   - Frontend UI: http://localhost:5000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### On Replit

Both workflows are pre-configured and will start automatically. Just click the "Run" button!

## 📖 Usage Guide

### Creating a Meeting

1. Navigate to **"➕ Create Meeting"** in the sidebar
2. Fill in the meeting details:
   - Title (e.g., "Sprint Planning Meeting")
   - Date and time
   - Participants (comma-separated)
   - Meeting notes
3. Check "Process with AI immediately" to auto-generate summary, action items, and tags
4. Click "Create Meeting"

### Processing Meetings with AI

From the Dashboard, click the **"🤖 Process with AI"** button on any meeting to:
- Generate a concise summary
- Extract action items with owners and due dates
- Create relevant tags

### Managing Action Items

1. Navigate to **"✅ Action Items"**
2. View all action items across all meetings
3. Filter by status (pending, in progress, completed)
4. Update action item status directly from the interface

### Asking Questions About Meetings

1. Navigate to **"🤖 Ask AI"**
2. Type your question (e.g., "What did we decide about the new feature?")
3. Click "Ask"
4. Get AI-powered answers based on relevant meeting notes

### Editing Meetings

1. Navigate to **"✏️ Edit Meeting"**
2. Select a meeting from the dropdown
3. Update the title, notes, or participants
4. Optionally re-process with AI to update summary and action items

## 🗄️ Database Schema

### Meeting Table
- `id`: Primary key
- `title`: Meeting title
- `datetime`: Meeting date and time
- `participants`: Comma-separated list of attendees
- `raw_notes`: Original meeting notes
- `ai_summary`: AI-generated summary
- `tags`: Comma-separated tags
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### ActionItem Table
- `id`: Primary key
- `meeting_id`: Foreign key to Meeting
- `description`: Action item description
- `owner`: Person responsible (if mentioned)
- `due_date`: Due date (if mentioned)
- `status`: pending | in_progress | completed
- `created_at`: Creation timestamp

## 🔍 How It Works

### Keyword-Based Search
The application uses a custom hashmap indexing system:
1. When a meeting is created, all words in the notes are tokenized
2. Each word is mapped to the meeting ID in a hashmap
3. When asking questions, keywords are extracted from the query
4. The hashmap quickly finds all meetings containing those keywords
5. Relevant meetings are ranked by keyword frequency

### AI Processing
Using Google Gemini API, the application:
1. **Summarizes**: Condenses meeting notes into 2-3 concise paragraphs
2. **Extracts**: Identifies action items with owners and due dates (only if explicitly mentioned)
3. **Tags**: Generates 3-5 relevant topic tags
4. **Answers**: Uses retrieved meeting context to answer questions accurately

## 📁 Project Structure

```
.
├── agent/
│   ├── __init__.py
│   └── meeting_agent.py          # Gemini AI agent for summarization and Q&A
├── backend/
│   ├── __init__.py
│   ├── keyword_indexer.py        # Hashmap-based keyword indexing
│   └── main.py                   # FastAPI application and endpoints
├── database/
│   ├── __init__.py
│   └── models.py                 # SQLAlchemy database models
├── frontend/
│   └── app.py                    # Streamlit web interface
├── .streamlit/
│   └── config.toml               # Streamlit configuration
├── requirements.txt              # Python dependencies
├── .env.example                  # Example environment variables
└── README.md                     # This file
```

## 🔧 API Endpoints

### Meetings
- `POST /meetings/` - Create a new meeting
- `GET /meetings/` - Get all meetings
- `GET /meetings/{meeting_id}` - Get a specific meeting
- `PUT /meetings/{meeting_id}` - Update a meeting
- `DELETE /meetings/{meeting_id}` - Delete a meeting
- `POST /meetings/{meeting_id}/process` - Process meeting with AI

### Action Items
- `GET /action-items/` - Get all action items
- `GET /meetings/{meeting_id}/action-items/` - Get action items for a meeting
- `PATCH /action-items/{action_item_id}` - Update action item status

### AI
- `POST /ask-ai/` - Ask a question about meetings


