from pyfinnotech.tests.helper import ApiClientTestCase
from pyfinnotech.tests.mock_api_server import valid_mock_cards

client_invalid_mock_cards = [
    '000000000000000',
    'A000000000000000',
]


class CardValidationTestCase(ApiClientTestCase):
    def test_server_validate_card(self):
        for c in valid_mock_cards:
            self.assertEqual('0', self.api_client.card_inquiry(c).get('result').get('result'))

    def test_client_validate_card(self):
        for c in client_invalid_mock_cards:
            with self.assertRaises(ValueError):
                self.assertEqual('0', self.api_client.card_inquiry(c).get('result').get('result'))
