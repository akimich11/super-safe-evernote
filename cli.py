import argparse
import requests
import sys
from crypto import ecdh
from crypto.ecc import scalar_mult

ADDRESS = 'http://localhost:8000/'  # 'https://super-safe-evernote-backend.herokuapp.com/'

users = {}
current_username = None


class User:
    def __init__(self, username, jwt=None):
        # Alice generates her own keypair.
        self.private_key, self.public_key = ecdh.make_keypair()
        self.shared_secret = None
        self.jwt = jwt
        self.notes = {}
        self.username = username
        users[self.username] = self


def report_success(response, expected_code=200):
    ok = response.status_code == expected_code
    print('Successful' if ok else 'Failed')
    return ok


def register(args):
    user = User(args.username)
    response = requests.post(ADDRESS + 'auth/register',
                             headers={
                                 'alice_public_key': user.public_key
                             },
                             json={
                                 'email': args.username + '@example.com',
                                 'password': args.password
                             })

    if report_success(response, 201):
        bob_public_key = response.headers['bob_public_key']
        user.shared_secret = scalar_mult(user.private_key, bob_public_key)


def login(args):
    global current_username
    user = users[args.username]
    headers = {'alice_public_key': user.public_key} if user.shared_secret is None else {}

    response = requests.post(ADDRESS + 'auth/jwt/login',
                             data={
                                 'username': args.username + '@example.com',
                                 'password': args.password
                             },
                             headers=headers)
    if report_success(response):
        bob_public_key = response.headers['bob_public_key']
        user.shared_secret = scalar_mult(user.private_key, bob_public_key)
    user.jwt = response.json()['access_token']
    current_username = user.username
    get_notes()


def get_notes(args=None):
    user = users[current_username]
    response = requests.get(ADDRESS + 'get_notes',
                            headers={'Authorization': f'Bearer {user.jwt}'})
    for note in response.json()['message']:
        user.notes[note['name']] = (note['id'], note['message'])
    print('Available notes:', ', '.join(user.notes))


def create(args):
    user = users[current_username]
    response = requests.post(ADDRESS + 'create_note',
                             headers={'Authorization': f'Bearer {user.jwt}'},
                             json={
                                 'name': args.note_name,
                                 'message': args.content
                             })
    if report_success(response):
        note = response.json()['message']
        user.notes[note['name']] = (note['id'], note['message'])


def edit(args):
    user = users[current_username]
    response = requests.post(ADDRESS + 'edit_note/' + str(user.notes[args.note_name][0]),
                             headers={'Authorization': f'Bearer {user.jwt}'},
                             json={
                                 'name': args.note_name,
                                 'message': args.content
                             })
    if report_success(response):
        note = response.json()['message']
        user.notes[note['name']] = (note['id'], note['message'])


def delete(args):
    user = users[current_username]
    response = requests.delete(ADDRESS + 'delete_note/' + str(user.notes[args.note_name][0]),
                               headers={'Authorization': f'Bearer {user.jwt}'})
    if report_success(response):
        del user.notes[args.note_name]


def print_p(args):
    user = users[current_username]
    print(user.notes[args.note_name][1])


COMMANDS = {
    'register': (argparse.ArgumentParser(prog='register'), register),
    'login': (argparse.ArgumentParser(prog='login'), login),
    'create': (argparse.ArgumentParser(prog='create'), create),
    'edit': (argparse.ArgumentParser(prog='edit'), edit),
    'get': (argparse.ArgumentParser(prog='get'), get_notes),
    'print': (argparse.ArgumentParser(prog='print'), print_p),
    'delete': (argparse.ArgumentParser(prog='delete'), delete),
    'exit': (argparse.ArgumentParser(prog='exit'), lambda _: sys.exit(0)),
}


def make_commands():
    register = COMMANDS['register'][0]
    register.add_argument('username')
    register.add_argument('password')

    login = COMMANDS['login'][0]
    login.add_argument('username')
    login.add_argument('password')

    create = COMMANDS['create'][0]
    create.add_argument('note_name')
    create.add_argument('content')

    edit = COMMANDS['edit'][0]
    edit.add_argument('note_name')
    edit.add_argument('content')

    print_p = COMMANDS['print'][0]
    print_p.add_argument('note_name')

    delete = COMMANDS['delete'][0]
    delete.add_argument('note_name')


def main():
    make_commands()
    while True:
        print('>>> ', end='')
        command = input().split(' ')
        if command[0] not in COMMANDS:
            print('Available commands:', *COMMANDS.keys())
            continue

        parser, callback = COMMANDS[command[0]]
        callback(parser.parse_args(command[1:]))


if __name__ == '__main__':
    main()
