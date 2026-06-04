#!/bin/bash
set -e

echo "Starting PoE2 PathOfCrafting Backend..."

# --- Optional residential egress for trade2 calls -------------------------------------
# Routes ONLY the PoE2 trade API calls (which Cloudflare 403s from datacenter IPs) out a
# home Tailscale exit node, via userspace networking + a local HTTP proxy on :1055.
# Fully gated on TAILSCALE_AUTHKEY: if unset, this whole block is a no-op (normal egress).
# Non-fatal AND non-blocking: the daemon + connect run in the background so they can never
# delay uvicorn startup / health checks. If it never connects, the local proxy just isn't
# reachable and trade pricing degrades to the "pricing unavailable" + trade deep-link path.
if [ -n "${TAILSCALE_AUTHKEY:-}" ] && command -v tailscaled >/dev/null 2>&1; then
  echo "Tailscale: starting userspace daemon (exit node: ${TS_EXIT_NODE:-<none>})..."
  tailscaled \
    --tun=userspace-networking \
    --socks5-server=localhost:1055 \
    --outbound-http-proxy-listen=localhost:1055 \
    --state=mem: \
    --socket=/tmp/tailscaled.sock >/tmp/tailscaled.log 2>&1 &

  # Connect in the background - do NOT block app startup on it.
  (
    EXIT_ARG=""
    [ -n "${TS_EXIT_NODE:-}" ] && EXIT_ARG="--exit-node=${TS_EXIT_NODE}"
    n=0
    until tailscale --socket=/tmp/tailscaled.sock up \
          --auth-key="${TAILSCALE_AUTHKEY}" \
          --hostname="${TS_HOSTNAME:-fly-poe-backend}" \
          ${EXIT_ARG} >/dev/null 2>&1; do
      n=$((n + 1))
      if [ "$n" -ge 30 ]; then
        echo "Tailscale: 'up' failed after ${n} tries - trade pricing will use the deep-link fallback."
        exit 0
      fi
      sleep 2
    done
    echo "Tailscale: connected via exit node ${TS_EXIT_NODE:-unset}."
  ) &
fi
# --------------------------------------------------------------------------------------

# Start the application immediately (Tailscale, if enabled, connects in the background).
echo "Starting uvicorn server..."
exec "$@"
