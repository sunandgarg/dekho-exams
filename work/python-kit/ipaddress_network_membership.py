from ipaddress import ip_address, ip_network

allowed = ip_network("192.0.2.0/24")
for peer_text in ("192.0.2.47", "203.0.113.7", "invalid"):
    try:
        accepted = ip_address(peer_text) in allowed
    except ValueError:
        accepted = False
    print(peer_text, accepted)
