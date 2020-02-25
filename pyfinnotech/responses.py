class BaseFinnotechResponse:
    def __init__(self, payload):
        self.payload = payload


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
