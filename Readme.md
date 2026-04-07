# CapMed-Sci 

A medical research chat application that answers questions based on scientific literature from PubMed Central, with inline citation and structured responses

## Project Overview

This is a Proof of Concept (PoC) application designed for medical researchers to query scientific literature using natural language. The system retrieves relevant open-access papers from PubMed Central, uses OpenAI GPT-4o to generate structured answers, and provides inline citations for verification.

### Key Features

- **Natural Language Queries**: Ask questions in plain English (e.g., "What is GLP-1?")
- **Structured Responses**: Answers organized into categories (Analytical, Clinical, etc.)
- **Inline Citations**: Every claim cited with references like [1], [2], [3]
- **Source Verification**: View 5-10 papers with title, authors, year, abstract, and links
- **Follow-up Questions**: Ask 3-5 follow-up questions with context awareness
- **Real-time Streaming**: See answers appear in real-time as they're generated
- **Zero Hallucinations**: Answers based strictly on retrieved papers

### Tech Stack

**Backend (FastAPI)**
- FastAPI == 0.109.0
- OpenAI Python SDK == 1.12.0
- httpx for async HTTP requests
- Pydantic for data validation
- Python 3.10 (3.9+)

**Frontend (React + "TypeScript")**
- React 18.2.0
- TypeScript 5.2.2
- Vite 5.0.8
- TailwindCSS 3.4.0
- React Markdown for rendering

**External APIs**
- PubMed Central API (free, no API key required)
- OpenAI GPT-4o API (requires API key)

## Prerequisites
 
- **Python 3.10 (3.9+)**
- **Node.js 18+** and npm/yarn
- **OpenAI API Key** (get from https://platform.openai.com/)
- **Email address** (required for PubMed API identification)


## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/ddoyediran/atosprototype.git
cd atosprototype
```

### 2. Backend Setup
```bash
cd backend
 
# Create virtual environment
python3.10 -m venv venv # on Windows, I think 'py -3.10 -m venv venv'
source venv/bin/activate  # On Windows: venv\Scripts\activate
 
# Install dependencies
pip install -r requirements.txt
 
# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key and email

# Test BioPython integration (Optional)
python test_pubmed.py
```

**Required Environment Variables:**
```env
OPENAI_API_KEY=<your-openai-key-here>
PUBMED_EMAIL=your.email@example.com
```

### 3. Run Backend
 
```bash

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Wait for: "Application startup complete."

# From backend directory
# python app/main.py
```
 
Backend will be available at: http://localhost:8000
 
API Documentation: http://localhost:8000/docs

### 4. Frontend Setup
 
```bash
cd frontend
 
# Install dependencies
npm install
 
# Configure environment
# Create .env file with:
# echo "VITE_API_BASE_URL=http://localhost:8000" > .env
```
 
### 5. Run Frontend
 
```bash
# From frontend directory
npm run dev
```
 
Frontend will be available at: http://localhost:5173

## Limitations (PoC)
 
1. **No Persistence:** Conversations not saved (browser memory only)
2. **No Caching:** Papers re-fetched for each session
3. **No Authentication:** Open access (add in production)
4. **No Rate Limiting:** Unlimited requests (add in production)
5. **No Analytics:** No usage tracking
6. **PDF Export:** Not implemented in PoC

## License


## Acknowledgments
 
- PubMed Central for open-access scientific papers
- OpenAI for GPT-4o API
- FastAPI and React communities