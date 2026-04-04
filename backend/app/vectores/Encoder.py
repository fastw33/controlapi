# app/vectores/encoder.py
from typing import Optional
import os
import shutil
import threading
import io
import numpy as np
from PIL import Image, ImageOps
import cv2
from zipfile import BadZipFile


from insightface.app import FaceAnalysis

_APP: Optional[FaceAnalysis] = None
_APP_LOCK = threading.Lock()

_MODEL_ROOT = os.getenv("INSIGHTFACE_HOME", os.path.expanduser("~/.insightface"))
_MODEL_BASE_DIR = os.path.join(_MODEL_ROOT, "models")
_MODEL_DIR = os.path.join(_MODEL_BASE_DIR, "buffalo_l")
_MODEL_ZIP = os.path.join(_MODEL_BASE_DIR, "buffalo_l.zip")


def _cleanup_corrupt_model_cache() -> None:
    """Elimina artefactos del modelo para forzar descarga limpia en el siguiente intento."""
    if os.path.isdir(_MODEL_DIR):
        shutil.rmtree(_MODEL_DIR, ignore_errors=True)
    if os.path.exists(_MODEL_ZIP):
        try:
            os.remove(_MODEL_ZIP)
        except OSError:
            pass

def _get_app() -> FaceAnalysis:
    """
    Inicializa y devuelve una instancia singleton de FaceAnalysis.
    Usa el modelo por defecto 'buffalo_l' (512D, normalizado).
    """
    global _APP
    if _APP is not None:
        return _APP

    with _APP_LOCK:
        if _APP is not None:
            return _APP

        for intento in range(2):
            try:
                app = FaceAnalysis(name="buffalo_l")
                # ctx_id=0 -> CPU; det_size ajusta la resolución del detector
                app.prepare(ctx_id=0, det_size=(640, 640))
                _APP = app
                return _APP
            except BadZipFile:
                if intento == 0:
                    _cleanup_corrupt_model_cache()
                    continue
                raise

    return _APP


def _load_image_fix_orientation(image_bytes: bytes) -> Optional["np.ndarray"]:
    """
    Carga bytes -> PIL -> aplica EXIF transpose -> RGB -> np.ndarray.
    Maneja CMYK, RGBA, etc.
    """
    with Image.open(io.BytesIO(image_bytes)) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode != "RGB":
            im = im.convert("RGB")
        arr = np.asarray(im)
    return arr


def embedding_from_image_bytes(image_bytes: bytes) -> Optional["np.ndarray"]:
    """
    Devuelve embedding float32 (shape (512,)) del rostro principal o None si no detecta.
    Con InsightFace el vector viene normalizado (norma ≈ 1.0) y tiene 512 dimensiones.
    """
    arr = _load_image_fix_orientation(image_bytes)
    if arr is None:
        return None

    # InsightFace trabaja en BGR
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    app = _get_app()
    faces = app.get(bgr)  # detecta rostros y calcula embeddings

    if not faces:
        return None

    # Elegimos el rostro más grande
    def area(face) -> float:
        x1, y1, x2, y2 = face.bbox
        return max(0.0, (x2 - x1)) * max(0.0, (y2 - y1))

    face = max(faces, key=area)

    # Embedding normalizado (512D)
    vec = face.normed_embedding.astype("float32")
    return vec


def bytes_from_embedding(vec: "np.ndarray") -> bytes:
    return vec.tobytes()
