from fastapi import FastAPI
from srcs.app.routers import jobs # Import both

app = FastAPI()

app.include_router(jobs.router) # Your system/data tasks
