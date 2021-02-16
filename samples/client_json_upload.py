
"""
This module demonstrates how a client can upload an json file to the DataPlatform using the ingress api.
"""

import logging
import logging.config
import os

import configparser
import requests
import msal  # pylint: disable=import-error

logging.config.fileConfig(fname='log.conf')
logger = logging.getLogger(__file__)


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

    def upload_json_file(self, filename: str, directory: str):
        """
        Uploads the given file using the ingress api.
        """
        logger.debug("upload_json_file is called")
        files = {'file': open(filename, 'rb')}

        response = requests.post(
            url=f"{self.host}/uploadfile/{directory}",
            files=files,
            headers={'Authorization': self.get_access_token()}
        )

        logger.debug(response)


def main():
    """
    Uploads a file to the DataPlatform.
    """
    client = Client()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    filename = f'{dir_path}/test_file.json'
    directory = '123456'

    client.upload_json_file(filename, directory)


if __name__ == '__main__':
    main()
