# AGENTS GUIDE FOR THE CALCULUS MONOREPO

Purpose: align all autonomous and human contributors on how to build, test, and style both the Next.js client (`calculus-client/`) and the FastAPI server (`server/`). Treat this as ground truth until updated.

## 1. REPO LAYOUT & ENVIRONMENTS
1. Root contains two primary apps: `calculus-client/` (Next.js App Router) and `server/` (FastAPI + async SQLAlchemy).
2. Node 20+ and npm 10+ are recommended; `package-lock.json` is committed so prefer `npm` over other package managers.
3. Python 3.12.3 is pinned via `.python-version`(root + server). The backend uses `uv` for dependency locking (`uv.lock`).
4. Local Postgres (with pgvector) and Redis are required for most backend features. Optional services include MCP, OpenAI, and Qdrant for RAG.
5. No Cursor (`.cursor/rules/`, `.cursorrules`) or Copilot instructions exist today—keep this file updated if that changes.

## 2. DEPENDENCY INSTALLATION
1. Frontend: `cd calculus-client && npm install` (runs once; Turbopack enabled in dev by default).
2. Backend with uv (preferred): `cd server && uv sync` (creates `.venv` if absent).
3. Backend with pip fallback: `python -m venv .venv && source .venv/bin/activate && pip install -e .`.
4. Environment variables: copy `.env.example` if provided (otherwise create `.env`) for both apps. Never commit secrets.
5. Postgres/Redis endpoints come from `POSTGRES_*` and `REDIS_*` vars; scheduler toggles use `RUN_SEMANTIC_SCHEDULER_TEST_ON_STARTUP`, `TRIGGER_SEMANTIC_SYNC_ON_STARTUP`.

## 3. DEV & BUILD COMMANDS
1. Frontend dev server: `npm run dev` (uses Turbopack; falls back to webpack if issues arise as noted in `next.config.ts`).
2. Frontend production build: `npm run build` followed by `npm run start` for preview.
3. Backend live reload (preferred): `cd server && uv run python run.py` (wrapper around Uvicorn with reload + watched dirs).
4. Alternate backend dev: `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
5. Scheduler test harness (manual): `uv run python test_semantic_scheduler.py`—requires seeded episodic data.

## 4. LINTING & TYPE CHECKING
1. Frontend: `npm run lint` (Next.js core-web-vitals config via `eslint.config.mjs`). Fix warnings before committing.
2. TypeScript is `strict`; respect path alias `@/*` per `tsconfig.json`. No implicit `any`, prefer explicit return types in stores/hooks.
3. Backend typing via Pyright: `cd server && uvx pyright` (configured in `pyproject.toml`). Keep `typeCheckingMode = "basic"` compliance; annotate async functions.
4. No automatic formatter is configured. Match existing spacing and semicolon rules (frontend uses standard Prettier-ish style; backend follows Black-like spacing but manual).

## 5. TESTING – FRONTEND (VITEST + RTL)
1. Standard suite: `npm run test` (JS DOM environment, global jest-dom matchers with `src/test/setup.ts`).
2. Watch mode: `npm run test:watch`. UI runner: `npm run test:ui`. Coverage: `npm run test:coverage`.
3. Run a single test file: `npx vitest run src/app/context/__tests__/profile.test.ts`.
4. Run by test name: `npx vitest run src/app/context/__tests__/profile.test.ts -t "should validate a complete and valid profile"`.
5. Vitest auto-imports `@` alias and cleans RTL state via `afterEach(cleanup)`; do not duplicate cleanup logic inside tests.
6. Use `vi.mock` for API modules; provide realistic mock implementations since components/stores expect structured `ApiResult` objects.

## 6. TESTING – BACKEND (PYTEST)
1. Full suite: `cd server && uv run pytest` (asyncio auto mode configured in `pytest.ini`).
2. Single file: `uv run pytest tests/test_auth_helpers.py`.
3. Single test case: `uv run pytest tests/test_auth_helpers.py -k test_get_user_id_with_valid_header`.
4. Keep tests async-aware (`@pytest.mark.asyncio`). Use `httpx.AsyncClient(app=app, base_url="http://test")` for API tests; rely on fixtures defined in each test module.
5. Integration harness for semantic scheduler is interactive; prefer targeted Pytest coverage instead of running the manual script in CI contexts.

## 7. RUNTIME DEPENDENCY NOTES
1. Database engine uses `postgresql+psycopg://` URL assembled in `app/db/my_sql_config.py`. Even though filename says "my_sql", it targets Postgres with pgvector.
2. `create_tables()` enables pgvector and builds HNSW indexes; run once after migrations or when schema changes.
3. Redis is optional but strongly recommended; `app/db/redis_config.py` manages a shared async pool. Use `await get_redis()` via FastAPI `Depends` when needed.
4. JWT helpers live in `app/utils/jwt_utils.py` and rely on `.env` secrets; set `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, etc.
5. MCP client + RAG features depend on external services. Wrap calls in try/except and log warnings rather than failing hard (see `app/main.py`).

## 8. FRONTEND ARCHITECTURE & STYLE
1. Next.js App Router with route groups: e.g., `(homepage)` and `(auth)` directories. Use `"use client"` at the top of client components.
2. Global layout lives under `src/app/layout.tsx`, with `globals.css` limited to reset + tokens. Component styles prefer Tailwind classes; fallback to CSS Modules for layout constraints (see `mainLayout.module.css`).
3. Shared UI pieces live in `src/app/components/`; page-level logic uses slices like `chatPage.tsx`, `helperPage.tsx`, `learningPlanPage.tsx`.
4. State is in Zustand stores under `src/app/context/`. Persisted stores must use `createSSRStorage` to avoid `window` access during SSR.
5. API clients live in `src/app/api/`. All functions return `Promise<ApiResult<T>>`; always `try/catch` and return `{ success: false, error }` rather than throwing.
6. Tokens are stored via cookies (`tokenStore` + `utils/cookies.ts`). Before reading cookies or storage, guard with `typeof window !== 'undefined'`.
7. Imports should follow: Node/React built-ins → external libs → internal `@/` modules → relative paths. Group with blank lines between categories.
8. Naming: use PascalCase for components, camelCase for hooks/utilities, UPPER_SNAKE for constants. Avoid single-letter variables except simple iterators.
9. Error handling: surface human-readable messages (`setError('Login failed')`) and log the raw error with `console.error` for debugging.

## 9. STYLING & ACCESSIBILITY
1. Tailwind utility-first approach; keep class lists organized (layout → spacing → colors → effects). Prefer descriptive containers instead of arbitrary `div` nesting.
2. When CSS Modules are necessary, co-locate `.module.css` files and use BEM-ish names (e.g., `.mainLayout`, `.leftSidebarExpanded`).
3. Keep animations subtle and prefer CSS transitions over JS. Use `prefers-reduced-motion` where motion is non-trivial.
4. Always provide semantic HTML + ARIA labels for buttons, inputs, and nav items. Check keyboard navigation in new UI flows.

## 10. BACKEND ARCHITECTURE & STYLE
1. API routers live under `app/api/**`. Keep HTTP wiring thin: parse inputs via Pydantic schemas, delegate to CRUD/services, convert results back to response models.
2. Database layer: `app/db/crud/**` for SQLAlchemy operations. Always pass `AsyncSession` via FastAPI `Depends(get_db)` and `await db.commit()` / `await db.rollback()` appropriately.
3. Schemas: `app/schemas/pydantic_schemas/**` handle camelCase output expected by the client, even if internal DB columns are snake_case.
4. Utilities (`app/utils`) provide auth helpers, JWT utilities, storage helpers. Avoid circular imports by keeping pure functions there.
5. When raising `HTTPException`, include `status_code`, `detail`, and `headers` where relevant (especially for auth flows).
6. Docstrings: use triple-quoted summaries with Args/Returns/Raises sections (see `auth_api.py`). Keep module-level docstrings describing intent.
7. Logging: prefer `logging.getLogger(__name__)` over `print`, except in bootstrap scripts. When using `print` for dev visibility, prefix with ✅/⚠️/❌ to match existing style.
8. Async patterns: never block inside async routes (no `time.sleep`). Use `asyncio` primitives or background tasks for long-running work.

## 11. DATABASE & MEMORY LAYERS
1. Episodic and semantic memory services live under `app/long_term_memory/`. When editing, keep extractor/processor/scheduler responsibilities separated.
2. `short_term_memory/manager.py` interacts with Redis; maintain TTL values consistent with `MEMORY_TTL_DAYS`.
3. When adding models, import them inside `app/db/create_tables.py` so metadata is registered before `Base.metadata.create_all()` executes.

## 12. TESTING BEST PRACTICES
1. Frontend tests must clean up DOM state; rely on `afterEach(cleanup)` in `src/test/setup.ts` instead of repeating in each file.
2. Backend tests should avoid touching real services. Mock external APIs (OpenAI, Redis) or use dependency overrides in FastAPI when necessary.
3. Keep fixtures in the same file unless reused widely; prefer pytest fixtures returning dicts that mirror actual request bodies (camelCase to match client expectations).
4. For scheduler tests, ensure Postgres + Redis contain sample data; otherwise skip to avoid misleading failures.

## 13. SECURITY & SECRETS
1. Never commit `.env` files or dump credentials in code. `.gitignore` already blocks common secret filenames—double-check before adding new ones.
2. The admin token in `app/utils/auth_helpers.py` is currently hardcoded for dev convenience. If updating, move it to an environment variable and update this doc.
3. Client cookies use `sameSite: 'strict'` and `secure` in production. Preserve these defaults when editing `utils/cookies.ts`.
4. JWT tokens must be cleared on logout flows (`tokenStore.clearToken()` plus store resets). Any new auth surface should follow the same pattern.

## 14. CONTRIBUTION REMINDERS
1. Keep changes scoped. Do not rename files/directories on a whim—other agents rely on predictable paths.
2. Update this `AGENTS.md` whenever build/test/style rules change. note explicitly if Cursor/Copilot instruction files get added.
3. Prefer incremental PRs: run targeted tests (`npm run test -- file`, `uv run pytest path -k name`) before handing off.
4. When adding dependencies, modify `package.json` / `pyproject.toml` and lockfiles (`package-lock.json`, `uv.lock`). Document new commands here.
5. If you find missing automation (formatters, lint rules), propose them via issues or PRs instead of ad-hoc scripts.

Stay consistent, document everything, and keep this guide authoritative for future agents.
