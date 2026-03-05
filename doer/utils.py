from cryptography.fernet import Fernet
from django.conf import settings

# Initialize fernet using your settings key
fernet = Fernet(settings.CHAT_ENCRYPTION_KEY)

def encrypt_message(text):
    # Encrypt and return as a string so it can be saved in the database field
    return fernet.encrypt(text.encode()).decode()

def decrypt_message(encrypted_text):
    # Convert the string back to bytes before decrypting
    if isinstance(encrypted_text, str):
        encrypted_text = encrypted_text.encode()
    return fernet.decrypt(encrypted_text).decode()