"""This module is a simple setup of fastapi"""

import logging
import logging.config
from typing import Dict

from fastapi import FastAPI

logging.config.fileConfig(fname='log.conf')

logger = logging.getLogger("main")

app = FastAPI()


@app.get("/")
async def root() -> Dict[str, str]:
    """
    A simple endpoint example
    """
    logger.info('root requested')
    return {"message": "Hello World"}
