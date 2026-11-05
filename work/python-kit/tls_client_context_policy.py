import ssl

client_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
print("hostname_check", client_context.check_hostname)
print("certificate_required", client_context.verify_mode == ssl.CERT_REQUIRED)
