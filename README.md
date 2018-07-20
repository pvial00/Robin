# Robin HTTP loadbalancer
Self healing HTTP round robin loadbalancer written in Python

# Usage:
robin = Robin("0.0.0.0", 80, 10000, {'1':'127.0.0.100', '2':'127.0.0.101', '3':'127.0.0.102'})

robin.start()

robin.health_check()
