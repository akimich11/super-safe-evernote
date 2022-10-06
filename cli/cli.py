import argparse
import os
import requests
import sys
from crypto import ecdh
from crypto.ecc import scalar_mult
from utils import report_success, encrypt_note, decrypt_note

ADDRESS = os.getenv('BACKEND_URL', 'https://super-safe-evernote-backend.herokuapp.com/')

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


def register(args):
    User(args.username)
    response = requests.post(ADDRESS + 'auth/register',
                             json={
                                 'email': args.username + '@example.com',
                                 'password': args.password
                             })

    report_success(response, 201)


def login(args):
    global current_username
    response = requests.post(ADDRESS + 'auth/jwt/login',
                             data={
                                 'username': args.username + '@example.com',
                                 'password': args.password
                             })
    if args.username not in users:
        users[args.username] = User(args.username, response.json()['access_token'])

    current_username = args.username
    report_success(response)


def handshake(args=None):
    user = users[current_username]
    response = requests.get(ADDRESS + 'get_public_key',
                            json={'public_key': str(user.public_key)},
                            headers={'Authorization': f'Bearer {user.jwt}'})
    if report_success(response):
        user.shared_secret = scalar_mult(user.private_key, eval(response.json()['public_key']))


def get_notes(args=None):
    user = users[current_username]
    response = requests.get(ADDRESS + 'get_notes',
                            headers={'Authorization': f'Bearer {user.jwt}'})
    if report_success(response):
        for note in response.json()['message']:
            name, content = decrypt_note(user, note['name'], note['message'])
            user.notes[name] = content
        print('Available notes:', ', '.join(user.notes))


def create(args):
    user = users[current_username]
    name, content = encrypt_note(user, args.note_name, args.content)

    response = requests.post(ADDRESS + 'create_note',
                             headers={'Authorization': f'Bearer {user.jwt}'},
                             json={
                                 'name': name,
                                 'message': content
                             })
    if report_success(response):
        note = response.json()['message']
        name, content = decrypt_note(user, note['name'], note['message'])
        user.notes[name] = content


def edit(args):
    user = users[current_username]
    name, content = encrypt_note(user, args.note_name, args.content)
    response = requests.post(ADDRESS + 'edit_note',
                             headers={'Authorization': f'Bearer {user.jwt}'},
                             json={
                                 'name': name,
                                 'message': content
                             })
    if report_success(response):
        note = response.json()['message']
        name, content = decrypt_note(user, note['name'], note['message'])
        user.notes[name] = content


def delete(args):
    user = users[current_username]
    name, content = encrypt_note(user, args.note_name, user.notes[args.note_name])
    response = requests.delete(ADDRESS + 'delete_note',
                               headers={'Authorization': f'Bearer {user.jwt}'},
                               json={
                                   'name': name,
                                   'message': content
                               })
    if report_success(response):
        del user.notes[args.note_name]


def print_p(args):
    user = users[current_username]
    print(user.notes[args.note_name])


COMMANDS = {
    'register': (argparse.ArgumentParser(prog='register'), register),
    'login': (argparse.ArgumentParser(prog='login'), login),
    'handshake': (argparse.ArgumentParser(prog='handshake'), handshake),
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
