#!/usr/bin/env python3.6
import sys
from pathlib import Path
import secrets


def ensure(path: Path):
    secret_path = Path(path)

    try:
        secret_key = secret_path.read_text()
    except FileNotFoundError:
        print('secret_key.txt not found, generating')
        secret_key = secrets.token_hex()
        secret_path.write_text(secret_key)

    return secret_key


if __name__ == '__main__':
    if sys.argv[1] == 'ensure':
        ensure(sys.argv[2])
