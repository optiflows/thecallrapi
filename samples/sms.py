#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from thecallrapi import TheCallrApi


API_LOGIN = '__LOGIN__'
API_PASSWORD = '__PASSWORD__'


if __name__ == "__main__":
    api = TheCallrApi(API_LOGIN, API_PASSWORD)

    resp = api.sms.send(sender='THECALLR', to='<phone number>', body='woof woof')
    print resp
    id = resp['result']

    time.sleep(3)

    resp = api.sms.get(id=id)
    print resp
    status = resp['status']
