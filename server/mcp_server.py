import os

from image_ops import (
    base64_to_bytes,
    product_photo_bytes,
    remove_background_bytes,
    replace_bg_bytes,
    restore_bytes,
    result_to_base64,
    strip_metadata_bytes,
    upscale_bytes,
)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - deployment dependency guard
    raise RuntimeError("Install server requirements before starting the PhotoTools MCP server") from exc


mcp = FastMCP("PhotoTools")


@mcp.tool()
async def remove_background(image_base64: str) -> dict:
    """Remove an image background and return a transparent PNG as base64."""
    return result_to_base64(await remove_background_bytes(base64_to_bytes(image_base64)))


@mcp.tool()
async def make_transparent_png(image_base64: str) -> dict:
    """Create a transparent foreground cutout PNG as base64."""
    return result_to_base64(await remove_background_bytes(base64_to_bytes(image_base64), alpha_matting=True))


@mcp.tool()
async def upscale_image(image_base64: str, scale: int = 2) -> dict:
    """Upscale an image by 2x or 4x. Returns mode=ai-upscale when the ONNX model is installed."""
    return result_to_base64(await upscale_bytes(base64_to_bytes(image_base64), scale))


@mcp.tool()
async def product_photo_background(image_base64: str, background: str = "white") -> dict:
    """Remove the background and place the product on white or light-gray background."""
    return result_to_base64(await product_photo_bytes(base64_to_bytes(image_base64), background))


@mcp.tool()
async def replace_background_preset(image_base64: str, background: str = "studio") -> dict:
    """Replace the background with one of: white, studio, sunset, nature."""
    return result_to_base64(await replace_bg_bytes(base64_to_bytes(image_base64), background))


@mcp.tool()
async def restore_photo(image_base64: str) -> dict:
    """Apply lightweight sharpening, contrast, color, and brightness restoration."""
    return result_to_base64(await restore_bytes(base64_to_bytes(image_base64)))


@mcp.tool()
async def strip_metadata(image_base64: str) -> dict:
    """Re-encode an image as PNG without EXIF/location metadata."""
    return result_to_base64(await strip_metadata_bytes(base64_to_bytes(image_base64)))


if __name__ == "__main__":
    transport = os.getenv("PHOTO_TOOLS_MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
