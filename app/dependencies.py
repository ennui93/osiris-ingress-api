"""
Contains dependencies used in several places of the application.
"""
import time

from azure.core.credentials import AccessToken


CONFIG_FILE_LOCATIONS = ['conf.ini', '/etc/osiris/conf.ini']


class AzureCredential:  # pylint: disable=too-few-public-methods
    """
    Represents a Credential object. This is a hack to use a access token
    received from a client.
    """

    # NOTE: This doesn't necessarily correspond to the token lifetime,
    # however it doesn't matter as it gets recreated per request
    EXPIRES_IN = 1000

    def __init__(self, token: str):
        self.token = token
        self.expires_on = self.EXPIRES_IN + time.time()

    def get_token(self, *scopes, **kwargs):  # pylint: disable=unused-argument
        """
        Returns an AcccesToken object.
        """
        return AccessToken(self.token, self.expires_on)
