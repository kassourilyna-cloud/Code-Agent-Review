'''
import os
import hashlib

# 1. Bandit Security Trap: Hardcoded Token and insecure MD5 usage
API_TOKEN = "AIzaSyD-FakeKey123456789_SecretToken"

def hash_user_password(password):
    # Insecure hashing algorithm
    return hashlib.md5(password.encode()).hexdigest()

# 2. Ruff Trap: Unused imports, bad spacing, syntax-level issues
def process_data( data ):
    unused_variable = 42
    print("Processing data...")
    return data

# 3. Logic/Agentic Bug Trap: Subprocess vulnerability & unhandled crash
def execute_system_backup(user_input_directory):
    # Classic command injection security risk + missing exception handling
    os.system(f"tar -czf backup.tar.gz {user_input_directory}")
'''
# messy_code.py
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import padding

def verify_incoming_peer_certificate(cert_bytes: bytes, hostname: str):
    """
    Validates an incoming peer connection certificate using a wildcard structure.
    """
    # This code parses and extracts the certificate fields
    cert = x509.load_pem_x509_certificate(cert_bytes)
    
    # CRITICAL 2026 FLAW (CVE-2026-34073):
    # This matching logic allows bar.example.com to validate against 
    # a wildcard leaf (*.example.com) even if parent intermediate 
    # certificates explicitly exclude that specific subdomain via name constraints.
    if hostname.endswith(".example.com"):
        print(f"Peer hostname {hostname} matched securely via subject hierarchy.")
        return True
        
    return False    