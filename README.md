# pyfinnotech

Python Finnotech Api Client

[![Build Status](https://travis-ci.org/mahdi13/pyfinnotech.svg?branch=master)](https://travis-ci.org/mahdi13/pyfinnotech)

Install using pypi:
```shell script
pip install pyfinnotech
```

## Usage
Initialize api client:
```python
from pyfinnotech import FinnotechApiClient

api_client = FinnotechApiClient(client_id='MY-CLIENT-ID', client_secret='MY-CLIENT-SECRET')
```

### Banking
Inquire Sheba:
```python
result = api_client.iban_inquiry('IR910800005000115426432001')
```

Inquire Card:
```python
result = api_client.card_inquiry('0000000000000000')
```
