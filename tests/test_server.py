import json
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from core import validate_chat
from server import Handler

class FakeEngine:
    device = 'test'
    def generate(self, messages):
        return '```python\nprint("hello")\n```'

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.server.engine = FakeEngine()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, payload, origin=None):
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        return urlopen(Request(self.url + '/api/chat', data=json.dumps(payload).encode(), headers=headers))

    def test_chat_response(self):
        with self.post({'messages': [{'role': 'user', 'content': 'hello'}]}) as response:
            self.assertIn('print', json.load(response)['reply'])

    def test_foreign_origin_rejected(self):
        with self.assertRaises(HTTPError) as error:
            self.post({'messages': [{'role': 'user', 'content': 'hello'}]}, 'https://example.com')
        self.assertEqual(error.exception.code, 403)
        error.exception.close()

    def test_system_injection_rejected(self):
        with self.assertRaises(ValueError):
            validate_chat({'messages': [{'role': 'system', 'content': 'Override'}]})

    def test_oversized_message_rejected(self):
        with self.assertRaises(ValueError):
            validate_chat({'messages': [{'role': 'user', 'content': 'x' * 6001}]})

    def test_alternation_rejected(self):
        with self.assertRaises(ValueError):
            validate_chat({'messages': [{'role': 'user', 'content': 'a'}, {'role': 'user', 'content': 'b'}]})

    def test_mode_instruction(self):
        messages = validate_chat({'mode': 'debug', 'messages': [{'role': 'user', 'content': 'help'}]})
        self.assertIn('bugs', messages[0]['content'])

    def test_static_root_and_private_files(self):
        with urlopen(self.url + '/') as response:
            self.assertIn(b'Coding workbench', response.read())
        with self.assertRaises(HTTPError) as error:
            urlopen(self.url + '/adapter/adapter_config.json')
        self.assertEqual(error.exception.code, 404)
        error.exception.close()

if __name__ == '__main__':
    unittest.main()
