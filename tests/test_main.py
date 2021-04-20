import os
import tempfile
from unittest.mock import patch

import pytest

from fastapi.testclient import TestClient
from app.routers.uploads import __get_destination_directory_client


def get_app():
    with patch('app.dependencies.Configuration') as _:
        from app.main import app

        return TestClient(app)


client = get_app()


def test_read_main():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'OK'}


@pytest.mark.parametrize('test_endpoint', ['/123456', '/123456/json'])
def test_upload_file_no_authorization_token(test_endpoint):
    response = client.post(
        test_endpoint,
    )

    assert response.status_code == 403
    assert response.json() == {'detail': 'Not authenticated'}


@pytest.mark.parametrize('test_endpoint', ['/123456', '/123456/json'])
def test_upload_file_no_file(test_endpoint):
    response = client.post(
        test_endpoint,
        headers={'Authorization': 'secret'},
    )

    assert response.status_code == 422
    assert response.json() == {'detail': [{'loc': ['body', 'file'],
                                           'msg': 'field required',
                                           'type': 'value_error.missing'}]}


def test_upload_file(mocker):
    directory_client = mocker.patch('app.routers.uploads.DataLakeDirectoryClient')
    with tempfile.NamedTemporaryFile(dir='.') as tmp:
        filename = os.path.basename(tmp.name)

        response = client.post(
            '/123456',
            headers={'Authorization': 'secret'},
            files={'file': tmp}
        )

    assert directory_client.called
    assert response.status_code == 201
    assert response.json()['filename'] == filename


@pytest.mark.parametrize('schema_validate', [False, True])
def test_upload_json_file(schema_validate, mocker):
    mocker.patch('app.routers.uploads.json')
    directory_client = mocker.patch('app.routers.uploads.DataLakeDirectoryClient')
    fastjsonschema_validate = mocker.patch('app.routers.uploads.fastjsonschema.validate')

    with tempfile.NamedTemporaryFile(dir='.') as tmp:
        filename = os.path.basename(tmp.name)

        response = client.post(
            '/123456/json',
            headers={'Authorization': 'secret'},
            files={'file': tmp},
            params={'schema_validate': schema_validate}
        )

    assert directory_client.called
    assert response.status_code == 201
    assert response.json()['filename'] == filename
    if schema_validate:
        assert fastjsonschema_validate.called
    else:
        assert not fastjsonschema_validate.called


def test_get_placement_directory_client(mocker):
    directory_client = mocker.patch('app.routers.uploads.DataLakeDirectoryClient')
    placement_directory_client = __get_destination_directory_client(directory_client)

    assert directory_client.get_sub_directory_client.called
    assert placement_directory_client is not None
