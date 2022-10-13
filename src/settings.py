import os

ADDRESS = os.getenv('BACKEND_URL', 'https://super-safe-evernote-backend.herokuapp.com/')
KEY_EXPIRATION_TIME = os.getenv('KEY_EXPIRATION_TIME', 3600 * 4)
JWT_SECRET = os.getenv('SECRET', 'sodijf0943wu0e9jf42emf34989fnmweiud94')
MITM_PROXY = {
    'http': 'http://localhost:8080',
}
