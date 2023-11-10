import yaml
from anyascii import anyascii

def normalize_str(_str) -> str:
    _str = anyascii(_str)
    _str = _str.lower()
    _str = _str.replace(' ', '_')
    _str = _str.replace('-', '_')
    return _str

with open('config-priv.yml', 'r') as file:
    raw_cfg = yaml.safe_load(file)
    for k, v in raw_cfg.items():
        if str(v).startswith('your_'):
            print(f'Please change {k} in config.yml')
            exit(1)
        
        globals()[normalize_str(k)] = v