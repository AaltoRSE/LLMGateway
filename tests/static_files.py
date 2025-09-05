from fastapi.staticfiles import StaticFiles


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
        except:
            response = await super().get_response(".", scope)
        if response.status_code == 404:
            response = await super().get_response(".", scope)
        return response

    async def post_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
        except:
            response = await super().get_response(".", scope)
        if response.status_code == 404:
            response = await super().get_response(".", scope)
        return response
