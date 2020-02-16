class Token:
    __token_type__ = 'CODE'

    def __init__(self, http_client):
        self.http_client = http_client

    def is_valid(self):
        raise NotImplementedError()

    def revoke(self):
        raise NotImplementedError()

    def refresh(self):
        raise NotImplementedError()

    @property
    def scopes(self):
        raise NotImplementedError()

    def generate_authorization_header(self):
        raise NotImplementedError()


class ClientCredentialToken(Token):
    __token_type__ = 'CODE'

    def __init__(self, http_client, token):
        super().__init__(http_client)
        self.token = token

    def is_valid(self):
        raise NotImplementedError()

    @property
    def scopes(self):
        raise NotImplementedError()

    def revoke(self):
        raise NotImplementedError()

    def refresh(self):
        pass

    def generate_authorization_header(self):
        return {
            'CLIENT-CREDENTIAL': self.token
        }


class AccessToken:
    __token_type__ = 'CODE'

    def is_valid(self):
        raise NotImplementedError()

    def revoke(self):
        raise NotImplementedError()

    def revoke(self):
        raise NotImplementedError()

    @property
    def user(self):
        raise NotImplementedError()
