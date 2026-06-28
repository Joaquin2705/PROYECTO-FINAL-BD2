#!/usr/bin/env python3
import base64
import io
import mimetypes
import os
import wave

import httpx

API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Carpeta local con imágenes reales para el seed
IMAGES_DIR = os.environ.get("SEED_IMAGES_DIR", "")

IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif")

# PNG de 1x1 usado cuando no hay imágenes locales
_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


# Arma un WAV corto en memoria para probar el audio player
def _tiny_wav() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"\x00\x00" * 800)
    return buffer.getvalue()


# Lista las imágenes de la carpeta local si existe
def _local_images() -> list[str]:
    if not IMAGES_DIR or not os.path.isdir(IMAGES_DIR):
        return []
    paths = []
    for name in sorted(os.listdir(IMAGES_DIR)):
        if name.lower().endswith(IMAGE_EXT):
            paths.append(os.path.join(IMAGES_DIR, name))
    return paths


def run_query(client: httpx.Client, sql: str) -> dict:
    res = client.post(f"{API_URL}/query", json={"sql": sql})
    res.raise_for_status()
    return res.json()


def upload(client: httpx.Client, name: str, data: bytes, content_type: str) -> dict:
    files = {"file": (name, data, content_type)}
    res = client.post(f"{API_URL}/upload", files=files)
    res.raise_for_status()
    return res.json()


# Sube las imágenes locales y devuelve las filas a insertar
def _seed_from_folder(client: httpx.Client, paths: list[str]) -> list[tuple]:
    rows = []
    for i, path in enumerate(paths, start=1):
        name = os.path.basename(path)
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        with open(path, "rb") as handle:
            upload(client, name, handle.read(), content_type)
        rows.append((i, name))
    return rows


# Sube datos sintéticos y devuelve las filas a insertar
def _seed_synthetic(client: httpx.Client) -> list[tuple]:
    upload(client, "demo.png", _PNG_1X1, "image/png")
    upload(client, "demo.wav", _tiny_wav(), "audio/wav")
    return [(1, "demo.png"), (2, "demo.wav")]


def main() -> None:
    with httpx.Client(timeout=30) as client:
        client.get(f"{API_URL}/health").raise_for_status()

        run_query(client, "CREATE TABLE media (id INT, path TEXT)")
        run_query(client, "CREATE INDEX ON media (id) USING hash")

        images = _local_images()
        rows = _seed_from_folder(client, images) if images else _seed_synthetic(client)

        values = ", ".join(f'({i}, "{name}")' for i, name in rows)
        run_query(client, f"INSERT INTO media (id, path) VALUES {values}")
        result = run_query(client, "SELECT * FROM media")

        print("source:", IMAGES_DIR if images else "synthetic")
        print("columns:", result["columns"])
        for row in result["rows"]:
            print("row:", row)


if __name__ == "__main__":
    main()
