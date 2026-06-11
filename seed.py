"""
Seed script: populates the database with default data.

Runs automatically inside Docker (see the `migrate` service in compose.yaml),
right after Alembic applies the migrations. Safe to run multiple times —
records that already exist are skipped (idempotent).

Seeds, in order:
  1. Users      from seed_users.json
  2. Categories from seed_products.json ("categories")
  3. Products   from seed_products.json ("products", linked to categories by name)
"""
import os
import json
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from model.models import User, Category, Product
from core.security import get_password_hash

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/fastapi_ecom",
)

BASE_DIR = os.path.dirname(__file__)
USERS_FILE = os.path.join(BASE_DIR, "seed_users.json")
PRODUCTS_FILE = os.path.join(BASE_DIR, "seed_products.json")


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def seed_users(session: AsyncSession) -> None:
    if not os.path.exists(USERS_FILE):
        return
    for u in _load(USERS_FILE):
        username = u["username"]
        role = u.get("role", "customer")
        existing = await session.exec(select(User).where(User.username == username))
        if existing.one_or_none():
            print(f"[seed] User '{username}' already exists — skipping")
            continue
        session.add(
            User(username=username, password=get_password_hash(u["password"]), role=role)
        )
        print(f"[seed] Created user '{username}' (role: {role})")
    await session.commit()


async def seed_categories(session: AsyncSession, names) -> dict:
    """Ensure every category exists; return a {name: id} map."""
    name_to_id = {}
    for name in names:
        existing = await session.exec(select(Category).where(Category.name == name))
        category = existing.one_or_none()
        if category is None:
            category = Category(name=name)
            session.add(category)
            await session.commit()
            await session.refresh(category)
            print(f"[seed] Created category '{name}'")
        else:
            print(f"[seed] Category '{name}' already exists — skipping")
        name_to_id[name] = category.id
    return name_to_id


async def seed_products(session: AsyncSession, products, name_to_id) -> None:
    created = 0
    updated = 0
    for p in products:
        name = p["name"]
        image_url = p.get("image_url")
        existing = await session.exec(select(Product).where(Product.name == name))
        found = existing.first()

        if found is not None:
            # Backfill / refresh the image on products that already exist.
            if image_url and found.image_url != image_url:
                found.image_url = image_url
                session.add(found)
                updated += 1
            continue

        category_id = name_to_id.get(p["category"])
        if category_id is None:
            print(f"[seed] WARNING: category '{p['category']}' missing for '{name}' — skipping")
            continue
        session.add(
            Product(
                name=name,
                description=p["description"],
                price=float(p["price"]),
                image_url=image_url,
                category_id=category_id,
            )
        )
        created += 1
    await session.commit()
    print(
        f"[seed] Products — created {created}, image updated {updated}, "
        f"unchanged {len(products) - created - updated}"
    )


async def seed() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        await seed_users(session)

        if os.path.exists(PRODUCTS_FILE):
            data = _load(PRODUCTS_FILE)
            names = data.get("categories") or sorted({p["category"] for p in data["products"]})
            name_to_id = await seed_categories(session, names)
            await seed_products(session, data["products"], name_to_id)

    await engine.dispose()
    print("[seed] Done.")


if __name__ == "__main__":
    asyncio.run(seed())
