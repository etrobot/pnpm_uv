# PNPM + UV Demo Project

This is a monorepo demonstrating a fullstack application using pnpm for package management and UV for Python dependency management.

## Project Structure

- `backend/`: Python backend using FastAPI and Uvicorn, with UV for dependency management.
- `frontend/`: React frontend using Vite and pnpm for dependency management.

## Getting Started

### Prerequisites

- Node.js (with pnpm installed)
- Python (with UV installed)

### Installation

1. **Install all dependencies (frontend and backend):**

   ```bash
   pnpm run install:all
   ```

### Running the Development Servers

To run both the frontend and backend development servers concurrently:

```bash
pnpm run dev
```

This will start:
- The backend server (FastAPI/Uvicorn) with auto-reloading.
- The frontend development server (Vite).

### Building the Project

To build both the frontend and backend:

```bash
pnpm run build
```

This will:
- Build the frontend for production.
- (Note: Backend build step is currently a placeholder and not fully implemented.)

---

## Authentication & User Management (Overview)

The project includes a JWT-based authentication system and a simple admin-only user management panel.

### Backend (FastAPI)

- JWT endpoints (under `/api`):
  - `POST /auth/token`: Login with email (username) and password using `application/x-www-form-urlencoded`. Returns `access_token`.
  - `POST /auth/logout`: Stateless logout endpoint (for symmetry).
  - `GET /auth/me`: Returns current user info using `Authorization: Bearer <token>`.
  - `POST /auth/change-password`: Change password for the authenticated user. Body: `{ current_password, new_password }`.
- Admin-only user management endpoints:
  - `GET /users`: List users (id, email, name) — admin only.
  - `POST /users`: Create user — admin only. Body: `{ email, name?, password }`.
  - `DELETE /users/{user_id}`: Delete user — admin only. Prevents deleting `admin@test.com`.
- CORS: Configured for `http://localhost:5173` and `http://127.0.0.1:5173`.
- Admin bootstrap on startup:
  - On app startup, if `INIT_ADMIN` is truthy (default: true), the backend ensures an admin user exists:
    - Email: `admin@test.com`
    - Password: `123456`
    - Name: `Admin User`

### Frontend (React + Vite)

- UI features:
  - Login form (centered vertically and horizontally).
  - Top header displays current user after login.
  - Change Password via a dialog (Radix Dialog component).
  - User Management section (admin only): list, create, delete users. Delete for `admin@test.com` is disabled.
  - All operations (login, logout, change password, create/delete user) show success/error toasts.
- Data fetching:
  - Migrated to TanStack Query for fetching/caching/mutations.
  - Queries:
    - `['me']`: fetches `/api/auth/me` when a token is present.
    - `['users']`: fetches `/api/users` when a token is present AND current user is admin.
  - Mutations:
    - Login: `POST /api/auth/token` — saves token to `localStorage` and invalidates `['me']`.
    - Change password: `POST /api/auth/change-password` — success closes dialog and toasts.
    - Create user: `POST /api/users` — invalidates `['users']`.
    - Delete user: `DELETE /api/users/{id}` — invalidates `['users']`.
  - Token handling:
    - On login, token stored in `localStorage` and used in Authorization headers.
    - On logout, token cleared and QueryClient cache reset.
- UI libraries:
  - `@tanstack/react-query` for data fetching and mutations
  - `@radix-ui/react-dialog` with a thin wrapper under `frontend/app/components/ui/dialog.tsx`
  - `react-hot-toast` for toasts
  - `class-variance-authority`, `tailwind-merge` utilities
- Layout:
  - Login view is fully centered (both axes).
  - Post-login panel is centered with a max width to improve readability.

### Local Development

1. Install dependencies:

   ```bash
   pnpm run install:all
   ```

2. Run both servers:

   ```bash
   pnpm run dev
   ```

3. Open `http://localhost:5173/` and login with:

   - Email: `admin@test.com`
   - Password: `123456`

4. Notes:

   - Set `INIT_ADMIN=false` to disable auto-creation of admin on startup.
   - Non-admin users cannot view or access the User Management module. The backend also enforces admin-only access.
   - Default token expiration is 30 minutes; configurable in `backend/auth.py`.
