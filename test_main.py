from fastapi import FastAPI

# Minimal FastAPI app for testing
app = FastAPI(title="Test API")

@app.get("/")
async def root():
    return {"message": "Hello from Vercel!", "status": "working"}

@app.get("/test")
async def test():
    return {"test": "success", "framework": "fastapi"}

# Vercel handler
handler = app
