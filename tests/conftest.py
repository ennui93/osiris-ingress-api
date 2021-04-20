from unittest import mock

import pytest


@pytest.fixture(scope="session", autouse=True)
def mocked_configuration(request):
    print("Patching core.feature.service")
    patched = mock.patch('app.dependencies.Configuration')
    patched.__enter__()

    def unpatch():
        patched.__exit__()
        print("Patching complete. Unpatching")

    request.addfinalizer(unpatch)