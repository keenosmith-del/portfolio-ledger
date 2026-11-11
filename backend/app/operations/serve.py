"""Use precisely configured proxy trust rather than Uvicorn's implicit default."""

import ipaddress
import socket

import uvicorn

from app.core.config import settings


def proxy_addresses() -> list[str]:
    addresses = set(settings.trusted_proxy_ips)
    for host in settings.trusted_proxy_hosts:
        # Exact deployment-time A/AAAA addresses, never a broad provider CIDR.
        resolved = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        for record in resolved:
            address = ipaddress.ip_address(record[4][0])
            if address.is_unspecified or address.is_multicast:
                raise ValueError("invalid proxy service address")
            addresses.add(str(address))
    if settings.app_env == "production" and not addresses:
        raise ValueError("proxy service DNS resolved no addresses")
    return sorted(addresses)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_bind_host,
        port=settings.port,
        proxy_headers=True,
        forwarded_allow_ips=",".join(proxy_addresses()),
    )
