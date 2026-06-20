import io
import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import numpy as np

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

rembg_session = None

def get_rembg():
    global rembg_session
    if rembg_session is None:
        from rembg import new_session
        rembg_session = new_session("u2net")
    return rembg_session

upscale_model = None

def get_upscale():
    global upscale_model
    if upscale_model is None:
        import onnxruntime as ort
        model_path = os.path.join(os.path.dirname(__file__), "models", "realesrgan-x2.onnx")
        if os.path.exists(model_path):
            upscale_model = ort.InferenceSession(model_path)
        else:
            raise RuntimeError("Upscale model not found. Download realesrgan-x2.onnx to server/models/")
    return upscale_model


@app.post("/api/remove-bg")
async def remove_bg(image: UploadFile = File(...)):
    data = await image.read()
    from rembg import remove
    result = remove(data, session=get_rembg())
    return Response(content=result, media_type="image/png")


@app.post("/api/transparent")
async def transparent(image: UploadFile = File(...)):
    data = await image.read()
    from rembg import remove
    result = remove(data, session=get_rembg(), alpha_matting=True)
    return Response(content=result, media_type="image/png")


@app.post("/api/upscale")
async def upscale(
    image: UploadFile = File(...),
    scale: int = Form(2),
):
    data = await image.read()
    img = Image.open(io.BytesIO(data)).convert("RGB")

    try:
        session = get_upscale()
        img_array = np.array(img).astype(np.float32).transpose(2, 0, 1) / 255.0
        img_array = np.expand_dims(img_array, 0)

        input_name = session.get_inputs()[0].name
        result = session.run(None, {input_name: img_array})[0]
        result = (result.clip(0, 1).transpose(1, 2, 0) * 255).astype(np.uint8)
        out = Image.fromarray(result)
    except Exception:
        w, h = img.size
        out = img.resize((w * scale, h * scale), Image.LANCZOS)

    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/api/watermark-remove")
async def watermark_remove(image: UploadFile = File(...)):
    data = await image.read()
    from rembg import remove
    result = remove(data, session=get_rembg(), alpha_matting=True)
    return Response(content=result, media_type="image/png")


@app.post("/api/product-photo")
async def product_photo(
    image: UploadFile = File(...),
    background: str = Form("white"),
):
    data = await image.read()
    from rembg import remove
    from PIL import Image
    import io

    nobg_bytes = remove(data, session=get_rembg())
    nobg_img = Image.open(io.BytesIO(nobg_bytes)).convert("RGBA")

    bg_color = (255, 255, 255) if background == "white" else (240, 240, 240)
    bg = Image.new("RGB", nobg_img.size, bg_color)
    bg.paste(nobg_img, mask=nobg_img.split()[3])

    buf = io.BytesIO()
    bg.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/api/replace-bg")
async def replace_bg(
    image: UploadFile = File(...),
    background: str = Form("white"),
):
    data = await image.read()
    from rembg import remove
    from PIL import Image, ImageDraw
    import io

    nobg_bytes = remove(data, session=get_rembg())
    nobg_img = Image.open(io.BytesIO(nobg_bytes)).convert("RGBA")

    bg = Image.new("RGB", nobg_img.size, (255, 255, 255))
    draw = ImageDraw.Draw(bg)
    w, h = nobg_img.size

    if background == "studio":
        for y in range(h):
            r = int(240 - (y / h) * 40)
            draw.line([(0, y), (w, y)], fill=(r, r, r))
    elif background == "sunset":
        for y in range(h):
            r = int(255 - (y / h) * 100)
            g = int(180 - (y / h) * 180)
            b = int(100 + (y / h) * 155)
            draw.line([(0, y), (w, y)], fill=(r, g, b))
    elif background == "nature":
        for y in range(h):
            r = int(100 + (y / h) * 100)
            g = int(180 - (y / h) * 50)
            b = int(120 + (y / h) * 80)
            draw.line([(0, y), (w, y)], fill=(r, g, b))
    else:
        pass

    bg.paste(nobg_img, mask=nobg_img.split()[3])

    buf = io.BytesIO()
    bg.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/api/restore")
async def restore(image: UploadFile = File(...)):
    data = await image.read()
    from PIL import Image, ImageEnhance, ImageFilter
    import io

    img = Image.open(io.BytesIO(data)).convert("RGB")

    img = img.filter(ImageFilter.SHARPEN)
    img = img.filter(ImageFilter.SMOOTH_MORE)
    img = img.filter(ImageFilter.SHARPEN)

    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2)

    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.3)

    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.05)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)