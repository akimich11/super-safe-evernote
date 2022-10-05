import hashlib
import random
from crypto.ecc import scalar_mult, curve, inverse_mod, point_add


def make_keypair():
    """Generates a random private-public key pair."""
    private_key = random.randrange(1, curve.n)
    public_key = scalar_mult(private_key, curve.g)

    return private_key, public_key


def hash_message(message):
    """Returns the truncated SHA521 hash of the message."""
    message_hash = hashlib.sha512(message).digest()
    e = int.from_bytes(message_hash, 'big')

    # FIPS 180 says that when a hash needs to be truncated, the rightmost bits
    # should be discarded.
    z = e >> (e.bit_length() - curve.n.bit_length())

    assert z.bit_length() <= curve.n.bit_length()

    return z


def sign_message(private_key, message):
    z = hash_message(message)

    r = 0
    s = 0

    while not r or not s:
        k = random.randrange(1, curve.n)
        x, y = scalar_mult(k, curve.g)

        r = x % curve.n
        s = ((z + r * private_key) * inverse_mod(k, curve.n)) % curve.n

    return r, s


def verify_signature(public_key, message, signature):
    z = hash_message(message)

    r, s = signature

    w = inverse_mod(s, curve.n)
    u1 = (z * w) % curve.n
    u2 = (r * w) % curve.n

    x, y = point_add(scalar_mult(u1, curve.g),
                     scalar_mult(u2, public_key))

    if (r % curve.n) == (x % curve.n):
        return 'signature matches'
    else:
        return 'invalid signature'


print('Curve:', curve.name)

private, public = make_keypair()
print("Private key:", hex(private))
print("Public key: (0x{:x}, 0x{:x})".format(*public))

msg = b'Hello!'
sign = sign_message(private, msg)

print()
print('Message:', msg)
print('Signature: (0x{:x}, 0x{:x})'.format(*sign))
print('Verification:', verify_signature(public, msg, sign))

msg = b'Hi there!'
print()
print('Message:', msg)
print('Verification:', verify_signature(public, msg, sign))

private, public = make_keypair()

msg = b'Hello!'
print()
print('Message:', msg)
print("Public key: (0x{:x}, 0x{:x})".format(*public))
print('Verification:', verify_signature(public, msg, sign))
