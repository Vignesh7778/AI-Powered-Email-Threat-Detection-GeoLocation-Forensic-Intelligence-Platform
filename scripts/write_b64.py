
import sys
import base64
import os

if len(sys.argv) < 3:
    print('Usage: python write_b64.py <target_path> <base64_content> [--append]')
    sys.exit(1)

target = sys.argv[1]
b64 = sys.argv[2]
append_mode = len(sys.argv) > 3 and sys.argv[3] == '--append'
b64 += '=' * (-len(b64) % 4)
data = base64.b64decode(b64.encode('utf-8'))

os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
mode = 'ab' if append_mode else 'wb'
with open(target, mode) as f:
    f.write(data)

print(f'Successfully wrote {len(data)} bytes to {target} (mode: {mode})')
