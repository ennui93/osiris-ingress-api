import tempfile
import os

from fastapi.testclient import TestClient
from mock import patch

from app.main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_upload_file_no_authorization_token():
    response = client.post(
        "/uploadfile/123456",
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}


def test_upload_file_no_file():
    response = client.post(
        "/uploadfile/{gui}",
        headers={"Authorization": "secret"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": [{"loc": ["body", "file"],
                                           "msg": "field required",
                                           "type": "value_error.missing"}]}


@patch('app.main.DataLakeDirectoryClient')
def test_upload_file(directory_client):
    with tempfile.NamedTemporaryFile(dir='.') as tmp:
        filename = os.path.basename(tmp.name)

        response = client.post(
            "/uploadfile/{gui}",
            headers={"Authorization": "secret"},
            files={'file': tmp}
        )

    assert directory_client.called
    assert response.status_code == 201
    assert response.json() == {'filename': filename}
