#!/bin/bash
set -e

echo "Starting PoE2 PathOfCrafting Backend..."

# --- Optional residential egress for trade2 calls -------------------------------------
# Routes ONLY the PoE2 trade API calls (which Cloudflare 403s from datacenter IPs) out a
# home Tailscale exit node, via userspace networking + a local HTTP proxy on :1055.
# Fully gated on TAILSCALE_AUTHKEY: if unset, this whole block is a no-op (normal egress).
# Non-fatal AND non-blocking: runs in the background so it can never delay uvicorn/health
# checks. If login or the exit node is unavailable, trade pricing degrades to the
# "pricing unavailable" + trade deep-link path; nothing else is affected.
if [ -n "${TAILSCALE_AUTHKEY:-}" ] && command -v tailscaled >/dev/null 2>&1; then
  echo "Tailscale: starting userspace daemon..."
  tailscaled \
    --tun=userspace-networking \
    --socks5-server=localhost:1055 \
    --outbound-http-proxy-listen=localhost:1055 \
    --state=mem: \
    --socket=/tmp/tailscaled.sock >/tmp/tailscaled.log 2>&1 &

  (
    set +e  # everything here is best-effort
    TS="tailscale --socket=/tmp/tailscaled.sock"

    # 1) Log in (auth only - kept separate so a transient exit-node issue can't block login)
    n=0
    until $TS up --auth-key="${TAILSCALE_AUTHKEY}" --hostname="${TS_HOSTNAME:-fly-poe-backend}" >/dev/null 2>&1; do
      n=$((n + 1))
      if [ "$n" -ge 30 ]; then
        echo "Tailscale: login failed after ${n} tries - trade pricing -> deep-link fallback."
        exit 0
      fi
      sleep 2
    done
    echo "Tailscale: logged in as ${TS_HOSTNAME:-fly-poe-backend}"

    # 2) Apply the exit node separately, with retries (the node may take a moment to appear).
    if [ -n "${TS_EXIT_NODE:-}" ]; then
      n=0
      until $TS set --exit-node="${TS_EXIT_NODE}" >/dev/null 2>&1; do
        n=$((n + 1))
        if [ "$n" -ge 15 ]; then
          echo "Tailscale: exit node ${TS_EXIT_NODE} unavailable - trade pricing -> deep-link fallback."
          exit 0
        fi
        sleep 4
      done
      echo "Tailscale: routing trade2 egress via exit node ${TS_EXIT_NODE}."
    fi
  ) &
fi
# --------------------------------------------------------------------------------------

# Start the application immediately (Tailscale, if enabled, connects in the background).
echo "Starting uvicorn server..."
exec "$@"
