"""Entrypoint for Snowflake Cortex Agent Gateway.

This project historically exposed the gateway as an HTTP service (port 8002).
It later evolved to support AWS Lambda + API Gateway deployments.

For Snowflake Container Services (SPCS) and local Docker usage, we provide a
lightweight stdlib HTTP server implementation in `snowflake_cortex.gateway.http_server`.
"""

from __future__ import annotations

from snowflake_cortex.gateway.http_server import main

if __name__ == "__main__":
    main()
