from cryptography.fernet import Fernet


def encrypt(key, password):
    return Fernet(key).encrypt(password.encode('utf-8'))


def decrypt(key, password):
    return Fernet(key).decrypt(password).decode('utf-8')
