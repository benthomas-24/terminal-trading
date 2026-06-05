import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from routes import account, positions, quote, portfolio

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    secret = os.getenv("PUBLIC_API_SECRET")
    token = os.getenv("PUBLIC_ACCESS_TOKEN")
    if not secret and not token:
        print(
            "FATAL: Set PUBLIC_API_SECRET (and optionally PUBLIC_ACCESS_TOKEN) "
            "in .env or your shell environment.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("Terminal Trading server ready on http://127.0.0.1:8765")
    yield


app = FastAPI(title="Terminal Trading", lifespan=lifespan)

app.include_router(account.router)
app.include_router(positions.router)
app.include_router(quote.router)
app.include_router(portfolio.router)
