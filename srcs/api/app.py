from fastapi import FastAPI
from srcs.api.routers import jobs # Import both

app = FastAPI()

app.include_router(jobs.router) # Your system/data tasks

@app.get("/")
def root():
    """Return the health status of the API."""
    return {"status": "ok"}