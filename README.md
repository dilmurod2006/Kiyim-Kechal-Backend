# FastAPI-E-Commarce
It is a E-Commerce project , made purly by FastAPI backend. it is for the FastAPI tutorial series availbale on Youtube.https://www.youtube.com/playlist?list=PL0BwLgm6AcFZhJehdlez2NZtQ9Kn13OsP

## Running locally (Docker)

```bash
docker compose up --build
```

This starts PostgreSQL, Redis, the FastAPI app, the Celery worker, runs the
database migrations, and automatically seeds the default users, 12 categories
and 100 products (each with an image) below.

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

To re-run the migrations + seeding manually:

```bash
docker compose run --rm migrate
```

## Seed data

On startup the `migrate` service runs `alembic upgrade head` and then `python seed.py`,
which is idempotent (safe to run repeatedly). It seeds:

- **Users** — from `seed_users.json` (see credentials below).
- **Catalogue** — 12 categories and 100 products from `seed_products.json`. Each
  product carries an `image_url` (Unsplash). The `product.image_url` column is added
  by migration `b2f1c4d5e6a7`. Re-running the seed backfills the image on any product
  that already exists, so an already-seeded database is updated in place.

> If you seeded the catalogue before images were added, just run
> `docker compose run --rm migrate` once to apply the new column and image URLs.

## Default login credentials

These accounts are created automatically from `seed_users.json` when the
containers start. Log in via `POST /api/v1/users/token` (form fields:
`username`, `password`).

### Regular user (customer)
- **Username:** `user`
- **Password:** `user12345`

### Admin
- **Username:** `admin`
- **Password:** `admin12345`

> ⚠️ These are default development credentials. Change them before deploying
> anywhere public.
