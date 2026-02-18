from pydantic import BaseModel
import os

class Settings(BaseModel):
    app_name: str = "TensorMarketData"
    env: str = os.getenv("ENV", "dev")
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-prod")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./tmd.db")
    
    # Stripe (optional; stub-friendly)
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_price_a: str = os.getenv("STRIPE_PRICE_A", "")
    stripe_price_b: str = os.getenv("STRIPE_PRICE_B", "")
    stripe_price_c: str = os.getenv("STRIPE_PRICE_C", "")
    
    # Email (optional; stub-friendly)
    send_from_email: str = os.getenv("SEND_FROM_EMAIL", "nova@tensormarketdata.com")
    support_email: str = os.getenv("SUPPORT_EMAIL", "nova@tensormarketdata.com")
    
    # Ops token for cron
    ops_token: str = os.getenv("OPS_TOKEN", "")

settings = Settings()
