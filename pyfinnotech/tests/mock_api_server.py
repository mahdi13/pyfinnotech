import base64
import functools

from nanohttp import RestController, json, HttpNotFound, context, HttpUnauthorized, HttpBadRequest

from pyfinnotech.const import ALL_SCOPE_CLIENT_CREDENTIALS

valid_mock_cards = [
    '0000000000000000'
]

valid_mock_ibans = [
    'IR910800005000115426432001'
]

valid_mock_client_id = 'mock-app'
valid_mock_client_secret = 'mock-secret'

valid_mock_client_credential_tokens = [
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Im1vY2stYXBwIn0.maxHiBX70CtQM_p_hNsv0RLmfhj_eg7bmRuN6We9HEU'
]

invalid_mock_client_credential_tokens = [
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInZhbGlkIjpmYWxzZX0.eyJpZCI6Im1vY2stYXBwIn0'
    '.9AxqC62m5tRc9Jxy5Mfj58YpgO2ANfcWhsm6LNMtgpo'
]

valid_mock_client_credential_refresh_tokens = [
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Im1vY2stYXBwIn0.W1sHpsKjNZrOg73ye0fVllbkzooK6tiIZl6TjiRsUlU'
]

invalid_mock_client_credential_refresh_tokens = [
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Im1vY2stYXBwIn0.W1sHpsKjNZrOg73ye0fVllbkzooK6tiIZl6TjiRsUlU'
]


def authorize_client_credential(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'HTTP_AUTHORIZATION' not in context.environ:
            raise HttpUnauthorized()

        encoded_token = context.environ['HTTP_AUTHORIZATION']
        if encoded_token is None or not encoded_token.strip().strip('Bearer').strip():
            raise HttpUnauthorized()
        encoded_token = encoded_token.strip().strip('Bearer').strip()

        if encoded_token in valid_mock_client_credential_tokens:
            return func(*args, **kwargs)

        if encoded_token in invalid_mock_client_credential_tokens:
            raise HttpUnauthorized()
        raise HttpUnauthorized()

    return wrapper


def authorize_basic(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'HTTP_AUTHORIZATION' not in context.environ:
            raise HttpUnauthorized()

        encoded_token = context.environ['HTTP_AUTHORIZATION']
        if encoded_token is None or not encoded_token.strip().strip('Basic').strip():
            raise HttpUnauthorized()
        encoded_token = encoded_token.strip().strip('Basic').strip()

        try:
            credential = base64.decodebytes(encoded_token.encode()).decode().split(":")
            if credential[0] == valid_mock_client_id and credential[1] == valid_mock_client_secret:
                return func(*args, **kwargs)
        except:
            raise HttpUnauthorized()

        raise HttpUnauthorized()

    return wrapper


class MockOauthController(RestController):

    @json
    @authorize_basic
    def post(self, r1: str = None):
        if r1 == 'token':
            return {
                "result": {
                    "value": valid_mock_client_credential_tokens[0]
                    , "scopes": [
                        ','.join(ALL_SCOPE_CLIENT_CREDENTIALS)
                    ]
                    , "lifeTime": 864000000
                    , "creationDate": "13970730111355"
                    ,
                    "refreshToken": valid_mock_client_credential_refresh_tokens
                }
                , "status": "DONE"
            }


class MockCardController(RestController):

    @json
    @authorize_client_credential
    def get(self, card_number: str = None):
        if card_number in valid_mock_cards:
            return {
                "result": {
                    "destCard": "xxxx-xxxx-xxxx-3899"
                    , "name": "علی آقایی"
                    , "result": "0"
                    , "description": "موفق"
                    , "doTime": "1396/06/15 12:32:04"
                }
                , "status": "DONE"
                , "trackId": "get-cardInfo-0232"
            }

        raise HttpBadRequest()

class MockIbanController(RestController):

    @json
    @authorize_client_credential
    def get(self):
        iban = context.query_string.get('iban')
        if iban in valid_mock_ibans:
            return {
                "trackId": "get-iban-inquiry-029",
                "result": {
                    "IBAN": "IR910800005000115426432001"
                    , "bankName": "قرض الحسنه رسالت"
                    , "deposit": "10.6423499.1"
                    , "depositDescription": "حساب فعال است"
                    , "depositComment": "سپرده حقيقي قرض الحسنه پس انداز حقيقي ريالی شیما کیایی"
                    , "depositOwners": [
                        {
                            "firstName": "شیما"
                            , "lastName": "کیایی"
                        }
                    ],
                    "depositStatus": "02",
                    "errorDescription": "بدون خطا"
                },
                "status": "DONE"
            }

        raise HttpBadRequest()

class FinnotechRootMockController(RestController):
    cards = MockCardController()
    ibanInquiry = MockIbanController()
    oauth2 = MockOauthController()

    def __call__(self, *remaining_paths):
        if remaining_paths[0] == 'oak':
            if remaining_paths[1] == 'v2':
                if remaining_paths[2] == 'clients':
                    from pyfinnotech.tests.helper import valid_mock_client_id
                    if remaining_paths[3] == valid_mock_client_id:
                        if remaining_paths[4] in ['cards', 'ibanInquiry']:
                            return super().__call__(*remaining_paths[4:])

        elif remaining_paths[0] == 'dev':
            if remaining_paths[1] == 'v2':
                if remaining_paths[2] == 'oauth2':
                    return super().__call__(*remaining_paths[2:])

        raise HttpNotFound()
