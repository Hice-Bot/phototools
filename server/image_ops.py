from __future__ import annotations

import asyncio
import base64
import io
import logging
import os
from dataclasses import dataclass
from typing import Literal

import numpy as np
from fastapi import HTTPException, UploadFile
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError

logger = logging.getLogger("phototools.image_ops")

PUBLIC_MAX_UPLOAD_BYTES = int(os.getenv("PHOTO_TOOLS_PUBLIC_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
PAID_MAX_UPLOAD_BYTES = int(os.getenv("PHOTO_TOOLS_PAID_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
MAX_INPUT_PIXELS = int(os.getenv("PHOTO_TOOLS_MAX_INPUT_PIXELS", "20000000"))
MAX_OUTPUT_PIXELS = int(os.getenv("PHOTO_TOOLS_MAX_OUTPUT_PIXELS", "64000000"))
MAX_CONCURRENT_JOBS = int(os.getenv("PHOTO_TOOLS_MAX_CONCURRENT_JOBS", "2"))

Image.MAX_IMAGE_PIXELS = MAX_INPUT_PIXELS * 2
_job_sem = asyncio.Semaphore(MAX_CONCURRENT_JOBS)
_rembg_session = None
_upscale_model = None


@dataclass
class ImageResult:
    data: bytes
    mime: str = "image/png"
    mode: str = "processed"
    width: int | None = None
    height: int | None = None


async def read_upload_limited(upload: UploadFile, max_bytes: int = PUBLIC_MAX_UPLOAD_BYTES) -> bytes:
    total = 0
    chunks: list[bytes] = []
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status_code=413, detail=f"Image is larger than {max_bytes // 1024 // 1024} MB")
        chunks.append(chunk)
    if not chunks:
        raise HTTPException(status_code=400, detail="No image uploaded")
    return b"".join(chunks)


def validate_scale(scale: int) -> int:
    if scale not in (2, 4):
        raise HTTPException(status_code=400, detail="Scale must be 2 or 4")
    return scale


def load_image(data: bytes, mode: Literal["RGB", "RGBA"] = "RGB") -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        img = Image.open(io.BytesIO(data))
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=400, detail="Invalid or unsupported image") from exc

    width, height = img.size
    if width <= 0 or height <= 0:
        raise HTTPException(status_code=400, detail="Invalid image dimensions")
    if width * height > MAX_INPUT_PIXELS:
        raise HTTPException(status_code=413, detail=f"Image exceeds {MAX_INPUT_PIXELS:,} pixels")
    return ImageOps.exif_transpose(img).convert(mode)


def ensure_output_pixels(width: int, height: int) -> None:
    if width * height > MAX_OUTPUT_PIXELS:
        raise HTTPException(status_code=413, detail=f"Output would exceed {MAX_OUTPUT_PIXELS:,} pixels")


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _get_rembg():
    global _rembg_session
    if _rembg_session is None:
        from rembg import new_session

        _rembg_session = new_session("u2net")
    return _rembg_session


def _upscale_model_path() -> str:
    return os.getenv(
        "PHOTO_TOOLS_UPSCALE_MODEL",
        os.path.join(os.path.dirname(__file__), "models", "realesrgan-x2.onnx"),
    )


def _get_upscale():
    global _upscale_model
    if _upscale_model is None:
        model_path = _upscale_model_path()
        if not os.path.exists(model_path):
            return None
        import onnxruntime as ort

        _upscale_model = ort.InferenceSession(model_path)
    return _upscale_model


async def remove_background_bytes(data: bytes, alpha_matting: bool = False) -> ImageResult:
    async with _job_sem:
        from rembg import remove

        result = remove(data, session=_get_rembg(), alpha_matting=alpha_matting)
    img = load_image(result, "RGBA")
    return ImageResult(data=result, mode="background-removed", width=img.width, height=img.height)


async def upscale_bytes(data: bytes, scale: int = 2) -> ImageResult:
    scale = validate_scale(int(scale))
    img = load_image(data, "RGB")
    ensure_output_pixels(img.width * scale, img.height * scale)

    session = _get_upscale()
    if session is None:
        out = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
        return ImageResult(data=png_bytes(out), mode="basic-resize", width=out.width, height=out.height)

    async with _job_sem:
        try:
            img_array = np.array(img).astype(np.float32).transpose(2, 0, 1) / 255.0
            img_array = np.expand_dims(img_array, 0)
            input_name = session.get_inputs()[0].name
            result = session.run(None, {input_name: img_array})[0]
            if result.ndim == 4:
                result = result[0]
            result = (result.clip(0, 1).transpose(1, 2, 0) * 255).astype(np.uint8)
            out = Image.fromarray(result)
        except Exception as exc:
            logger.exception("AI upscale failed")
            raise HTTPException(status_code=500, detail="Upscale processing failed") from exc

    ensure_output_pixels(out.width, out.height)
    return ImageResult(data=png_bytes(out), mode="ai-upscale", width=out.width, height=out.height)


async def product_photo_bytes(data: bytes, background: str = "white") -> ImageResult:
    cutout = await remove_background_bytes(data)
    nobg_img = load_image(cutout.data, "RGBA")
    bg_color = (255, 255, 255) if background == "white" else (240, 240, 240)
    bg = Image.new("RGB", nobg_img.size, bg_color)
    bg.paste(nobg_img, mask=nobg_img.split()[3])
    return ImageResult(data=png_bytes(bg), mode="product-photo", width=bg.width, height=bg.height)


async def replace_bg_bytes(data: bytes, background: str = "white") -> ImageResult:
    cutout = await remove_background_bytes(data)
    nobg_img = load_image(cutout.data, "RGBA")
    bg = Image.new("RGB", nobg_img.size, (255, 255, 255))
    draw = ImageDrawProxy(bg)
    draw.fill_preset(background)
    bg.paste(nobg_img, mask=nobg_img.split()[3])
    return ImageResult(data=png_bytes(bg), mode="replace-bg", width=bg.width, height=bg.height)


class ImageDrawProxy:
    def __init__(self, img: Image.Image):
        from PIL import ImageDraw

        self.img = img
        self.draw = ImageDraw.Draw(img)

    def fill_preset(self, background: str) -> None:
        width, height = self.img.size
        if background == "studio":
            for y in range(height):
                r = int(240 - (y / height) * 40)
                self.draw.line([(0, y), (width, y)], fill=(r, r, r))
        elif background == "sunset":
            for y in range(height):
                r = int(255 - (y / height) * 100)
                g = int(180 - (y / height) * 180)
                b = int(100 + (y / height) * 155)
                self.draw.line([(0, y), (width, y)], fill=(r, g, b))
        elif background == "nature":
            for y in range(height):
                r = int(100 + (y / height) * 100)
                g = int(180 - (y / height) * 50)
                b = int(120 + (y / height) * 80)
                self.draw.line([(0, y), (width, y)], fill=(r, g, b))


async def restore_bytes(data: bytes) -> ImageResult:
    img = load_image(data, "RGB")
    async with _job_sem:
        img = img.filter(ImageFilter.SHARPEN)
        img = img.filter(ImageFilter.SMOOTH_MORE)
        img = img.filter(ImageFilter.SHARPEN)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = ImageEnhance.Color(img).enhance(1.3)
        img = ImageEnhance.Brightness(img).enhance(1.05)
    return ImageResult(data=png_bytes(img), mode="restore", width=img.width, height=img.height)


async def strip_metadata_bytes(data: bytes) -> ImageResult:
    img = load_image(data, "RGBA")
    return ImageResult(data=png_bytes(img), mode="metadata-stripped", width=img.width, height=img.height)


def result_to_base64(result: ImageResult) -> dict:
    return {
        "image_base64": base64.b64encode(result.data).decode("ascii"),
        "mime": result.mime,
        "mode": result.mode,
        "width": result.width,
        "height": result.height,
    }


def base64_to_bytes(image_base64: str) -> bytes:
    try:
        if "," in image_base64 and image_base64.split(",", 1)[0].startswith("data:"):
            image_base64 = image_base64.split(",", 1)[1]
        return base64.b64decode(image_base64, validate=True)
    except Exception as exc:
        raise ValueError("image_base64 must be valid base64 image data") from exc
