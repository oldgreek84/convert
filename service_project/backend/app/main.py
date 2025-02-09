from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_origins=["*"],  # Replace "*" with the frontend URL for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/api")
async def api_root():
    return {"message": "API v1.1"}
