from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from .models import GoogleCredential
import json

def get_credentials_for_user(user):
    try:
        g = GoogleCredential.objects.get(user=user)
    except GoogleCredential.DoesNotExist:
        return None
    
    info = g.as_dict()
    creds = Credentials(
        token=info['token'],
        refresh_token=info.get('refresh_token'),
        token_uri=info['token_uri'],
        client_id=info['client_id'],
        client_secret=info['client_secret'],
        scopes=json.loads(g.scopes) if g.scopes else None
    )
    if not creds.valid:
        request = Request()
        creds.refresh(request)

        g.token = creds.token
        if creds.refresh_token:
            g.refresh_token = creds.refresh_token
        g.expiry = creds.expiry
        g.save(update_fields=['token', 'refresh_token', 'expiry', 'updated_at'])

    return creds