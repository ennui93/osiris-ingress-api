"""
Contains uploads endpoints.
"""
from http import HTTPStatus
from json.decoder import JSONDecodeError
import logging.config
from typing import Dict, Union
import configparser
import json

import fastjsonschema

from fastapi import APIRouter, UploadFile, File, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from azure.storage.filedatalake import DataLakeDirectoryClient, DataLakeFileClient  # pylint: disable=import-error
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
async def upload_json_file(guid: str,   # noqa: C901
                           schema_validate: bool = False,
                           file: UploadFile = File(...),
                           token: str = Security(api_key_header)) -> Dict[str, Union[str, bool]]:
    """
    Upload json file to data storage.
    """
    logger.debug('upload json requested')
    logger.debug("Access token: %s", token)

    json_schema_file = 'schema.json'
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

        try:
            # NOTE: We don't use get_file_client as a context manager because it closes the DirectoryClient on __exit__
            file_client: DataLakeFileClient
            file_data: bytes = file.file.read()

            if schema_validate:
                file_client = directory_client.get_file_client(json_schema_file)
                try:
                    file_client.get_file_properties()
                except ResourceNotFoundError as error:
                    logger.error(error)
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                        detail="The expected JSON Schema does not exist") from error

                try:
                    stream = file_client.download_file()
                except Exception as error:
                    logger.error(type(error).__name__, error)
                    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                        detail="Schema could not be retrieved for validation") from error

                try:
                    schema = json.loads(stream.readall().decode())
                except JSONDecodeError as error:
                    logger.debug(error)
                    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                        detail=f"Malformed schema JSON: {error}") from error

                try:
                    fastjsonschema.validate(schema, json.loads(file_data.decode()))
                except (TypeError, fastjsonschema.JsonSchemaDefinitionException) as error:
                    logger.debug(error)
                    raise HTTPException(
                        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail=f"Invalid schema definition: {getattr(error, 'message', error)}") from error
                except fastjsonschema.JsonSchemaValueException as error:
                    logger.debug(error)
                    raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                                        detail={
                                            "message": f"Data validation error: {error.message}",
                                            "name": f"{error.name}",
                                            "rule": f"{error.rule}",
                                            "rule_definition": f"{error.rule_definition}"
                                        }) from error

            file_client = directory_client.get_file_client(file.filename)
            try:
                file_client.upload_data(file_data, overwrite=True)
            except Exception as error:
                logger.error(type(error).__name__, error)
                raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                    detail="File could not be uploaded") from error
        finally:
            file_client.close()

    return {"filename": file.filename, "schema_validated": schema_validate}
