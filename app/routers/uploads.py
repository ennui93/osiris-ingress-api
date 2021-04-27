"""
Contains endpoints for uploading data to the DataPlatform.
"""
import json

from http import HTTPStatus
from datetime import datetime
from typing import Dict, Union

import fastjsonschema

from fastapi import APIRouter, UploadFile, File, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from azure.storage.filedatalake import DataLakeDirectoryClient, DataLakeFileClient
from osiris.core.azure_client_authorization import AzureCredential

from ..dependencies import Configuration, Metric

configuration = Configuration(__file__)
config = configuration.get_config()
logger = configuration.get_logger()

access_token_header = APIKeyHeader(name='Authorization', auto_error=True)

router = APIRouter(tags=['uploads'])


@router.post('/{guid}', status_code=HTTPStatus.CREATED)
@Metric.histogram
async def upload_file(guid: str,
                      file: UploadFile = File(...),
                      token: str = Security(access_token_header)) -> Dict[str, str]:
    """
    Upload an arbitrary file to data storage.
    """
    logger.debug('upload file requested')

    with __get_directory_client(token, guid) as directory_client:
        __check_directory_exist(directory_client)
        destination_directory_client = __get_destination_directory_client(directory_client)
        file_data = file.file.read()
        __upload_file(destination_directory_client, file.filename, file_data)

    return {'filename': file.filename}


@router.post('/{guid}/json', status_code=HTTPStatus.CREATED)
@Metric.histogram
async def upload_json_file(guid: str,
                           schema_validate: bool = False,
                           file: UploadFile = File(...),
                           token: str = Security(access_token_header)) -> Dict[str, Union[str, bool]]:
    """
    Upload json file to data storage with optional schema validation.
    """
    logger.debug('upload json requested')

    json_schema_file_path = 'schema.json'   # NOTE: Could be parameterized in the url

    with __get_directory_client(token, guid) as directory_client:
        __check_directory_exist(directory_client)
        destination_directory_client = __get_destination_directory_client(directory_client)
        file_data = file.file.read()
        try:
            json_data = json.loads(file_data.decode())  # Ensures the incoming data is valid JSON
            if schema_validate:
                __validate_json_with_schema(directory_client, json_schema_file_path, json_data)
        except json.JSONDecodeError as error:
            message = f'({type(error).__name__}) JSON validation error: {error}'
            logger.error(message)
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=message) from error

        __upload_file(destination_directory_client, file.filename, file_data)

    return {'filename': file.filename, 'schema_validated': schema_validate}


@router.post('/{guid}/save_state', status_code=HTTPStatus.CREATED)
@Metric.histogram
async def save_state(guid: str,
                     file: UploadFile = File(...),
                     token: str = Security(access_token_header)):
    """
    Upload state file to data storage - will be called state.json in the root folder.
    """
    logger.debug('save state requested')

    with __get_directory_client(token, guid) as directory_client:
        __check_directory_exist(directory_client)

        file_data = file.file.read()
        filename = 'state.json'

        __upload_file(directory_client, filename, file_data)

    return {'filename': filename}


def __upload_file(directory_client: DataLakeDirectoryClient, filename: str, file_data: bytes):
    try:
        # NOTE: Using get_file_client as a context manager will close the parent DirectoryClient on __exit__
        file_client = directory_client.get_file_client(filename)
        try:
            file_client.upload_data(file_data, overwrite=True)
        except HttpResponseError as error:
            message = f'({type(error).__name__}) An error occurred while uploading file: {error}'
            logger.error(message)
            raise HTTPException(status_code=error.status_code, detail=message) from error
    finally:
        file_client.close()


def __check_directory_exist(directory_client: DataLakeDirectoryClient):
    try:
        directory_client.get_directory_properties()
    except ResourceNotFoundError as error:
        message = f'({type(error).__name__}) The given dataset doesnt exist: {error}'
        logger.error(message)
        raise HTTPException(status_code=error.status_code, detail=message) from error
    except HttpResponseError as error:
        message = f'({type(error).__name__}) An error occurred while checking if the dataset exist: {error}'
        logger.error(message)
        raise HTTPException(status_code=error.status_code, detail=message) from error


def __validate_json_with_schema(directory_client: DataLakeDirectoryClient, json_schema_file_path: str, data_dict: Dict):
    file_client = directory_client.get_file_client(json_schema_file_path)
    schema = __get_validation_schema(file_client)
    try:
        fastjsonschema.validate(schema, data_dict)
    except (TypeError, fastjsonschema.JsonSchemaDefinitionException) as error:
        logger.error(type(error).__name__, error)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Invalid schema definition: {getattr(error, "message", error)}') from error
    except fastjsonschema.JsonSchemaValueException as error:
        message = f'({type(error).__name__}) JSON Schema validation error: {error}'
        logger.error(message)
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail={
                                'message': f'JSON Schema validation error: {error.message}',
                                'name': f'{error.name}',
                                'rule': f'{error.rule}',
                                'rule_definition': f'{error.rule_definition}'
                            }) from error


def __get_validation_schema(file_client: DataLakeFileClient) -> Dict:
    try:
        file_client.get_file_properties()
    except ResourceNotFoundError as error:
        message = f'({type(error).__name__}) The expected JSON Schema does not exist: {error}'
        logger.error(message)
        raise HTTPException(status_code=error.status_code, detail=message) from error

    try:
        stream = file_client.download_file()
    except HttpResponseError as error:
        message = f'({type(error).__name__}) Schema could not be retrieved for validation: {error}'
        logger.error(message)
        raise HTTPException(status_code=error.status_code, detail=message) from error

    try:
        schema = json.loads(stream.readall().decode())
    except json.JSONDecodeError as error:
        message = f'({type(error).__name__}) Malformed schema JSON: {error}'
        logger.error(message)
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=message) from error

    return schema


def __get_destination_directory_client(directory_client: DataLakeDirectoryClient) -> DataLakeDirectoryClient:
    now = datetime.utcnow()

    path = f'year={now.year:02d}/month={now.month:02d}/day={now.day:02d}/hour={now.hour:02d}'
    return directory_client.get_sub_directory_client(path)


def __get_directory_client(token: str, guid: str) -> DataLakeDirectoryClient:
    account_url = config['Azure Storage']['account_url']
    filesystem_name = config['Azure Storage']['filesystem_name']
    credential = AzureCredential(token)

    return DataLakeDirectoryClient(account_url, filesystem_name, guid, credential=credential)
