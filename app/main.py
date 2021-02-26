"""
The main application entry-point for the Osiris Ingress API.
"""

import logging.config
from typing import Dict
import configparser

from http import HTTPStatus
from fastapi import FastAPI

from .dependencies import CONFIG_FILE_LOCATIONS
from .routers import uploads


config = configparser.ConfigParser()
config.read(CONFIG_FILE_LOCATIONS)

logging.config.fileConfig(fname=config['Logging']['configuration_file'], disable_existing_loggers=False)
logger = logging.getLogger(__file__)

app = FastAPI(
    title='Osiris Ingress API',
    version='0.1.0',
    root_path=config['FastAPI']['root_path']
)
app.include_router(uploads.router)


@app.get('/', status_code=HTTPStatus.OK)
async def root() -> Dict[str, str]:
    """
    Endpoint for basic connectivity test.
    """
    logger.debug('root requested')
    return {'message': 'OK'}
