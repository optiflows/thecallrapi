import aiohttp
from aiohttp.helpers import BasicAuth
import asyncio
import logging
import json


log = logging.getLogger(__name__)

UNKNOWN_ERROR = 'Unknown error'
NO_CONNECTION_ERROR = 'No connection'
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


"""
Main class that needs to be instanciated to access the API.
"""


class TheCallrApi(object):
    """
    Wrapper for JSON-RPC 2.0 TheCallr API.
    """

    API_URL = 'https://api.thecallr.com'

    def __init__(self, login, password):
        """
        When you subscribed to TheCallr products, you should have received
        credentials (aka login and password).
        """
        self.auth = BasicAuth(login, password)
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

    @asyncio.coroutine
    def call(self, httpmethod, method, *args):
        """
        Call and parse TheCallr json-rpc API.
        Returns (status, json).
        """
        self.seq += 1
        headers = {'Content-Type': 'application/json-rpc; charset=utf-8'}
        data = {
            'jsonrpc': '2.0',
            'id': self.seq,
            'method': method,
            'params': list(args)
        }

        log.debug('method : %s', method)
        log.debug('sending data : %s', data)

        try:
            response = yield from aiohttp.request(
                httpmethod,
                self.API_URL,
                data=json.dumps(data),
                headers=headers,
                auth=self.auth
            )
        except (aiohttp.HttpProcessingError,
                aiohttp.ServerDisconnectedError,
                aiohttp.ClientOSError):
            status = 500
            body = NO_CONNECTION_ERROR
        else:
            status = response.status
            if status == 200:
                body = yield from response.json()
                if 'error' in body:
                    body = body['error']
                    status = 400
                else:
                    body = {'result': body['result']}
            elif status in API_ERRORS:
                body = API_ERRORS[status]
            else:
                body = UNKNOWN_ERROR

        return status, body


"""
API services.
"""


class _Service(object):
    def __init__(self, api):
        self.api = api


class _Analytics(_Service):

    def __init__(self, api):
        super(_Analytics, self).__init__(api)
        self.calls = self.Calls(self.api)
        self.sms = self.SMS(self.api)

    class Calls(_Service):
        """
        Calls analytics.
        """
        def cli_countries(self, sort, dfrom, dto, limit):
            return (yield from self.api.call(
                'POST', 'analytics/calls.cli_countries',
                sort, dfrom, dto, limit
            ))

        def history(self, caller, to):
            return (yield from self.api.call(
                'POST', 'analytics/calls.history', caller, to
            ))

        def inbound_did(self, sort, dfrom, dto, limit):
            return (yield from self.api.call(
                'POST', 'analytics/calls.inbound_did',
                sort, dfrom, dto, limit
            ))

        def outbound_countries(self, sort, dfrom, dto, limit):
            return (yield from self.api.call(
                'POST', 'analytics/calls.outbound_countries',
                sort, dfrom, dto, limit
            ))

        def outbound_destinations(self, sort, dfrom, dto, limit):
            return (yield from self.api.call(
                'POST', 'analytics/calls.outbound_destinations',
                sort, dfrom, dto, limit
            ))

        def summary(self, dfrom, dto):
            return (yield from self.api.call(
                'POST', 'analytics/calls.summary', dfrom, dto
            ))

        def top_apps(self, atype, sort, dfrom, dto, limit):
            return (yield from self.api.call(
                'POST', 'analytics/calls.top_apps',
                atype, sort, dfrom, dto, limit
            ))

    class SMS(_Service):
        """
        SMS analytics.
        """
        def history(self, dfrom, dto):
            return (yield from self.api.call(
                'POST', 'analytics/sms.history', dfrom, dto
            ))

        def history_out(self, dfrom, dto, fields):
            return (yield from self.api.call(
                'POST', 'analytics/sms.history_out', dfrom, dto, fields
            ))

        def history_out_by_status(self, dfrom, dto):
            return (yield from self.api.call(
                'POST', 'analytics/sms.history_out_by_status', dfrom, dto
            ))

        def summary(self, dfrom, dto):
            return (yield from self.api.call(
                'POST', 'analytics/sms.summary', dfrom, dto
            ))

        def summary_out(self, dfrom, dto, fields):
            return (yield from self.api.call(
                'POST', 'analytics/sms.summary_out', dfrom, dto, fields
            ))

        def summary_out_by_status(self, dfrom, dto):
            return (yield from self.api.call(
                'POST', 'analytics/sms.summary_out_by_status', dfrom, dto
            ))


class _Media(_Service):

    def __init__(self, api):
        super(_Media, self).__init__(api)
        self.library = self.Library(self.api)
        self.tts = self.TTS(self.api)

    def get_quota_status(self):
        return (yield from self.api.call('POST', 'media.get_quota_status'))

    class Library(_Service):
        def create(self, name):
            return (yield from self.api.call(
                'POST', 'media/library.create', name
            ))

        def get(self, lib_id):
            return (yield from self.api.call(
                'POST', 'media/library.get', lib_id
            ))

    class TTS(_Service):
        def get_voice_list(self):
            return (yield from self.api.call(
                'POST', 'media/tts.get_voice_list'
            ))

        def set_content(self, media_id, text, voice, rate=50):
            return (yield from self.api.call(
                'POST', 'media/tts.set_content',
                media_id, text, voice, {'rate': rate}
            ))


class _SMS(_Service):
    """
    Send and list SMS.
    """
    def get(self, sms_id):
        return (yield from self.api.call('POST', 'sms.get', sms_id))

    def get_count_for_body(self, body):
        return (yield from self.api.call(
            'POST', 'sms.get_count_for_body', body
        ))

    def get_list(self, stype, sfrom, sto):
        return (yield from self.api.call(
            'POST', 'sms.get_list', stype, sfrom, sto
        ))

    def get_settings(self):
        return (yield from self.api.call('POST', 'sms.get_settings'))

    def send(self, sender, to, body, flash=False):
        return (yield from self.api.call(
            'POST', 'sms.send', sender, to, body, {'flash_message': flash}
        ))

    def set_settings(self, settings):
        return (yield from self.api.call('POST', 'sms.set_settings', settings))


class _System(_Service):
    """
    System service.
    """
    def get_timestamp(self):
        return (yield from self.api.call('POST', 'system.get_timestamp'))


class _Billing(_Service):
    """
    Billing service.
    """
    def get_prepaid_credit(self):
        return (yield from self.api.call('POST', 'billing.get_prepaid_credit'))
