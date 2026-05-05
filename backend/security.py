import os
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "surveillance_secret_key_2024")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(
        status_code=403,
        detail="Unauthorized node: Invalid API Key."
    )
