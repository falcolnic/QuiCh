# QuiCh: Quick Search Application

## Overview
**QuiCh** is a semantic search application designed to extract and display insightful information from video transcripts. It leverages **FastAPI** for the backend, **SQLite** for the database, and advanced **AI models** for embedding and processing transcripts. The application is built to handle large-scale video data, process transcripts, and provide meaningful search results to users.

### Features

1. **Semantic Search**:
   - Users can search for ideas, insights, and key information across video transcripts.
   - Results are ranked based on relevance using vector embeddings.

2. **Transcript Processing**:
   - Automatically fetches and processes YouTube video transcripts.
   - Splits transcripts into meaningful chunks for better searchability.

3. **AI-Powered Insights**:
   - Extracts key ideas and insights from transcripts using AI models like Anthropic Claude.
   - Generates embeddings for semantic similarity.

4. **User Authentication**:
   - Secure user signup and login using hashed passwords and JWT-based authentication.

5. **Database Management**:
   - Uses SQLite with SQLAlchemy for efficient data storage and retrieval.
   - Supports migrations using Alembic.

6. **Responsive UI**:
   - Clean and modern interface built with Jinja2 templates and Bootstrap.

### Project Structure

```
QuiCh/
├── app/
│   ├── alembic/                # Database migrations
│   ├── api/                    # API routes and dependencies
│   ├── auth/                   # Authentication logic
│   ├── models/                 # Database models
│   ├── schemas/                # Pydantic schemas for validation
│   ├── scripts/                # Utility scripts for data processing
│   ├── services/               # Core business logic and AI integrations
│   ├── static/                 # Static files (CSS, JS, images)
│   ├── templates/              # Jinja2 templates for the UI
│   ├── config.py               # Application configuration
│   ├── database.py             # Database setup and session management
│   ├── main.py                 # FastAPI application entry point
│   └── jinja_setup.py          # Jinja2 setup for FastAPI
├── Dockerfile                  # Docker configuration
├── pyproject.toml              # Poetry dependencies
├── fly.toml                    # Fly.io deployment configuration
├── README.md                   # Project documentation
└── .github/workflows/fly.yml   # GitHub Actions for CI/CD
```

---

## Installation

### Prerequisites

- **Python 3.11**
- **Docker** (optional for containerized deployment)
- **Poetry** (for dependency management)

### Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/QuiCh.git
   cd QuiCh
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Initialize the database**:
   ```bash
   poetry run alembic upgrade head
   ```

4. **Run the application**:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

5. **Access the application**:
   Open your browser and navigate to [http://localhost:8000](http://localhost:8000).

---

## Running with Docker

1. **Build the Docker image**:
   ```bash
   docker build -t quich .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 quich
   ```

---

## Deployment on Fly.io

The project is configured for deployment on **Fly.io**. Use the following command to deploy:

```bash
fly deploy --remote-only
```
---

## Contributing

1. **Fork the repository**.
2. **Create a new branch** for your feature or bug fix.
3. **Submit a pull request** with a detailed description of your changes.

---

## License

This project is licensed under the **MIT License**.



