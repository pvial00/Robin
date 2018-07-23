# Robin HTTP loadbalancer
Self healing HTTP round robin loadbalancer written in Python

# Usage:
robin = Robin("0.0.0.0", 6969, 10000, [('127.0.0.100',80), ('127.0.0.101',80), ('127.0.0.102',80)])

robin.start()
