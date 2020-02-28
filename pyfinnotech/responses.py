class BaseFinnotechResponse:
    def __init__(self, payload):
        self.payload = payload

    @property
    def track_id(self):
        return self.payload.get('trackId', None)


class CardInquiryResponse(BaseFinnotechResponse):

    @property
    def is_valid(self):
        return self.payload.get('result', None) == '0'

    @property
    def full_name(self):
        return self.payload.get('name', None)


class IbanInquiryResponse(BaseFinnotechResponse):

    @property
    def is_valid(self):
        return self.payload.get('depositStatus', None) == '02'

    @property
    def owner_first_name(self):
        # FIXME: What should we do with cards with more than one owner?
        if len(self.payload.get('depositOwners')) != 1:
            return None
        return self.payload.get('depositOwners')[0].get('firstName', None)

    @property
    def owner_last_name(self):
        if len(self.payload.get('depositOwners')) != 1:
            return None
        return self.payload.get('depositOwners')[0].get('lastName', None)


class StandardReliabilitySms(BaseFinnotechResponse):

    @property
    def result(self):
        return self.payload.get('result', None)


class AuthorizationTokenSmsSend(BaseFinnotechResponse):

    @property
    def sms_sent(self):
        return self.payload.get('smsSent', None)


class AuthorizationSmsVerify(BaseFinnotechResponse):

    @property
    def code(self):
        return self.payload.get('code', None)


class AuthorizationSmsToken(BaseFinnotechResponse):

    @property
    def client_id(self):
        return self.payload.get('clientId', None)

    @property
    def scopes(self):
        return self.payload.get('scopes', None)

    @property
    def deposits(self):
        return self.payload.get('deposits', None)

    @property
    def lifetime(self):
        return self.payload.get('lifetime', None)

    @property
    def bank(self):
        return self.payload.get('bank', None)

    @property
    def type(self):
        return self.payload.get('type', None)

    @property
    def creation_date(self):
        return self.payload.get('creationDate', None)

    @property
    def user_national_id(self):
        return self.payload.get('user_national_id', None)

    @property
    def auth_type(self):
        return self.payload.get('auth_type', None)

    @property
    def refresh_token(self):
        return self.payload.get('refreshToken', None)

    @property
    def access_token(self):
        return self.payload.get('value', None)
