"""
Contains endpoints for uploading data to the DataPlatform.
"""
import json
import configparser
import logging.config

from http import HTTPStatus
from typing import Dict, Union
from json.decoder import JSONDecodeError

import fastjsonschema

from fastapi import APIRouter, UploadFile, File, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.filedatalake import DataLakeDirectoryClient, DataLakeFileClient

from ..dependencies import CONFIG_FILE_LOCATIONS, AzureCredential


config = configparser.ConfigParser()
config.read(CONFIG_FILE_LOCATIONS)

access_token_header = APIKeyHeader(name='Authorization', auto_error=True)

logging.config.fileConfig(fname=config['Logging']['configuration_file'], disable_existing_loggers=False)
logger = logging.getLogger(__file__)

router = APIRouter(tags=['uploads'])


@router.post('/{guid}/json', status_code=HTTPStatus.CREATED)
async def upload_json_file(guid: str,
                           schema_validate: bool = False,
                           file: UploadFile = File(...),
                           token: str = Security(access_token_header)) -> Dict[str, Union[str, bool]]:
    """
    Upload json file to data storage with optional schema validation.
    """
    logger.debug('upload json requested')

    json_schema_file = 'schema.json'
    account_url = config['Azure Storage']['account_url']
    file_system_name = config['Azure Storage']['file_system_name']
    credential = AzureCredential(token)

    with DataLakeDirectoryClient(account_url, file_system_name, guid, credential=credential) as directory_client:
        try:
            directory_client.get_directory_properties()  # Test if the directory exist otherwise return error.
        except ResourceNotFoundError as error:
            logger.error(type(error).__name__, error)
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail='The given dataset doesnt exist') from error

        try:
            # NOTE: We can't use get_file_client as a context manager because it closes the DirectoryClient on __exit__
            file_client: DataLakeFileClient
            file_data: bytes = file.file.read()

            if schema_validate:
                file_client = directory_client.get_file_client(json_schema_file)
                __validate_json(file_client, file_data)

            file_client = directory_client.get_file_client(file.filename)
            try:
                file_client.upload_data(file_data, overwrite=True)
            except Exception as error:
                logger.error(type(error).__name__, error)
                raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                    detail='File could not be uploaded') from error
        finally:
            file_client.close()

    return {'filename': file.filename, 'schema_validated': schema_validate}


def __validate_json(file_client: DataLakeFileClient, file_data: bytes):
    schema = __get_validation_schema(file_client)
    try:
        fastjsonschema.validate(schema, json.loads(file_data.decode()))
    except (TypeError, fastjsonschema.JsonSchemaDefinitionException) as error:
        logger.error(type(error).__name__, error)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Invalid schema definition: {getattr(error, "message", error)}') from error
    except fastjsonschema.JsonSchemaValueException as error:
        logger.debug(type(error).__name__, error)
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail={
                                'message': f'Data validation error: {error.message}',
                                'name': f'{error.name}',
                                'rule': f'{error.rule}',
                                'rule_definition': f'{error.rule_definition}'
                            }) from error


def __get_validation_schema(file_client: DataLakeFileClient) -> Dict:
    try:
        file_client.get_file_properties()
    except ResourceNotFoundError as error:
        logger.debug(type(error).__name__, error)
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='The expected JSON Schema does not exist') from error

    try:
        stream = file_client.download_file()
    except Exception as error:
        logger.error(type(error).__name__, error)
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail='Schema could not be retrieved for validation') from error

    try:
        schema = json.loads(stream.readall().decode())
    except JSONDecodeError as error:
        logger.error(type(error).__name__, error)
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail=f'Malformed schema JSON: {error}') from error

    return schema
