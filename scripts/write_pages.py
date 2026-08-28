import os

PAGES = 'frontend/src/pages'
COMP = 'frontend/src/components'
SRC = 'frontend/src'
os.makedirs(PAGES, exist_ok=True)
os.makedirs(COMP, exist_ok=True)

def w(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Wrote {path}')

import base64
def wb64(path, b64str):
    b64str += '=' * (-len(b64str) % 4)
    text = base64.b64decode(b64str.encode('utf-8')).decode('utf-8')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'Wrote {path} ({len(text)} chars)')
