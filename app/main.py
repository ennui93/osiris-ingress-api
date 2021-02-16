"""This module is a simple setup of fastapi"""

import logging
import logging.config
import time
from typing import Dict
from http import HTTPStatus
import configparser

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.security import OAuth2

from azure.core.credentials import AccessToken  # pylint: disable=import-error
from azure.storage.filedatalake import DataLakeDirectoryClient  # pylint: disable=import-error
from azure.core.exceptions import ResourceNotFoundError  # pylint: disable=import-error

logging.config.fileConfig(fname='log.conf')

logger = logging.getLogger("main")

app = FastAPI()

oauth2_scheme = OAuth2()

config = configparser.ConfigParser()
config.read('conf.ini')


class AzureCredential():  # pylint: disable=too-few-public-methods
    """
    Represents a Credential object. This is a hack to use a access token
    received from a client.
    """
    EXPIRES_IN = 1000

    def __init__(self, token: str):
        self.token = token
        self.expires_on = self.EXPIRES_IN + time.time()

    def get_token(self, *scopes, **kwargs):  # pylint: disable=unused-argument
        """
        Returns an AcccesToken object.
        """
        return AccessToken(self.token, self.expires_on)


@app.get("/")
async def root() -> Dict[str, str]:
    """
    A simple endpoint example.
    """
    logger.info('root requested')
    return {"message": "Hello World"}


@app.post("/uploadfile/{guid}", status_code=HTTPStatus.CREATED)
async def create_upload_file(guid: str, file: UploadFile = File(...),
                             token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
    """
    Upload json file to data storage.
    """
    logger.debug(token)

    credential = AzureCredential(token)

    account_url = config['Storage']["account_url"]
    file_system_name = config['Storage']["file_system_name"]

    with DataLakeDirectoryClient(account_url, file_system_name, guid, credential=credential) as directory_client:
        try:
            directory_client.get_directory_properties()  # Test if the directory exist otherwise return error.
        except ResourceNotFoundError as error:
            logger.error(error)
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail="The given dataset doesnt exist") from error

        with directory_client.get_file_client(file.filename) as file_client:
            try:
                file_client.upload_data(file.file.read(), overwrite=True)
            except Exception as error:
                logger.error(type(error).__name__)

                raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                    detail="File could not be uploaded") from error

    return {"filename": file.filename}
