# PhotoTools

PhotoTools is a lightweight image tools site with a static frontend, FastAPI backend, and MCP server for agent/API workflows.

The web app is designed for ad-supported public usage. The API and MCP layer are designed for paid access through Clerk auth, API keys, and credit-based plans.

## What Is Included

- Static frontend in `frontend/`
- FastAPI image API in `server/main.py`
- Shared image operations in `server/image_ops.py`
- Clerk/dummy billing hooks in `server/auth.py`
- MCP server in `server/mcp_server.py`
- Systemd template for MCP in `server/deploy/`
- Pricing and MCP marketing/docs pages in `frontend/pricing.html` and `frontend/mcp.html`

## Web Tools

The frontend includes browser and API-backed image tools such as:

- Resize and crop
- Compress
- Convert
- Remove background
- Transparent foreground cutout
- Product photo background
- Background presets
- Metadata removal
- Social media presets
- Marketplace presets
- Thumbnails
- Watermarking
- Add text
- Profile pictures
- Collage
- Border
- Blur
- Passport/ID photos
- Style effects
- Restore photo

Each tool page uses the same workflow:

1. Upload box is shown first.
2. After upload, the original image replaces the upload box.
3. Controls appear below the original.
4. Processed result appears to the right on desktop or below on mobile.
5. A clear download button is shown with the result.

## Monetization Model

Suggested model:

- Free Web: ad-supported usage
- Starter API/MCP: `$12/mo`, 200 credits
- Pro API/MCP: `$29/mo`, 500 credits
- Studio: `$79/mo`, 1,500 credits
- Overage: about `$0.06/credit`

MCP/API access is especially useful for AI agents that need to process images during automated workflows.

## Local Frontend

```powershell
cd frontend
python -m http.server 8091
```

Open:

```text
http://127.0.0.1:8091/
```

## Local API

```powershell
cd server
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8093
```

Health check:

```text
http://127.0.0.1:8093/api/health
```

## MCP

For local stdio use:

```powershell
cd server
python3.12 -m pip install -r requirements-mcp.txt
python mcp_server.py
```

Available MCP tools:

- `remove_background`
- `make_transparent_png`
- `upscale_image`
- `product_photo_background`
- `replace_background_preset`
- `restore_photo`
- `strip_metadata`

Hosted MCP/API deployments should sit behind an auth-aware proxy and require either:

- `Authorization: Bearer <clerk-session-token>`
- `X-PhotoTools-API-Key: <api-key>`

## Clerk Billing

This repo is wired for Clerk auth and dummy billing placeholders.

Set real Clerk environment values in production:

- `CLERK_PUBLISHABLE_KEY`
- `CLERK_FRONTEND_API` or `CLERK_JWKS_URL`
- `CLERK_JWT_AUDIENCE`
- `CLERK_AUTHORIZED_PARTIES`

Keep `PHOTO_TOOLS_BILLING_MODE=dummy` while testing. Use `PHOTO_TOOLS_DUMMY_PAID_USERS` and `PHOTO_TOOLS_DUMMY_API_KEYS` to simulate paid access.

## Deployment Notes

Existing VPS layout used during development:

```text
/home/mcuser/phototools/frontend
/home/mcuser/phototools/server
```

Existing service names:

```text
phototools-frontend.service
phototools-api.service
```

Recommended hardening before production:

- Put API/MCP behind a reverse proxy.
- Keep upload byte and pixel limits enabled.
- Set CORS to the production origin only.
- Add rate limiting.
- Add real Clerk billing webhooks or app-owned credit accounting.
- Install a real ONNX model before marketing upscale as AI-powered.
