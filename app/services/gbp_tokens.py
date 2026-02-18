from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.models import GBPCredential
from app.services.gbp_client import decrypt_refresh_token, refresh_access_token

def get_fresh_access_token(session: Session, business_id: int) -> str:
    cred = session.exec(select(GBPCredential).where(GBPCredential.business_id == business_id)).first()
    if not cred:
        return ""
    
    refresh_tok = decrypt_refresh_token(cred.refresh_token_enc)
    if not refresh_tok:
        return ""
    
    tok = refresh_access_token(refresh_tok)
    access = tok.get("access_token", "")
    if not access:
        return ""
    
    cred.access_token = access
    expires_in = int(tok.get("expires_in", 3600))
    cred.token_expiry_utc = datetime.utcnow() + timedelta(seconds=expires_in)
    cred.updated_at = datetime.utcnow()
    session.add(cred)
    session.commit()
    return access
