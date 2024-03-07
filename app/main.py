"""
A placeholder hello world app.
"""

import logging

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
uvlogger = logging.getLogger("app")


from fastapi import FastAPI


from utils.serverlogging import RouterLogging
from llmapi.llm_router import lifespan

debugging = True


app = FastAPI(lifespan=lifespan, debug=True)

# Add Request logging
app.add_middleware(RouterLogging, logger=uvlogger, debug=debugging)

from llmapi.llm_router import router as llm_router

app.include_router(llm_router)

from admin.admin_router import router as admin_router

app.include_router(admin_router)
