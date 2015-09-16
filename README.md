# TheCallr API
[![pypi version](http://img.shields.io/pypi/v/thecallrapi.svg)](https://pypi.python.org/pypi/thecallrapi) [![pypi download week](http://img.shields.io/pypi/dw/thecallrapi.svg)](https://pypi.python.org/pypi/thecallrapi)

Python module to manage TheCallr's API

It currently wraps most of the services available in [http://thecallr.com/docs/api/services/sms/](their documentation) simply using attributes.
An example of call :

```python
from thecallrapi import TheCallrApi

api = TheCallrApi('login', 'password')
status, body = yield from api.sms.send('sender_name', 'phone_number', 'body')
```