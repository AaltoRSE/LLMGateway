"""Logs in common event format"""

import logging

from datetime import datetime
from typing import OrderedDict
from fastapi import Request, Response

from app.security.auth import BackendUser


def format_cef_message(
    correlation_id: str | None,
    request: Request,
    response: Response,
    start_time: datetime,
    end_time: datetime,
    authenticated_user: BackendUser | None,
    is_debug: bool = False,
) -> str:

    # Header details
    vendor = "Aalto"
    product = "AI Assistant"
    version = "1.0"  # TODO: get from build pipeline version?
    signature_id = "access"
    severity = response.status_code

    response_duration = end_time - start_time
    response_time_ms = int(response_duration.total_seconds() * 1000)

    # Event time
    start_time_str = start_time.strftime("%b %d %Y %H:%M:%S")
    end_time_str = end_time.strftime("%b %d %Y %H:%M:%S")

    # Collect parameters in an OrderedDict to maintain the order
    cef_params = OrderedDict(
        [
            # Request correlation id
            ("cs2Label", "Correlation ID"),
            ("cs2", correlation_id if correlation_id else "unknown"),
            # Authenticated user, if any
            (
                "suser",
                (
                    authenticated_user.request_source.user_id
                    if authenticated_user
                    else "unknown"
                ),
            ),
            ("cs1Label", "User Roles"),
            ("cs1", authenticated_user.roles if authenticated_user else "unknown"),
            # Timings
            ("start", start_time_str),
            ("end", end_time_str),
            # Scheme & proto
            ("app", request.scope["scheme"]),
            ("proto", "TCP"),
            # Source IP
            (
                "src",
                request.scope["client"][0] if request.scope["client"] else "unknown",
            ),
            # The HTTP Request method
            ("requestMethod", request.method),
            # Timing
            ("cn1Label", "Response Time (ms)"),
            ("cn1", response_time_ms),
            # Request [body] sizes (input, output)
            ("in", request.headers.get("content-length", 0)),
            ("out", response.headers.get("content-length", 0)),
            # Referer, if any
            (
                "requestContext",
                request.headers.get("origin", "unknown"),
            ),  # by spec refererer, using origin here as this is an API endpoint
            # Log the user-agent
            ("requestClientApplication", request.headers.get("user-agent", "unknown")),
            # The X-Forwarded-For header, needed as the app is behind a proxy
            ("cs3Label", "X-Forwarded-For"),
            ("cs3", request.headers.get("x-forwarded-for", "unknown")),
            # The request URL
            (
                "request",
                f"{request.scope['scheme']}://{request.headers.get('host', 'unknown')}{request.url.path}{request.url.query}",
            ),
        ]
    )

    # Print the parameters in a formatted way
    if is_debug:
        print("CEF log parameters:")
        for key, value in cef_params.items():
            print(f"\t{key}:\t{value}")

    # Construct the CEF message
    cef_message = (
        f"CEF:0|{vendor}|{product}|{version}|{signature_id}|{request.method}|{severity}|"
        + " ".join([f"{key}={value}" for key, value in cef_params.items()])
    )

    return cef_message


class CEFRequestLogger:
    def __init__(self) -> None:
        self.logger = logging.getLogger("cef_request_logger")

    def log(
        self,
        correlation_id: str | None,
        request: Request,
        response: Response,
        start_time: datetime,
        end_time: datetime,
        authenticated_user: BackendUser | None,
    ) -> None:
        cef_message = format_cef_message(
            correlation_id=correlation_id,
            request=request,
            response=response,
            start_time=start_time,
            end_time=end_time,
            authenticated_user=authenticated_user,
        )

        self.logger.info(cef_message)
