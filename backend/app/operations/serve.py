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
    if settings.api_bind_host == "::":
        # IPv4 peers arrive as exact mapped addresses on the dual-family socket.
        for value in tuple(addresses):
            if isinstance(ipaddress.ip_address(value), ipaddress.IPv4Address):
                addresses.add(str(ipaddress.IPv6Address("::ffff:" + value)))
    if settings.app_env == "production" and not addresses:
        raise ValueError("proxy service DNS resolved no addresses")
    return sorted(addresses)


def listener_socket() -> socket.socket:
    # asyncio's host="::" creates an IPv6-only listener. Railway health probes
    # also use IPv4, so explicitly accept IPv4-mapped addresses on this socket.
    family = socket.AF_INET6 if settings.api_bind_host == "::" else socket.AF_INET
    listener = socket.socket(family, socket.SOCK_STREAM)
    try:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if family == socket.AF_INET6:
            listener.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        listener.bind((settings.api_bind_host, settings.port))
        listener.listen(2048)
        return listener
    except BaseException:
        listener.close()
        raise


if __name__ == "__main__":
    config = uvicorn.Config(
        "app.main:app",
        host=settings.api_bind_host,
        port=settings.port,
        proxy_headers=True,
        forwarded_allow_ips=",".join(proxy_addresses()),
    )
    with listener_socket() as listener:
        uvicorn.Server(config).run(sockets=[listener])
