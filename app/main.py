"""
The main application entry-point for the Osiris Ingress API.
"""

from typing import Dict


from http import HTTPStatus
from fastapi import FastAPI

from .dependencies import Configuration
from .routers import uploads


configuration = Configuration(__file__)
config = configuration.get_config()
logger = configuration.get_logger()


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
