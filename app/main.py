"""This module is a simple setup of fastapi"""

import logging
import logging.config
from typing import Dict

from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.security import OAuth2

logging.config.fileConfig(fname='log.conf')

logger = logging.getLogger("main")

app = FastAPI()

oauth2_scheme = OAuth2()


@app.get("/")
async def root() -> Dict[str, str]:
    """
    A simple endpoint example.
    """
    logger.info('root requested')
    print('Hellooo')
    return {"message": "Hello World"}


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...), token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
    """
    Upload json file to data storage.
    """
    logger.debug(token)
    return {"filename": file.filename}
