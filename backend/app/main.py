from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health

app = FastAPI(
    title="EU & Ireland Public Services AI Advisor",
    version="0.1.0",
    description="RAG system over Irish government and EU legislative sources.",
)

# Allow the Next.js dev server to call our API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
