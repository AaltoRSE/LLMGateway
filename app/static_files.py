"""Static file serving for frontend provision"""

import logging

from fastapi.staticfiles import StaticFiles
from fastapi import Response
from starlette.types import Scope

logger = logging.getLogger("app")


class SPAStaticFiles(StaticFiles):
    """
    Single Page application Static file rovision defaulting back to index.html
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        """
        Returns a Response for the requested static file path.
        If the file is not found or an error occurs, serves the default index.html (".").
        This is useful for single-page applications to handle client-side routing.
        """
        scope["static"] = True
        try:
            response = await super().get_response(path, scope)

        except:  # pylint: disable=bare-except
            response = await super().get_response(".", scope)
        if response.status_code == 404:
            response = await super().get_response(".", scope)
        return response

    async def post_response(self, path: str, scope: Scope) -> Response:
        """
        Returns a Response for POST requests to static file paths.
        If the file is not found or an error occurs, serves the default index.html (".").
        This allows POST requests to fallback to the SPA entry point for client-side handling.
        """
        scope["static"] = True
        try:
            response = await super().get_response(path, scope)
        except:  # pylint: disable=bare-except
            response = await super().get_response(".", scope)
        if response.status_code == 404:
            response = await super().get_response(".", scope)
        return response
