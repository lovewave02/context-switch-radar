from fastapi import FastAPI

app = FastAPI(title="Context Switch Radar API")


@app.get("/health")
def health():
    return {"status": "ok"}
