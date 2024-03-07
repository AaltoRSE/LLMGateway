from fastapi.staticfiles import StaticFiles
import logging

logger = logging.getLogger(__name__)


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
        except Exception as e:
            logger.debug("errored")
            logger.error(e)
            response = await super().get_response(".", scope)
        if response.status_code == 404:
            response = await super().get_response(".", scope)
        return response

    async def post_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
        except Exception as e:
            logger.debug("errored")
            logger.error(e)
            response = await super().get_response(".", scope)
        if response.status_code == 404:
            response = await super().get_response(".", scope)
        return response
