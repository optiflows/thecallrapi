import json
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException


API_HOST = 'api.thecallr.com'
API_URL = 'https://{url}/'.format(url=API_HOST)
API_ERRORS = {
    401: 'Authentication failed',
    205: 'This Voice App cannot be assigned a DID',
    100: 'This feature is not allowed. Please contact the support',
    115: 'File not found',
    150: 'Missing property',
    1000: 'SMS routing error',
    151: 'Invalid property value',
}


class TheCallrApiException(Exception):
    pass


class TheCallrApi(object):
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

        self.apps = None
        self.billing = None
        self.cdr = None
        self.list = None
        self.media = None
        self.sms = _SMS(self)
        self.system = None
        self.thedialr = None

    def call(self, type, method, *args):
        headers = {
            'Content-Type': 'application/json-rpc; charset=utf-8'
        }

        data = {
            'jsonrpc': '2.0',
            'id': self.seq,
            'method': method,
            'params': filter(None, list(args))
        }

        self.seq = self.seq + 1

        req_method = getattr(requests, type.lower())
        return req_method(API_URL,
                          auth=HTTPBasicAuth(self.login, self.password),
                          headers=headers,
                          data=json.dumps(data))


def _clean_response(func, *args, **kwargs):
    try:
        request = func(*args, **kwargs)
    except RequestException:
        raise TheCallrApiException('The API request cannot been made')
    else:
        rsc = request.status_code

        # Check returned status code and raise exceptions if any
        if rsc is not 200:
            if rsc in API_ERRORS:
                raise TheCallrApiException(API_ERRORS[rsc])
            elif rsc is 110:
                return None
            else:
                raise TheCallrApiException('Unknown error from API (%s)' % rsc)
        return request


def _json(func):
    def inner(*args, **kwargs):
        data = _clean_response(func, *args, **kwargs)
        if data:
            json = data.json()
            if 'error' in json:
                raise TheCallrApiException(json['error']['message'])
            return json['result']
        return None
    return inner


def _string(func):
    def inner(*args, **kwargs):
        data = _clean_response(func, *args, **kwargs)
        if data:
            return data.text
        return None
    return inner


class _Service(object):
    def __init__(self, manager):
        self.manager = manager


class _SMS(_Service):
    """
    Send and list SMS.
    """
    @_json
    def get(self, id):
        """
        Params:
            - id (string): SMS ID (hash).
        """
        return self.manager.call('POST', 'sms.get', id)

    @_json
    def get_count_for_body(self, body):
        """
        Params:
            - body (string): Text message.
        """
        return self.manager.call('POST', 'sms.get_count_for_body', body)

    @_json
    def get_list(self, type, sender, to):
        """
        Params:
            - type (string): Type of SMS ('IN' or 'OUT').
            - from (string): Retrieve from date (datetime).
            - to (string): Retrieve to date (datetime).
        """
        return self.manager.call('POST', 'sms.get_list', type, sender, to)

    @_json
    def get_settings(self):
        return self.manager.call('POST', 'sms.get_settings')

    @_json
    def send(self, sender, to, body, flash=False):
        """
        Params:
            - from (string): The SMS sender.
            - to (string): The SMS recipient (International E.164 "+CCNSN").
            - body (string): Text message (UTF-8 JSON strings).
            - options (object): SMS Options. Send NULL to use default values.
        """
        return self.manager.call('POST', 'sms.send', sender, to, body,
                                 {'flash_message': flash})

    @_json
    def set_settings(self, settings):
        """
        Params:
            - settings (object): SMS settings.
        """
        return self.manager.call('POST', 'sms.set_settings', settings)
