import json
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, Timeout
from datetime import datetime


API_HOST = 'api.thecallr.com'
API_URL = 'https://{url}/'.format(url=API_HOST)

API_TIMEOUT = 10
API_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
API_ERRORS = {
    401: 'Authentication failed',
    205: 'This Voice App cannot be assigned a DID',
    100: 'This feature is not allowed. Please contact the support',
    115: 'File not found',
    150: 'Missing property',
    1000: 'SMS routing error',
    151: 'Invalid property value',
}


"""
Utils and decorators.
"""


class TheCallrApiException(Exception):
    pass


def _clean_response(func, *args, **kwargs):
    try:
        request = func(*args, **kwargs)
    except RequestException:
        raise TheCallrApiException('The API request cannot been made')
    else:
        rsc = request.status_code

        # Check returned status code and raise exception if any
        if rsc is not 200:
            if rsc in API_ERRORS:
                raise TheCallrApiException(API_ERRORS[rsc])
            elif rsc is 110:
                return None
            else:
                raise TheCallrApiException('Unknown error from API (%s)' % rsc)

        # The request is valid, now check if it succeed
        content = request.json()
        if 'error' in content:
            raise TheCallrApiException(content['error']['message'])

        # The request is valid, and it succeed
        return content['result']


def _json(func):
    def inner(*args, **kwargs):
        return _clean_response(func, *args, **kwargs)
    return inner


def _string(func):
    def inner(*args, **kwargs):
        data = _clean_response(func, *args, **kwargs)
        if data:
            return str(data)
        return None
    return inner


def _int(func):
    def inner(*args, **kwargs):
        data = _clean_response(func, *args, **kwargs)
        if data:
            return int(data)
        return None
    return inner


def _float(func):
    def inner(*args, **kwargs):
        data = _clean_response(func, *args, **kwargs)
        if data:
            return float(data)
        return None
    return inner


def _bool(func):
    def inner(*args, **kwargs):
        data = _clean_response(func, *args, **kwargs)
        if data:
            return bool(data)
        return None
    return inner


def datetime_format(timestamp):
    return datetime.fromtimestamp(int(timestamp)).strftime(API_DATE_FORMAT)



"""
Main class that needs to be instanciated to access the API.
"""


class TheCallrApi(object):
    """
    Wrapper for JSON-RPC 2.0 TheCallr API.
    """
    def __init__(self, login, password, timeout=API_TIMEOUT):
        """
        When you subscribed to TheCallr products, you should have received
        credentials (aka login and password).
        """
        self.login = login
        self.password = password
        self.timeout = timeout
        self.seq = 0

        self.analytics = _Analytics(self)
        self.apps = None
        self.billing = _Billing(self)
        self.cdr = None
        self.list = None
        self.media = _Media(self)
        self.sms = _SMS(self)
        self.system = _System(self)
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

        self.seq += 1

        req_method = getattr(requests, type.lower())

        try:
            return req_method(API_URL,
                              auth=HTTPBasicAuth(self.login, self.password),
                              headers=headers,
                              data=json.dumps(data),
                              timeout=self.timeout)
        except Timeout as e:
            raise TheCallrApiException(e)


"""
API services.
"""


class _Service(object):
    def __init__(self, manager):
        self.manager = manager


class _Analytics(_Service):
    class Calls(_Service):
        """
        Calls analytics.
        """
        @_json
        def cli_countries(self, sort, dfrom, dto, limit):
            return self.manager.call('POST', 'analytics/calls.cli_countries',
                                     sort, dfrom, dto, limit)

        @_json
        def history(self, caller, to):
            return self.manager.call('POST', 'analytics/calls.history',
                                     caller, to)

        @_json
        def inbound_did(self, sort, dfrom, dto, limit):
            return self.manager.call('POST', 'analytics/calls.inbound_did',
                                     sort, dfrom, dto, limit)

        @_json
        def outbound_countries(self, sort, dfrom, dto, limit):
            return self.manager.call('POST',
                                     'analytics/calls.outbound_countries',
                                     sort, dfrom, dto, limit)

        @_json
        def outbound_destinations(self, sort, dfrom, dto, limit):
            return self.manager.call('POST',
                                     'analytics/calls.outbound_destinations',
                                     sort, dfrom, dto, limit)

        @_json
        def summary(self, dfrom, dto):
            return self.manager.call('POST', 'analytics/calls.summary',
                                     dfrom, dto)

        @_json
        def top_apps(self, type, sort, dfrom, dto, limit):
            return self.manager.call('POST', 'analytics/calls.top_apps',
                                     type, sort, dfrom, dto, limit)

    class SMS(_Service):
        """
        SMS analytics.
        """
        @_json
        def history(self, dfrom, dto):
            return self.manager.call('POST', 'analytics/sms.history',
                                     dfrom, dto)

        @_json
        def history_out(self, dfrom, dto, fields):
            return self.manager.call('POST', 'analytics/sms.history_out',
                                     dfrom, dto, fields)

        @_json
        def history_out_by_status(self, dfrom, dto):
            return self.manager.call('POST',
                                     'analytics/sms.history_out_by_status',
                                     dfrom, dto)

        @_json
        def summary(self, dfrom, dto):
            return self.manager.call('POST', 'analytics/sms.summary',
                                     dfrom, dto)

        @_json
        def summary_out(self, dfrom, dto, fields):
            return self.manager.call('POST', 'analytics/sms.summary_out',
                                     dfrom, dto, fields)

        @_json
        def summary_out_by_status(self, dfrom, dto):
            return self.manager.call('POST',
                                     'analytics/sms.summary_out_by_status',
                                     dfrom, dto)

    def __init__(self, manager):
        super(_Analytics, self).__init__(manager)
        self.calls = self.Calls(self.manager)
        self.sms = self.SMS(self.manager)


class _Media(_Service):
    class Library(_Service):
        @_int
        def create(self, name):
            return self.manager.call('POST', 'media/library.create', name)

        @_json
        def get(self, id):
            return self.manager.call('POST', 'media/library.get', id)

    class TTS(_Service):
        @_json
        def get_voice_list(self):
            return self.manager.call('POST', 'media/tts.get_voice_list')

        @_bool
        def set_content(self, media_id, text, voice, rate=50):
            return self.manager.call('POST', 'media/tts.set_content',
                                     media_id, text, voice,
                                     {'rate': rate})

    @_json
    def get_quota_status(self):
        return self.manager.call('POST', 'media.get_quota_status')

    def __init__(self, manager):
        super(_Media, self).__init__(manager)
        self.library = self.Library(self.manager)
        self.tts = self.TTS(self.manager)


class _SMS(_Service):
    """
    Send and list SMS.
    """
    @_json
    def get(self, id):
        return self.manager.call('POST', 'sms.get', id)

    @_json
    def get_count_for_body(self, body):
        return self.manager.call('POST', 'sms.get_count_for_body', body)

    @_json
    def get_list(self, type, sender, to):
        return self.manager.call('POST', 'sms.get_list', type, sender, to)

    @_json
    def get_settings(self):
        return self.manager.call('POST', 'sms.get_settings')

    @_string
    def send(self, sender, to, body, flash=False):
        return self.manager.call('POST', 'sms.send', sender, to, body,
                                 {'flash_message': flash})

    @_json
    def set_settings(self, settings):
        return self.manager.call('POST', 'sms.set_settings', settings)


class _System(_Service):
    """
    System service.
    """
    @_int
    def get_timestamp(self):
        return self.manager.call('POST', 'system.get_timestamp')


class _Billing(_Service):
    """
    Billing service.
    """
    @_float
    def get_prepaid_credit(self):
        return self.manager.call('POST', 'billing.get_prepaid_credit')