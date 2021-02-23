"""
Contains uploads endpoints.
"""
from http import HTTPStatus
import logging.config
from typing import Dict
import configparser

from fastapi import APIRouter, UploadFile, File, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from azure.storage.filedatalake import DataLakeDirectoryClient  # pylint: disable=import-error
from azure.core.exceptions import ResourceNotFoundError  # pylint: disable=import-error

from ..dependencies import AzureCredential


config = configparser.ConfigParser()

all_config_files = ['conf.ini', '/etc/config/conf.ini']
config.read(all_config_files)

api_key_header = APIKeyHeader(name='Authorization', auto_error=True)

logging.config.fileConfig(fname=config['Misc']["log_configuration_file"], disable_existing_loggers=False)
logger = logging.getLogger(__file__)

router = APIRouter(prefix="/upload", tags=["uploads"])


@router.post("/json/{guid}", status_code=HTTPStatus.CREATED)
async def upload_json_file(guid: str, file: UploadFile = File(...),
                           token: str = Security(api_key_header)) -> Dict[str, str]:
    """
    Upload json file to data storage.
    """
    logger.debug('upload json requested')
    logger.debug("Access token: %s", token)

    account_url = config['Storage']["account_url"]
    file_system_name = config['Storage']["file_system_name"]
    credential = AzureCredential(token)

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
