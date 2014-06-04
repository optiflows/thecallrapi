import requests
import json
from requests.auth import HTTPBasicAuth



API_HOST = 'api.thecallr.com'
API_URL = 'https://{url}/'.format(url=API_HOST)


class Api(object):
    """
    Wrapper for JSON-RPC 2.0 TheCallr API.
    """

    def __init__(self, login, password):
        """
        When you subscribed to TheCallr products, you should have received
        credentials (aka login and password).
        """
        self.login = login
        self.password = password
        self.seq = 0

    def call(self, type, method, *args):
        headers = {
            'Content-Type': 'application/json-rpc; charset=utf-8'
        }

        data = {
            'jsonrpc': '2.0',
            'id': self.seq,
            'method': method,
            'params': [args]
        }

        self.seq = self.seq + 1

        req_method = getattr(requests, type.lower())
        return req_method(API_URL,
                          auth=HTTPBasicAuth(self.login, self.password),
                          headers=headers,
                          data=json.dumps(data))

    def sms_get(self, id):
        return self.call('GET', 'sms.get', id)