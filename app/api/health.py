from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {
        "service": "GPTunnel Proxy",
        "status": "active",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/health"
        }
    }

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
