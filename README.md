# Robin HTTP loadbalancer
Self healing HTTP round robin loadbalancer written in Python

# Usage:
Round Robin

robin = Robin("0.0.0.0", 9001, 10000, [('127.0.0.100',80), ('127.0.0.101',80), ('127.0.0.102',80)], lb_method='RR', uid=33)

robin.start()

Least Connections

robin = Robin("0.0.0.0", 9001, 10000, [('127.0.0.100',80), ('127.0.0.101',80), ('127.0.0.102',80)], lb_method='LEAST_CONN', uid=33)

robin.start()
