import base64

import ujson

from pyfinnotech.const import ALL_SCOPE_CLIENT_CREDENTIALS


class Token:
    __token_type__ = 'CODE'

    scopes = []

    def __init__(self):
        pass

    @property
    def is_valid(self):
        raise NotImplementedError()

    def revoke(self):
        raise NotImplementedError()

    def refresh(self, *args, **kwargs):
        raise NotImplementedError()

    def generate_authorization_header(self):
        raise NotImplementedError()


class ClientCredentialToken(Token):
    __token_type__ = 'CODE'

    def __init__(self, **kwargs):
        super().__init__()
        self.token = kwargs.get('value', None)
        self.refresh_token = kwargs.get('refreshToken', None)
        self.creation_date = kwargs.get('creationDate', None)
        self.life_time = kwargs.get('lifeTime', None)
        self.scopes = kwargs.get('scopes', None)

    @property
    def is_valid(self):
        return True

    def revoke(self):
        raise NotImplementedError()

    def refresh(self, http_client):
        # TODO: We should ues refresh token, but it's not based on RFC, so it's almost unusable
        new_token = self.__class__.fetch(http_client)
        self.token = new_token.token
        self.refresh_token = new_token.refresh_token
        self.creation_date = new_token.creation_date
        self.life_time = new_token.life_time
        self.scopes = new_token.scopes

    @classmethod
    def load(cls, raw_token, refresh_token=None):
        payload = ujson.loads(base64.decodebytes((raw_token.split('.')[1] + '==').encode()).decode())
        payload.setdefault('refreshToken', refresh_token)
        return cls(value=raw_token, **payload)

    def generate_authorization_header(self):
        return {
            'Authorization': f'Bearer {self.token}'
        }

    # noinspection PyProtectedMember
    @classmethod
    def fetch(cls, http_client):
        """
        https://devbeta.finnotech.ir/v2/boomrang-get-clientCredential-token.html
        :return:
        """
        url = '/dev/v2/oauth2/token'

        encoded_basic_authentication = base64 \
            .encodebytes(f'{http_client.client_id}:{http_client.client_secret}'.encode()) \
            .decode().strip()
        return cls(**http_client._execute(
            uri=url,
            body={
                "grant_type": "client_credentials",
                "nid": http_client.client_national_id,
                "scopes": ','.join(list(set(http_client.scopes) & set(ALL_SCOPE_CLIENT_CREDENTIALS)))
            },
            method='post',
            headers={'Authorization': f'Basic {encoded_basic_authentication}'}
        ).get('result'))


class AccessToken(Token):
    def refresh(self):
        pass

    def generate_authorization_header(self):
        pass

    __token_type__ = 'CODE'

    @property
    def is_valid(self):
        raise NotImplementedError()

    def revoke(self):
        raise NotImplementedError()

    @property
    def user(self):
        raise NotImplementedError()
