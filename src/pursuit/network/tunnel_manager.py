"""TunnelManager: the tunnel's whole lifecycle, pyngrok calls injected
(D-54, CLOUD-01).

Every pyngrok call and timing primitive is an injected callable, the same DI
style Gatekeeper (clock/sleep) and Watchdog (clock/sleeper/exit_action)
already use -- so every unit test drives this class with fakes, zero real
processes, zero real sleeps, zero ngrok.exe. Production callers pass
nothing: the real pyngrok functions are bound as this class's own
constructor defaults, in one place (`pyngrok` is imported ONLY here, and
only as function references -- plain import never triggers pyngrok's own
lazy binary download; that happens inside pyngrok's own first real
`connect()` call, never at import time).

Reconnect is bounded by NetworkParams.retry_count/backoff_seconds (Table 19
rows 4/3, reused -- D-55 adds no new number) and reconnects to the SAME
static domain every time, so the opponent's own public URL never changes
mid-game.

Pitfall-3 finding (RESEARCH.md): pyngrok never auto-reconnects a dropped
tunnel on its own -- it only exposes get_ngrok_process().healthy() for the
caller to poll. A tunnel drop is NOT a process freeze: the local FastMCP
server and turn loop keep running; only the external ingress path is
broken. That is why this concern belongs entirely to TunnelManager, and
watchdog.py stays untouched by this plan.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from pyngrok import ngrok

from pursuit.shared.network_config import NetworkParams
from pursuit.shared.tunnel_config import TunnelParams, require_env

ConnectFn = Callable[..., object]
DisconnectFn = Callable[[str], None]
KillFn = Callable[[], None]
GetProcessFn = Callable[[], object]
SleepFn = Callable[[float], None]
ClockFn = Callable[[], float]


class TunnelManager:
    """Start/monitor/stop the tunnel process; expose its public URL.

    `params`/`network_params` are the two required, positional
    collaborators (Watchdog's own required-args discipline); every pyngrok
    call and timing primitive is keyword-only and injectable.
    """

    def __init__(
        self,
        params: TunnelParams,
        network_params: NetworkParams,
        *,
        connect: ConnectFn = ngrok.connect,
        disconnect: DisconnectFn = ngrok.disconnect,
        kill: KillFn = ngrok.kill,
        get_process: GetProcessFn = ngrok.get_ngrok_process,
        sleep: SleepFn = time.sleep,
        clock: ClockFn = time.monotonic,
    ) -> None:
        self.params = params
        self._network_params = network_params
        self._connect = connect
        self._disconnect = disconnect
        self._kill = kill
        self._get_process = get_process
        self._sleep = sleep
        self._clock = clock
        self.public_url: str | None = None
        self._stopped = False

    def start(self) -> None:
        """Connect the configured local port to the static domain.

        Preflights NGROK_AUTHTOKEN's presence (pyngrok reads its actual
        value from the environment itself; this only checks the var is
        SET, by name) and resolves the domain explicitly -- both BEFORE
        the real connect call, so a missing var is reported by name at
        startup, not as a cryptic mid-connect ngrok failure. Any further
        connect failure (domain already taken, no network) propagates
        as-is -- this method never swallows an exception.
        """
        require_env(self.params.authtoken_env)
        domain = require_env(self.params.domain_env)
        tunnel = self._connect(self._network_params.port, domain=domain)
        self.public_url = tunnel.public_url

    def healthy(self) -> bool:
        """True iff the local ngrok agent process reports itself healthy."""
        return self._get_process().healthy()

    def ensure_connected(self) -> bool:
        """Reconnect to the SAME domain while unhealthy, bounded by
        network_params.retry_count with backoff_seconds waits between
        attempts (Table 19, reused -- D-55). Returns True iff healthy by
        the time this returns, False if every attempt was exhausted.
        """
        if self.healthy():
            return True
        domain = require_env(self.params.domain_env)
        for _attempt in range(self._network_params.retry_count):
            self._sleep(self._network_params.backoff_seconds)
            tunnel = self._connect(self._network_params.port, domain=domain)
            self.public_url = tunnel.public_url
            if self.healthy():
                return True
        return False

    def stop(self) -> None:
        """Disconnect (if a tunnel is open) then kill the local ngrok
        agent, exactly once each across the whole lifecycle. Idempotent --
        a second call is a safe no-op."""
        if self._stopped:
            return
        self._stopped = True
        if self.public_url is not None:
            self._disconnect(self.public_url)
        self._kill()
