from fastapi import Depends, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from auth import allowed_origins, clerk_health, pricing_payload, require_paid_api_access
from image_ops import (
    PAID_MAX_UPLOAD_BYTES,
    PUBLIC_MAX_UPLOAD_BYTES,
    ImageResult,
    product_photo_bytes,
    read_upload_limited,
    remove_background_bytes,
    replace_bg_bytes,
    restore_bytes,
    strip_metadata_bytes,
    upscale_bytes,
)

app = FastAPI(title="PhotoTools API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-PhotoTools-API-Key"],
    expose_headers=["X-PhotoTools-Mode", "X-PhotoTools-Width", "X-PhotoTools-Height"],
)


def image_response(result: ImageResult) -> Response:
    return Response(
        content=result.data,
        media_type=result.mime,
        headers={
            "X-PhotoTools-Mode": result.mode,
            "X-PhotoTools-Width": str(result.width or ""),
            "X-PhotoTools-Height": str(result.height or ""),
        },
    )


@app.post("/api/remove-bg")
async def remove_bg(image: UploadFile = File(...)):
    data = await read_upload_limited(image, PUBLIC_MAX_UPLOAD_BYTES)
    return image_response(await remove_background_bytes(data))


@app.post("/api/transparent")
async def transparent(image: UploadFile = File(...)):
    data = await read_upload_limited(image, PUBLIC_MAX_UPLOAD_BYTES)
    return image_response(await remove_background_bytes(data, alpha_matting=True))


@app.post("/api/upscale")
async def upscale(image: UploadFile = File(...), scale: int = Form(2)):
    data = await read_upload_limited(image, PUBLIC_MAX_UPLOAD_BYTES)
    return image_response(await upscale_bytes(data, scale))


@app.post("/api/foreground-cutout")
async def foreground_cutout(image: UploadFile = File(...)):
    data = await read_upload_limited(image, PUBLIC_MAX_UPLOAD_BYTES)
    return image_response(await remove_background_bytes(data, alpha_matting=True))


@app.post("/api/product-photo")
async def product_photo(image: UploadFile = File(...), background: str = Form("white")):
    data = await read_upload_limited(image, PUBLIC_MAX_UPLOAD_BYTES)
    return image_response(await product_photo_bytes(data, background))


@app.post("/api/replace-bg")
async def replace_bg(image: UploadFile = File(...), background: str = Form("white")):
    data = await read_upload_limited(image, PUBLIC_MAX_UPLOAD_BYTES)
    return image_response(await replace_bg_bytes(data, background))


@app.post("/api/restore")
async def restore(image: UploadFile = File(...)):
    data = await read_upload_limited(image, PUBLIC_MAX_UPLOAD_BYTES)
    return image_response(await restore_bytes(data))


@app.post("/api/strip-metadata")
async def strip_metadata(image: UploadFile = File(...)):
    data = await read_upload_limited(image, PUBLIC_MAX_UPLOAD_BYTES)
    return image_response(await strip_metadata_bytes(data))


@app.post("/v1/remove-background")
async def paid_remove_background(
    image: UploadFile = File(...),
    _access=Depends(require_paid_api_access),
):
    data = await read_upload_limited(image, PAID_MAX_UPLOAD_BYTES)
    return image_response(await remove_background_bytes(data))


@app.post("/v1/upscale")
async def paid_upscale(
    image: UploadFile = File(...),
    scale: int = Form(2),
    _access=Depends(require_paid_api_access),
):
    data = await read_upload_limited(image, PAID_MAX_UPLOAD_BYTES)
    return image_response(await upscale_bytes(data, scale))


@app.get("/api/pricing")
async def pricing():
    return await pricing_payload()


@app.get("/api/clerk-health")
async def clerk_config():
    return await clerk_health()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/mcp")
async def mcp_info():
    return {
        "name": "PhotoTools MCP",
        "status": "configured",
        "transport": "stdio or streamable-http via server/mcp_server.py",
        "auth": "Paid HTTP deployments should require Clerk bearer tokens or X-PhotoTools-API-Key.",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8093)
