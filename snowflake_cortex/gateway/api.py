"""Snowflake Cortex Agent Gateway module.

Some repo docs and scripts reference `python -m snowflake_cortex.gateway.api`.
To support Snowflake Container Services (SPCS) deployments (and local Docker),
this module exposes the stdlib HTTP server implementation.
"""

from __future__ import annotations

from snowflake_cortex.gateway.http_server import main, run

__all__ = ["run", "main"]

if __name__ == "__main__":
    main()

