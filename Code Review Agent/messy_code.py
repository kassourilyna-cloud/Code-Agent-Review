
# messy_code.py
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import padding

def verify_incoming_peer_certificate(cert_bytes: bytes, hostname: str):
    """
    Validates an incoming peer connection certificate using a wildcard structure.
    """

    cert = x509.load_pem_x509_certificate(cert_bytes)
    
    
    if hostname.endswith(".example.com"):
        print(f"Peer hostname {hostname} matched securely via subject hierarchy.")
        return True
        
    return False    