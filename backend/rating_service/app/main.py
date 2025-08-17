from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Rating Service - PagePuff"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rating"}
