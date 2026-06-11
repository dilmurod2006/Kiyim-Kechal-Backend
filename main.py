# main.py
import os
from fastapi import FastAPI, Request, status
from api import user, product, category, review, basic_background, background_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


# Create the main FastAPI application instance.
# The metadata parameters like title, description, etc., are optional
# and primarily used for the automatic API documentation.
app = FastAPI()

async def validation_exception_handler(request: Request, exc:RequestValidationError):
    friendly_error = []
    for error_details in exc.errors():
        where_it_is = "->".join(str(part) for part in error_details["loc"])
        what_went_wrong = error_details["msg"]
        friendly_error.append({"field": where_it_is, "message": what_went_wrong})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"validation_issues":friendly_error}
    )

app.add_exception_handler(RequestValidationError, validation_exception_handler)
# --- Include API Routers ---
# Connect the modular endpoint files from the /api directory to the main app.
app.include_router(user.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(category.router, prefix="/api/v1/categories", tags=["Categories"])
app.include_router(product.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(review.router, prefix="/api/v1/reviews", tags=["Reviews"])
app.include_router(basic_background.router, prefix="/api/v1/background", tags=["Background Tasks"])
app.include_router(background_status.router, prefix="/api/v1/order_status", tags=["Order Status"])

# --- CORS ---
# Local dev/preview on ANY localhost port is always allowed (regex below).
# Extra production origins (your domain) come from the CORS_ORIGINS env var,
# a comma-separated list, e.g.:
#   CORS_ORIGINS=https://myshop.com,https://www.myshop.com
# Set CORS_ORIGINS=* to allow every origin (note: this disables credentials,
# which is fine here because auth uses a Bearer token, not cookies).
_cors_env = os.getenv("CORS_ORIGINS", "").strip()

if _cors_env == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    default_origins = [
        # Local dev / preview
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        # Production frontend domains (no trailing slash — must match the
        # browser's Origin header exactly)
        "http://kiyimlar-pro-uzb.gastro-analytics.uz",
        "http://kiyim-kechak-pro.gastro-analytics.uz",
        "http://prokiyim.gastro-analytics.uz",
    ]
    extra_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=default_origins + extra_origins,
        # Allow any localhost/127.0.0.1 port, plus any http/https subdomain of
        # gastro-analytics.uz (covers all current and future store domains).
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|https?://([a-z0-9-]+\.)*gastro-analytics\.uz",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/", tags=["Root"])
def read_root():
    """
    A simple root endpoint to confirm that the API is running.
    """
    return {"message": "Welcome to the E-commerce API!"}

# To run this application:
# 1. Make sure you are in the root directory of your project.
# 2. Run the command: uvicorn main:app --reload
