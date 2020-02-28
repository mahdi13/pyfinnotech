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


class NationalIdVerification(BaseFinnotechResponse):

    @property
    def national_code(self):
        return self.payload.get('nationalCode', None)

    @property
    def birth_date(self):
        return self.payload.get('birthDate', None)

    @property
    def status(self):
        return self.payload.get('status', None)

    @property
    def full_name(self):
        return self.payload.get('fullName', None)

    @property
    def first_name(self):
        return self.payload.get('firstName', None)

    @property
    def last_name(self):
        return self.payload.get('lastName', None)

    @property
    def full_name_similarity(self):
        return self.payload.get('fullNameSimilarity', None)

    @property
    def first_name_similarity(self):
        return self.payload.get('firstNameSimilarity', None)

    @property
    def last_name_similarity(self):
        return self.payload.get('lastNameSimilarity', None)

    @property
    def gender(self):
        return self.payload.get('gender', None)

    @property
    def gender_similarity(self):
        return self.payload.get('genderSimilarity', None)

    @property
    def father_name(self):
        return self.payload.get('fatherName', None)

    @property
    def father_name_similarity(self):
        return self.payload.get('fatherNameSimilarity', None)

    @property
    def is_alive(self):
        return self.payload.get('deathStatus', None) == 'زنده'

    @property
    def is_valid(self):
        return self.status == 'DONE'

    @property
    def description(self):
        return self.payload.get('description', None)
