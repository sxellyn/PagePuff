from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Recommendation Service - PagePuff"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "recommendation"}
