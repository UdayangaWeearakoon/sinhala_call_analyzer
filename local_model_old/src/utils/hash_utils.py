import hashlib


def generate_sha256_hash(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()
