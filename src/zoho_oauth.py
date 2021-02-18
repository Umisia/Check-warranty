import requests
import json
from logger import Logger
import config

def refresh_token(token):
    pars = {
        'refresh_token': token,
        'client_id': config.client_id,
        'client_secret': config.client_secret,
        'redirect_uri': 'http://localhost:8080/',
        'grant_type': 'refresh_token'}
    resp = requests.post("https://accounts.zoho.com/oauth/v2/token", params=pars)
    json_data = json.loads(resp.text)
    access_toks_refreshed = json_data["access_token"]
    log.info(f"status_code: {resp.status_code}")
    log.debug(access_toks_refreshed)
    return access_toks_refreshed

log = Logger(__name__).logger

