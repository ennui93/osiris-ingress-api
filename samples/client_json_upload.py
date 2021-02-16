
"""
This module demonstrates how a client can upload an json file to the DataPlatform using the ingress api.
"""

import logging
import logging.config
import os
import datetime

import configparser
import requests
import msal  # pylint: disable=import-error
from azure.identity import ClientSecretCredential

from azure.core.credentials import AccessToken
from azure.storage.blob import BlobServiceClient

logging.config.fileConfig(fname='log.conf')
logger = logging.getLogger(__file__)


class MyCredential(object):
    def __init__(self, token: str, expires_on: int):
        self.token = token
        self.expires_on = expires_on

    def get_token(self, *scopes, **kwargs):
        return AccessToken(self.token, self.expires_on)


class Client():
    """
    Client prototype to upload an json file using the ingress api.
    """

    def __init__(self):
        logger.debug("Client class is getting initialized")
        dir_path = os.path.dirname(os.path.realpath(__file__))
        config = configparser.ConfigParser()
        config.read(f'{dir_path}/conf.ini')

        self.scopes = config['Authentication']["scopes"].split()
        self.host = config['Server']["host"]

        self.app = msal.ConfidentialClientApplication(
            client_id=config['Authentication']["client_id"],
            authority=config['Authentication']["authority"],
            client_credential=config['Authentication']["secret"]
        )

        self.token_credential = ClientSecretCredential(
            tenant_id='mjolnerdk.onmicrosoft.com',
            client_id=config['Authentication']["client_id"],
            client_secret=config['Authentication']["secret"]
        )

    def get_access_token(self) -> str:
        """
        Returns the access token
        """
        logger.debug("get_access_token is called")
        result = self.app.acquire_token_silent(self.scopes, account=None)

        if not result:
            logging.debug("No suitable token exists in cache. Let's get a new one from AAD.")
            result = self.app.acquire_token_for_client(scopes=self.scopes)

        logger.debug("access_token: %s", result['access_token'])
        return result['access_token']

    def upload_json_file(self, filename: str):
        """
        Uploads the given file using the ingress api.
        """
        logger.debug("upload_json_file is called")
        files = {'file': open(filename, 'rb')}

        response = requests.post(
            url=f"{self.host}/uploadfile",
            files=files,
            headers={'Authorization': 'Bearer ' + self.get_access_token()}
        )

        blob_service_client = BlobServiceClient(account_url='https://energinetstorage.blob.core.windows.net', credential=MyCredential(
                token=self.get_access_token(),
                expires_on=int(1000 + datetime.datetime.now().timestamp()) # probably not quite right
            ))

        account_info = blob_service_client.list_containers()

        logger.debug(account_info)
        logger.debug(response.json())

        print(list(account_info))


def main():
    """
    Uploads a file to the DataPlatform.
    """
    client = Client()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    filename = f'{dir_path}/test_file.json'

    client.upload_json_file(filename)


if __name__ == '__main__':
    main()
