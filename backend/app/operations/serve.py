"""Use precisely configured proxy trust rather than Uvicorn's implicit default."""

import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        proxy_headers=True,
        forwarded_allow_ips=",".join(settings.trusted_proxy_ips),
    )
