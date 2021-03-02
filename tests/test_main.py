import os
import tempfile

from fastapi.testclient import TestClient

from app.main import app
from app.routers.uploads import __get_placement_directory_client


client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "OK"}


def test_upload_file_no_authorization_token():
    response = client.post(
        "/123456/json",
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}


def test_upload_file_no_file():
    response = client.post(
        "/123456/json",
        headers={"Authorization": "secret"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": [{"loc": ["body", "file"],
                                           "msg": "field required",
                                           "type": "value_error.missing"}]}


def test_upload_file(mocker):
    directory_client = mocker.patch('app.routers.uploads.DataLakeDirectoryClient')
    with tempfile.NamedTemporaryFile(dir='.') as tmp:
        filename = os.path.basename(tmp.name)

        response = client.post(
            "/123456/json",
            headers={"Authorization": "secret"},
            files={'file': tmp}
        )

    assert directory_client.called
    assert response.status_code == 201
    assert response.json() == {'filename': filename, 'schema_validated': False}


def test_get_placement_directory_client(mocker):
    directory_client = mocker.patch('app.routers.uploads.DataLakeDirectoryClient')
    placement_directory_client = __get_placement_directory_client(directory_client)

    assert directory_client.create_sub_directory.called
    assert placement_directory_client is not None
