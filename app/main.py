from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.pages import router as pages_router
from app.routes.api import router as api_router


app = FastAPI(
    title="Letter Generator",
    description="Official Document Generation System",
    version="1.0.0",
)


# =========================================================
# STATIC FILES
# =========================================================

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

app.mount(
    "/storage",
    StaticFiles(directory="storage"),
    name="storage",
)


# =========================================================
# PAGE ROUTES
# =========================================================

app.include_router(pages_router)
app.include_router(api_router)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "application": "Letter Generator",
    }
