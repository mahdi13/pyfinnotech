import base64

from pyfinnotech.const import ALL_SCOPE_CLIENT_CREDENTIALS


class Token:
    __token_type__ = 'CODE'

    scopes = []

    def __init__(self):
        pass

    def is_valid(self):
        raise NotImplementedError()

    def revoke(self):
        raise NotImplementedError()

    def refresh(self):
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

    def is_valid(self):
        raise True

    def revoke(self):
        raise NotImplementedError()

    def refresh(self):
        pass

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


class AccessToken:
    __token_type__ = 'CODE'

    def is_valid(self):
        raise NotImplementedError()

    def revoke(self):
        raise NotImplementedError()

    @property
    def user(self):
        raise NotImplementedError()
