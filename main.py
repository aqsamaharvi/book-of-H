from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Hello World API")

@app.get("/", tags=["root"])
async def read_root():
    """Return a simple Hello World message."""
    return {"message": "Welcome to Book of H! version2"}


if __name__ == "__main__":

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)