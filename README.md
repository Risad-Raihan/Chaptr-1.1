# 📚 Chaptr 1.1

**AI-Powered Book Analysis & Chat Platform**

Transform your reading experience with intelligent book analysis, RAG-powered conversations, and comprehensive book management.

[![GitHub repo](https://img.shields.io/badge/GitHub-Chaptr--1.1-blue?style=flat-square&logo=github)](https://github.com/Risad-Raihan/Chaptr-1.1)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## 🎯 What is Chaptr?

Chaptr is a cutting-edge RAG (Retrieval-Augmented Generation) platform that allows users to:
- **Upload any book** (PDF/ePub) and chat with it using AI
- **Get instant summaries** and deep analysis of your books
- **Build a personal library** with intelligent organization
- **Ask questions** and get contextual answers from your books

Perfect for students, researchers, book clubs, and avid readers who want to interact with their books in revolutionary ways.

---

## 🚀 Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 14 + TypeScript + Tailwind CSS | Modern, responsive UI |
| **Backend** | FastAPI + Python 3.11+ | High-performance API |
| **Database** | PostgreSQL | User data & book metadata |
| **Vector DB** | Chroma | RAG embeddings & search |
| **AI/LLM** | Google Gemini 1.5 Flash | Natural language processing |
| **Auth** | NextAuth.js | Secure user authentication |
| **Deploy** | Docker + Docker Compose | Containerized deployment |

---

## ✨ Features

### 📖 Core Features
- **Universal Book Upload** - Support for PDF and ePub formats
- **AI-Powered Chat** - Conversation with your books using RAG
- **Smart Summarization** - Automatic chapter and book summaries
- **Personal Library** - Organize and manage your book collection
- **Secure Authentication** - User accounts and book privacy

### 🔮 Coming Soon (Phase 2)
- Multi-language support
- Book sharing & collaboration
- Advanced analytics & reading insights
- Mobile app companion
- Integration with popular reading platforms

---

## ⚡ Quick Start

### One-Command Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/Risad-Raihan/Chaptr-1.1.git
cd Chaptr-1.1

# Copy environment files
cp backend/env_example.txt backend/.env
cp frontend/env_example.txt frontend/.env.local

# 🔥 Start everything with Docker
docker-compose up -d
```

**That's it!** 🎉 Access your app at:
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 📖 **API Docs**: http://localhost:8000/docs

### Prerequisites
- Docker & Docker Compose
- Git

---

## 🛠️ Manual Development Setup

<details>
<summary>Click to expand manual setup instructions</summary>

### Backend Setup
```bash
cd backend
python -m venv venv

# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Prerequisites for Manual Setup
- Node.js 18+
- Python 3.11+
- PostgreSQL (if not using Docker)

</details>

---

## 📁 Project Structure

```
Chaptr-1.1/
├── 🎨 frontend/              # Next.js application
│   ├── src/app/              # App router pages
│   ├── components/           # Reusable UI components
│   └── package.json          # Frontend dependencies
├── ⚙️  backend/              # FastAPI application
│   ├── app/                  # Application code
│   │   ├── models.py         # Database models
│   │   ├── main.py           # FastAPI app entry
│   │   └── config.py         # Configuration
│   └── requirements.txt      # Python dependencies
├── 🐳 docker-compose.yml     # Container orchestration
├── 🗄️  init.sql              # Database initialization
└── 🚀 start-dev.sh           # Development startup script
```

---

## 🔧 Environment Configuration

### Backend Environment (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/chaptr

# AI/LLM
GOOGLE_API_KEY=your_gemini_api_key_here

# Security
SECRET_KEY=your_jwt_secret_key_here

# Vector Database
CHROMA_PERSIST_DIR=./chroma_db
```

### Frontend Environment (.env.local)
```env
# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret_here

# API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> ⚠️ **Important**: Copy the example files and add your actual API keys before running!

---

## 📊 Development Status

### ✅ Phase 1 (Current)
- [x] Project foundation & setup
- [x] Docker containerization
- [x] Database models & migrations
- [x] Basic FastAPI backend structure
- [x] Next.js frontend foundation
- [ ] File upload system
- [ ] Text extraction pipeline
- [ ] RAG implementation
- [ ] Chat interface
- [ ] Book summarization engine
- [ ] User authentication

### 🔮 Phase 2 (Planned)
- [ ] Advanced analytics
- [ ] Social features
- [ ] Mobile responsiveness
- [ ] Performance optimization

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

Built with ❤️ by the Chaptr team.

**Questions?** Open an issue or reach out to the team!

---

<div align="center">

**⭐ If you find this project useful, please give it a star! ⭐**

</div>
 
 