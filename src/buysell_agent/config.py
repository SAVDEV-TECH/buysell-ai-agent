import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    gemini_api_key: str
    model_name: str = "gemini-flash-lite-latest"
    database_url: str = "sqlite:///./buysell.db"
    paystack_secret_key: str = ""  # Set in .env to enable real payment links
    whatsapp_token: str = ""                    # Meta Cloud API access token
    whatsapp_phone_number_id: str = ""          # Phone Number ID from Meta dashboard
    whatsapp_business_account_id: str = ""      # WhatsApp Business Account ID
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

# Ensure the underlying SDKs can see the API key
os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
