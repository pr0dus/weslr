# Weslr Private Test Deployment

This is a **private, isolated test deployment** of the Weslr chat UI, created to validate functionality before production.

## Quick Start

```bash
cd /data/data/com.termux/files/home/.openclaw/workspace
./weslr-test-deployment/start.sh
```

## Configuration

| Component | Port | Purpose |
|-----------|------|---------|
| **UI Server** | `8087` | Serves static HTML/CSS/JS from `weslr-ui/` |
| **API Server** | `8091` | Provides Weslr backend endpoints (Python) |

## Endpoints

### API Server (`http://localhost:8091/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/contract/continuity` | Fetch continuity status |
| `GET` | `/api/contract/operator/summary` | Fetch operator summary |
| `GET` | `/api/contract/operator/visibility` | Fetch operator panel visibility |
| `GET` | `/api/contract/conversations` | Fetch conversation list |
| `POST` | `/api/contract/file-route` | Route a file to Weslr |
| `POST` | `/api/contract/upload-file` | Upload a file to Weslr |

### UI Server (`http://localhost:8087/`)

Serves the React app from `weslr-ui/` with CORS enabled for API access.

## Access

- **Local**: http://127.0.0.1:8087/
- **LAN**: http://{server-ip}:8087/

## Stopping

```bash
cd /data/data/com.termux/files/home/.openclaw/workspace
./weslr-test-deployment/stop.sh
```

## Comparison: Test vs Production

| Feature | Test Deployment | Production |
|---------|-----------------|------------|
| Ports | 8087 (UI), 8091 (API) | 8008 (UI via nginx), 8000 (API) |
| Backend | Python directly | Python via nginx proxy |
| CORS | Enabled (all origins) | Configured origins only |
| SSL | None | HTTPS (Let's Encrypt) |
| Authentication | None | JWT token |

## Production Template

To replicate this setup for production:

1. Keep the same **port separation** (8087 UI, 8091 API)
2. Add nginx reverse proxy for `/api` → `http://localhost:8091/`
3. Add SSL certificates via Let's Encrypt
4. Add authentication middleware
5. Configure CORS origins explicitly

## Safety Notes

- ✅ **No changes** to live website (chat.weslr.de)
- ✅ **No changes** to nginx configuration
- ✅ **No changes** to existing public services
- ✅ **Isolated** from production data
- ✅ **Reversible** - `rm -rf weslr-test-deployment`

## Troubleshooting

### Port already in use

Edit `weslr-test-deployment/start.sh` and change the ports to unused ones:

```bash
# Change from:
--ui-port 8087 --api-port 8091

# To:
--ui-port 8088 --api-port 8092
```

### CORS errors in browser

The server already enables CORS. Check that the browser is accessing the test site directly, not through a proxy that strips headers.

### API not responding

Verify the API server started:
```bash
ps aux | grep server.py
```

Check logs:
```bash
tail -f weslr-test-deployment/logs/*
```

## What's Next?

After testing:
1. Verify chat UI renders correctly
2. Test file upload functionality
3. Verify operator panel displays properly
4. Confirm real Weslr responses (not mocks)
5. Document any blockers for production
