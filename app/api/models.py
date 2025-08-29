from fastapi import APIRouter, HTTPException
import logging
import time
from app.services.gptunnel import GPTunnelService
from app.schemas.model import ModelsResponse

router = APIRouter()
logger = logging.getLogger(__name__)
gptunnel_service = GPTunnelService()

# Кэш для моделей (обновляется каждые 5 минут)
models_cache = {"data": None, "timestamp": 0}

@router.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    """
    Получает и проксирует список доступных моделей из GPTunnel
    """
    try:
        current_time = time.time()

        # Проверяем кэш (обновляем каждые 5 минут)
        if models_cache["data"] and (current_time - models_cache["timestamp"]) < 300:
            logger.info("Returning cached models list")
            return models_cache["data"]

        # Получаем свежий список моделей
        logger.info("Fetching fresh models list from GPTunnel")
        models = await gptunnel_service.get_models()

        # Обновляем кэш
        models_cache["data"] = models
        models_cache["timestamp"] = current_time

        logger.info(f"Successfully fetched {len(models.data)} models")
        return models

    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        # Возвращаем кэшированные данные, если они есть
        if models_cache["data"]:
            logger.info("Returning cached models due to error")
            return models_cache["data"]
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """
    Получает информацию о конкретной модели
    """
    try:
        models = await list_models()
        for model in models.data:
            if model.id == model_id:
                return model
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching model {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
