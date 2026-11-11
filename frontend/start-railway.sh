#!/bin/sh
set -eu
: "${PUBLIC_HOST:?Set the exact public HTTPS hostname}"
: "${API_UPSTREAM_HOST:?Set the private API hostname}"
PORT=${PORT:-8080}
API_UPSTREAM_PORT=${API_UPSTREAM_PORT:-8000}
export PORT API_UPSTREAM_PORT
printf '%s' "$PUBLIC_HOST" | grep -Eq '^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$' || exit 64
printf '%s' "$API_UPSTREAM_HOST" | grep -Eq '^[a-z0-9][a-z0-9-]*\.railway\.internal$' || exit 64
for value in "$PORT" "$API_UPSTREAM_PORT"; do
  case "$value" in ''|*[!0-9]*) exit 64;; esac
  [ "$value" -gt 0 ] && [ "$value" -le 65535 ] || exit 64
done
# Use this container's provider DNS, including IPv6 nameservers; no public resolver.
DNS_RESOLVERS=$(awk '$1 == "nameserver" { if ($2 ~ /:/) printf "[%s] ",$2; else printf "%s ",$2 }' /etc/resolv.conf)
[ -n "$DNS_RESOLVERS" ] || exit 69
export DNS_RESOLVERS
# Explicit substitution allowlist preserves Nginx $uri/$remote_addr/$api_upstream.
envsubst '${PORT} ${PUBLIC_HOST} ${API_UPSTREAM_HOST} ${API_UPSTREAM_PORT} ${DNS_RESOLVERS}' \
  < /opt/portfolioledger/nginx.railway.template > /tmp/portfolioledger-railway.conf
# The unprivileged image permits its worker temp/pid directories in /tmp.
cat > /tmp/portfolioledger-nginx.conf <<'NGINX'
pid /tmp/portfolioledger-nginx.pid;
events { worker_connections 1024; }
http {
  include /etc/nginx/mime.types;
  default_type application/octet-stream;
  access_log /dev/stdout;
  error_log /dev/stderr warn;
  client_body_temp_path /tmp/client_temp;
  proxy_temp_path /tmp/proxy_temp;
  include /tmp/portfolioledger-railway.conf;
}
NGINX
nginx -t -c /tmp/portfolioledger-nginx.conf
exec nginx -c /tmp/portfolioledger-nginx.conf -g 'daemon off;'
