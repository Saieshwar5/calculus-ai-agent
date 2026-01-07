# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Calculus is a full-stack AI learning assistant platform with episodic and semantic memory capabilities. The monorepo contains a Next.js frontend (`calculus-client/`) and FastAPI backend (`server/`) designed to provide personalized learning experiences through contextual conversations.

## Common Commands

### Frontend (calculus-client/)
```bash
# Development
cd calculus-client
npm install              # Install dependencies
npm run dev              # Start dev server with Turbopack (http://localhost:3000)
npm run build            # Production build
npm run start            # Preview production build

# Testing
npm run test                     # Run all tests with Vitest
npm run test:watch               # Watch mode
npm run test:ui                  # UI runner
npm run test:coverage            # Coverage report
npx vitest run path/to/test.ts   # Run specific test file
npx vitest run path/to/test.ts -t "test name"  # Run specific test by name

# Linting
npm run lint             # ESLint with Next.js config
```

### Backend (server/)
```bash
# Setup
cd server
uv sync                  # Install dependencies (creates .venv)
# OR: python -m venv .venv && source .venv/bin/activate && pip install -e .

# Development
uv run python run.py     # Start server with hot reload (http://localhost:8000)
# OR: uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Testing
uv run pytest                                    # Run all tests
uv run pytest tests/test_auth_helpers.py         # Run specific file
uv run pytest tests/test_auth_helpers.py -k test_get_user_id_with_valid_header  # Run specific test
uv run python test_semantic_scheduler.py         # Interactive scheduler test (requires seeded data)

# Type checking
uvx pyright              # Type check with Pyright (config in pyproject.toml)
```

## Architecture Overview

### Frontend Architecture

**Stack**: Next.js 15 (App Router) + React 19 + TypeScript + Tailwind CSS + Zustand

**Directory Structure**:
- `src/app/(homepage)/` - Main authenticated routes (chat, learning plans)
- `src/app/(auth)/` - Authentication routes (login, signup, onboarding)
- `src/app/components/` - Reusable UI components
- `src/app/context/` - Zustand stores for global state management
- `src/app/api/` - API client functions (all return `ApiResult<T>`)
- `src/app/utils/` - Utilities (cookies, helpers)
- `src/test/` - Test setup and utilities

**Key State Management Pattern**:
All stores use Zustand with SSR-safe persistence via `createSSRStorage`. Stores include:
- `auth.tsx` - Authentication state, JWT token management
- `profileStore.tsx` - User profile data
- `chat.tsx` - Chat messages and conversation state
- `learningPreferenceContext.tsx` - Learning preferences
- `learningPlan.tsx` - Learning plan state
- `queriesStore.tsx` - Query history
- `buttonsStore.tsx` - UI button states

**API Client Pattern**:
All API functions return `Promise<ApiResult<T>>` where:
```typescript
type ApiResult<T> =
  | { success: true; data: T }
  | { success: false; error: string }
```
Never throw errors—always catch and return structured error results.

**Authentication Flow**:
- JWT tokens stored in cookies via `tokenStore` and `utils/cookies.ts`
- Guards require `typeof window !== 'undefined'` checks
- Token refresh handled in API client interceptors

### Backend Architecture

**Stack**: FastAPI + SQLAlchemy (async) + PostgreSQL (with pgvector) + Redis

**Directory Structure**:
- `app/main.py` - FastAPI app initialization, startup/shutdown lifecycle
- `app/api/` - API route handlers organized by feature (auth, chat, profile, etc.)
- `app/db/` - Database configuration and CRUD operations
  - `my_sql_config.py` - PostgreSQL async session config (despite name)
  - `create_tables.py` - Table initialization with pgvector extension
  - `crud/` - Database operations organized by domain
- `app/models/` - SQLAlchemy ORM models
- `app/schemas/` - Pydantic models for request/response validation
- `app/core/` - Core business logic
- `app/services/` - Service layer for complex operations
- `app/utils/` - Utilities (JWT, auth helpers, storage)
- `app/long_term_memory/` - Episodic and semantic memory processing
  - `episodic/` - Short-term conversation memory
  - `semantic/` - Long-term extracted insights (runs on scheduler)
- `app/short_term_memory/` - Redis-backed temporary memory
- `app/mcp/` - MCP client for web search integration

**Memory System Architecture**:
The backend implements a three-tier memory system:
1. **Short-term Memory** (Redis): Temporary conversation context with TTL
2. **Episodic Memory** (PostgreSQL): Raw conversation history with timestamps
3. **Semantic Memory** (PostgreSQL + pgvector): Extracted insights and patterns, synced via nightly scheduler

The semantic scheduler (`app/long_term_memory/semantic/scheduler.py`) processes unprocessed episodes at midnight. Can be triggered manually for testing.

**Database Layer Pattern**:
- All database operations use `AsyncSession` via `Depends(get_db)`
- Always `await db.commit()` or `await db.rollback()` within transaction scope
- CRUD functions live in `app/db/crud/` and are imported by API routes

**API Route Pattern**:
1. Parse request via Pydantic schema
2. Extract user ID from JWT via `get_user_id_or_error(request)`
3. Delegate to CRUD/service layer with `AsyncSession`
4. Convert DB models to response schemas (camelCase for frontend)
5. Return FastAPI response or raise `HTTPException`

**Authentication**:
- JWT-based auth with utilities in `app/utils/jwt_utils.py`
- Helper functions in `app/utils/auth_helpers.py` extract user IDs from requests
- Environment variables: `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`

## Critical Integration Points

### Frontend ↔ Backend Communication
- Frontend expects camelCase; backend internal DB uses snake_case
- Pydantic schemas in `app/schemas/` handle transformation via `alias_generator`
- CORS configured in `app/main.py` (currently allows all origins for development)

### Database Schema
- PostgreSQL with pgvector extension for semantic embeddings
- HNSW indexes created in `create_tables()` for vector similarity search
- Connection string format: `postgresql+psycopg://...` (assembled in `my_sql_config.py`)

### External Dependencies
- **PostgreSQL**: Required for all database operations
- **Redis**: Required for short-term memory features
- **OpenAI API**: Required for AI chat and semantic extraction
- **MCP Client**: Optional, enables web search capabilities
- **Qdrant**: Optional, for RAG document search features

### Environment Variables
Both frontend and backend require `.env` files. Key variables:
- Backend: `POSTGRES_*`, `REDIS_*`, `JWT_SECRET_KEY`, `OPENAI_API_KEY`, scheduler toggles
- Frontend: API endpoint URLs, feature flags

## Development Workflow Notes

**Adding New API Endpoints**:
1. Create route handler in appropriate `app/api/*/` directory
2. Define Pydantic request/response schemas in `app/schemas/`
3. Implement CRUD operations in `app/db/crud/`
4. Add ORM model in `app/models/` if new table needed
5. Import model in `app/db/create_tables.py` to register with metadata
6. Create frontend API client function in `src/app/api/` returning `ApiResult<T>`
7. Add tests in `tests/` (backend) and `src/app/context/__tests__/` (frontend)

**Working with Memory Systems**:
- Episodic memory stores raw conversations immediately
- Semantic extraction runs nightly via APScheduler (configurable in startup)
- Manual trigger: Set `TRIGGER_SEMANTIC_SYNC_ON_STARTUP=true` in `.env`
- Test semantic scheduler: `uv run python test_semantic_scheduler.py`

**Testing Guidelines**:
- Frontend: Vitest with React Testing Library, use `vi.mock` for API modules
- Backend: pytest with asyncio, use `httpx.AsyncClient` for API integration tests
- Mock external services (OpenAI, Redis) in tests to avoid real API calls
- Test fixtures should mirror actual request/response shapes

**Database Migrations**:
Currently using `create_tables()` for schema management. After model changes:
1. Update ORM models in `app/models/`
2. Import in `create_tables.py`
3. Run startup to apply changes (destructive in dev, needs migration strategy for prod)

## Key Dependencies & Versions

- **Frontend**: Next.js 15.3.4, React 19, TypeScript 5, Zustand 5, Vitest 1
- **Backend**: Python 3.12.3, FastAPI 0.127+, SQLAlchemy 2.0+, Pydantic 2.x
- **Database**: PostgreSQL with pgvector extension
- **Package Managers**: npm (frontend), uv (backend preferred)

## Important Notes

- The file `app/db/my_sql_config.py` is misnamed—it configures PostgreSQL, not MySQL
- Turbopack is enabled by default for frontend dev; falls back to webpack if issues arise
- No automatic formatter configured; match existing code style manually
- JWT tokens have hardcoded admin token for dev (see `auth_helpers.py`)—move to env var for production
- Scheduler runs at midnight; use env toggles for startup testing
- Always check `typeof window !== 'undefined'` before accessing browser APIs in frontend
