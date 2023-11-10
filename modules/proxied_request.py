import requests
import random
from modules import config

def proxied_get(*args, **kwargs):
    return proxied_request('GET', *args, **kwargs)

def proxied_post(*args, **kwargs):
    return proxied_request('POST', *args, **kwargs)

def proxied_request(method, *args, max_retries=3, **kwargs):
    # Pick a proxy to use
    proxy_req = requests.get('https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&anonymity=all')
    proxies = [str(x).strip() for x in proxy_req.text.split('\n') if x.strip()]
    proxies = random.choices(proxies, k=max(max_retries, len(proxies)))
    
    for i in range(max_retries):
        # Try to apply proxy 
        if config.use_proxies and i < len(proxies):
            kwargs['proxies'] = {'http': proxies[i], 'https': proxies[i]}
        
        if config.user_agent:
            kwargs['headers'] = {**kwargs.get('headers',{}), **{'User-Agent': config.user_agent}}
        
        # Try to make the request
        try:
            resp = requests.request(method, *args, **kwargs)
        except Exception as e:
            print(f'Error during request: {e}')
            continue

        # If the request was successful, return the response
        if resp.status_code == 200:
            return resp
        
        # Otherwise, try again
        print(f'Error during request, response: {resp.status_code}')
    # All retries failed
    return None

