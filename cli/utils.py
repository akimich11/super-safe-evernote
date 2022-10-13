import zpp_serpent


def encrypt_note(shared_secret, name, content=None):
    password = shared_secret.to_bytes(32, 'big')
    name = str(zpp_serpent.encrypt_CFB(name.encode(), password))
    if content is not None:
        content = str(zpp_serpent.encrypt_CFB(content.encode(), password))
    return name, content


def decrypt_note(shared_secret, name, content):
    password = shared_secret.to_bytes(32, 'big')
    name = str(zpp_serpent.decrypt_CFB(eval(name), password).decode())
    content = str(zpp_serpent.decrypt_CFB(eval(content), password).decode())
    return name, content


def report_success(response, expected_code=200):
    ok = response.status_code == expected_code
    if 'message' in response.json() and response.json()['message'] == 'ECDH error':
        print('ECDH error')
        return False
    else:
        print('Successful' if ok else 'Failed')
    return ok
