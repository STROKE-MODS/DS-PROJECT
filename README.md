# InternAI

InternAI is an AI-powered internship recommendation engine for college students. **Phase 0** establishes the project foundation and verifies frontend-to-backend communication.

## Tech stack

- **Frontend:** React, Vite, and Tailwind CSS
- **Backend:** FastAPI, Uvicorn, SQLAlchemy, and psycopg2
- **Configuration:** `pydantic-settings` and environment variables
- **Database:** PostgreSQL (connected locally by the developer)

## Project structure

```text
internai/
├── frontend/                 # Vite + React + Tailwind application
├── backend/
│   ├── app/
│   │   ├── api/              # API routes (future phases)
│   │   ├── models/           # ORM models (future phases)
│   │   ├── schemas/          # API schemas (future phases)
│   │   ├── services/         # Application services (future phases)
│   │   ├── recommendation/   # Recommendation logic (future phases)
│   │   ├── nlp/              # NLP features (future phases)
│   │   ├── resume/           # Resume features (future phases)
│   │   ├── career/           # Career alignment (future phases)
│   │   └── core/             # Settings and database setup
│   ├── requirements.txt
│   └── .env.example
├── data/                     # Project data (future phases)
├── docs/                     # Project documentation
├── tests/                    # Automated tests
└── README.md
```

## Setup

### Backend

1. Change into the backend directory and create a virtual environment:

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

2. Copy the environment template and set the PostgreSQL connection string to your own local database credentials and database name:

   ```bash
   cp .env.example .env
   ```

   Update `DATABASE_URL` in `.env`, for example:

   ```text
   DATABASE_URL=postgresql://user:password@localhost:5432/internai_db
   ENVIRONMENT=development
   CORS_ORIGINS=http://localhost:5173
   ```

3. Start the API from `backend/`:

   ```bash
   uvicorn app.main:app --reload
   ```

   The health endpoint is available at [http://localhost:8000/api/health](http://localhost:8000/api/health). It returns API status and whether the database connectivity check succeeded. Phase 0 does not create tables, migrations, or seed data.

### Frontend

1. In a second terminal, change into the frontend directory and install dependencies:

   ```bash
   cd frontend
   npm install
   cp .env.example .env
   ```

2. Confirm `VITE_API_BASE_URL` in `.env` points to the backend (the default is `http://localhost:8000`), then start the development server:

   ```bash
   npm run dev
   ```

3. Open [http://localhost:5173](http://localhost:5173). The landing page calls `/api/health` on load and displays **Backend Connected** when the API responds with `{"status":"ok"}`, or **Backend Disconnected** when the request fails.

## Phase 0 scope

This phase intentionally contains no database models, migrations, recommendation logic, resume parsing, NLP, authentication, or additional pages.
