"""Single-file FastAPI application

This file provides a minimal FastAPI app with a single endpoint
that returns a Hello World message. Run with:

    python main.py

or with uvicorn in production:

    uvicorn main:app --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI
import uvicorn


app = FastAPI(title="Hello World API")


@app.get("/", tags=["root"])
async def read_root():
    """Return a simple Hello World message."""
    return {"message": "Welcome to Book of H!"}


if __name__ == "__main__":

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
