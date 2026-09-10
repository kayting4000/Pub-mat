# pubmat-api

A FastAPI backend for managing publication materials (PubMat) with a dual-database architecture using PostgreSQL and MongoDB.

## Stack

- **FastAPI** + Uvicorn
- **PostgreSQL** via SQLAlchemy (async) + asyncpg
- **MongoDB** via Motor (async)
- **JWT** authentication (python-jose + passlib/bcrypt)
- **Pydantic v2** + pydantic-settings

## Features

- JWT-based auth with role-based access control (`admin`, `editor`, `journalist`, `layout_artist`)
- Draft lifecycle: `draft → submitted → approved/rejected → published`
- Drafts stored in MongoDB with full revision history and comments
- Published articles and pubmat assets stored in PostgreSQL
- Rich pubmat metadata stored in MongoDB

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
SECRET_KEY=your-secret-key
POSTGRES_URL=postgresql+asyncpg://user:password@localhost/pubmat_db
MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=pubmat_drafts_db
```

Run the server:

```bash
uvicorn app.main:app --reload
```

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and get JWT |
| GET | `/users/me` | Get current user |
| GET | `/users` | List all users (admin/editor) |
| PUT | `/users/{id}/role` | Update user role (admin) |
| DELETE | `/users/{id}` | Delete user (admin) |
| GET | `/categories` | List categories |
| POST | `/categories` | Create category (admin/editor) |
| PUT | `/categories/{id}` | Update category (admin/editor) |
| DELETE | `/categories/{id}` | Delete category (admin/editor) |
| POST | `/drafts` | Create draft |
| GET | `/drafts` | List drafts |
| GET | `/drafts/{id}` | Get draft |
| PUT | `/drafts/{id}` | Update draft |
| DELETE | `/drafts/{id}` | Delete draft |
| POST | `/submissions/{id}/submit` | Submit draft for review |
| GET | `/submissions/pending` | List pending drafts (admin/editor) |
| POST | `/submissions/{id}/review` | Approve or reject draft (admin/editor) |
| POST | `/articles/publish` | Publish approved draft (admin/editor) |
| GET | `/articles` | List published articles |
| GET | `/articles/{id}` | Get article |
| DELETE | `/articles/{id}` | Delete article (admin/editor) |
| POST | `/pubmats/attach/{article_id}` | Attach pubmat asset |
| GET | `/pubmats/{article_id}` | Get pubmat assets for article |
