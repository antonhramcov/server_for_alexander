#!/usr/bin/env python3
"""Set the public HTTPS directory of server/ and generate the T123 block."""
from pathlib import Path
from urllib.parse import urlsplit
import html, json, sys
root = Path(__file__).resolve().parent
if len(sys.argv) != 2:
    raise SystemExit('Usage: python3 configure.py https://YOUR_DOMAIN/PUBLIC_DIRECTORY/')
address = sys.argv[1].rstrip('/') + '/'
url = urlsplit(address)
if (url.scheme != 'https' or not url.hostname or url.username or url.password
        or url.query or url.fragment or any(c.isspace() for c in address)):
    raise SystemExit('Use a public HTTPS directory URL without credentials, query or fragment.')
(root / 'hosting.json').write_text(json.dumps({'baseUrl': address}, indent=2) + '\n', encoding='utf-8')
template = (root / 'frontend/tilda-t123.template.html').read_text(encoding='utf-8')
assert template.count('__SET_HOSTING_URL__') == 1, 'Invalid frontend template'
block = template.replace('__SET_HOSTING_URL__', html.escape(address, quote=True))
for suffix in ['txt', 'html']:
    (root / ('frontend/tilda-t123.' + suffix)).write_text(block, encoding='utf-8')
print('Configured: ' + address)
print('Upload server/ contents, then paste frontend/tilda-t123.txt into one T123 and publish.')
