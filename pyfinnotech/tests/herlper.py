import socket
import unittest

from nanohttp import quickstart

from pyfinnotech import FinnotechApiClient
from pyfinnotech.tests.mock_api_server import FinnotechRootMockController

mock_client_id = 'mock-api-client'
mock_client_secret = 'mock-api-secret'


class ApiClientTestCase(unittest.TestCase):
    _server_shutdown = None
    api_client = None

    @classmethod
    def find_free_port(cls):
        s = socket.socket()
        s.bind(('', 0))  # Bind to a free port provided by the host.
        port = s.getsockname()[1]  # Return the port number assigned.
        s.close()
        return port

    @classmethod
    def setUpClass(cls):
        server_port = cls.find_free_port()
        cls._server_shutdown = quickstart(
            controller=FinnotechRootMockController(),
            port=server_port,
            block=False
        )
        cls.api_client = FinnotechApiClient(
            client_id=mock_client_id,
            client_secret=mock_client_secret,
            base_url=f'http://localhost:{server_port}'
        )
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls._server_shutdown()
        super().tearDownClass()
