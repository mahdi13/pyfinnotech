# pyfinnotech

Python Finnotech Api Client

[![Build Status](https://travis-ci.org/mahdi13/pyfinnotech.svg?branch=master)](https://travis-ci.org/mahdi13/pyfinnotech)
[![Build Status](https://badge.fury.io/py/pyfinnotech.svg)](https://pypi.org/project/pyfinnotech/)
[![Build Status](https://pypip.in/d/pyfinnotech/badge.png)](https://pypi.org/project/pyfinnotech/)
[![codecov](https://codecov.io/gh/mahdi13/pyfinnotech/branch/master/graph/badge.svg)](https://codecov.io/gh/mahdi13/pyfinnotech)


Install using pypi:
```shell script
pip install pyfinnotech
```

## Finnotech
Home Page: https://finnotech.ir/  
Api Doc: https://apibeta.finnotech.ir/  
Sandbox Dashboard Url: https://sandboxbeta.finnotech.ir/
Mainnet Dashboard Url: https://devbeta.finnotech.ir/

## Usage
Initialize api client:
```python
from pyfinnotech import FinnotechApiClient

api_client = FinnotechApiClient(client_id='MY-CLIENT-ID', client_secret='MY-CLIENT-SECRET', client_national_id='0067408595')
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

### Sms Authorization Token

Retrieve sms authorization token:
```python
sms_facility_access_token = None
result1 = FacilitySmsAccessTokenToken.request_sms(
    api_client,
    target_phone='09300000000',
    scopes=[SCOPE_FACILITY_SMS_NID_VERIFICATION_GET, ],
    redirect_url='http://localhost/finnotech-callback'
)
tracking_id = result1.track_id
print(ujson.dumps(result1.payload, indent=4, sort_keys=True, ensure_ascii=False))

otp = input("Enter otp: ").strip()
result2 = FacilitySmsAccessTokenToken.verify_sms(
    api_client,
    target_phone='09300000000',
    track_id=tracking_id,
    target_national_id='0067408595',
    otp=otp
)
print(ujson.dumps(result2.payload, indent=4, sort_keys=True, ensure_ascii=False))

code = result2.code
token = FacilitySmsAccessTokenToken.request_token(
    api_client,
    code=code,
    redirect_url='http://localhost/finnotech-callback'
)
print(token.token)
```

And for refreshing it:
```python
token.refresh(api_client)
```


### National Id Verification
First retrieve `sms_authorization_token` from the target user
```python
verification_result = api_client.national_id_verification(
        access_token=token,
        birth_date='1365/11/25',
        first_name='سعید',
        national_id='0067408595',
        gender='مرد'
    )
```
