from nanohttp import RestController, json, HttpNotFound

valid_mock_cards = [
    '0000000000000000'
]


class MockCardController(RestController):

    @json
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


class FinnotechRootMockController(RestController):
    cards = MockCardController()

    def __call__(self, *remaining_paths):
        if remaining_paths[0] == 'oak':
            if remaining_paths[1] == 'v2':
                if remaining_paths[2] == 'clients':
                    from pyfinnotech.tests.herlper import mock_client_id
                    if remaining_paths[3] == mock_client_id:
                        if remaining_paths[4] == 'cards':
                            return super().__call__(*remaining_paths[4:])

        raise HttpNotFound()
