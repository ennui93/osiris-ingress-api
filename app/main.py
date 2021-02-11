"""This module is a simple setup of fastapi"""

import logging
import logging.config

from fastapi import FastAPI

logging.config.fileConfig(fname='log.conf')

logger = logging.getLogger("main")

app = FastAPI()


@app.get("/")
async def root() -> str:
    """
    A simple endpoint example
    """
    logger.info('root requested')
    return {"message": "Hello World"}
