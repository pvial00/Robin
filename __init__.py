import socket, threading, select
import os, time

class Robin:
    offline = []
    lb_pool = []
    connections = {}
    methods = ['RR','LEAST_CONN']
    lb_method = 'RR'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    def __init__(self, host="0.0.0.0", port=80, listeners=10000, pool=[], health_check=True, health_check_interval=2, lb_method='RR', recv_size=8192, uid=33):
        self.host = host
        self.port = port
        self.listeners = listeners
        self.master_pool = pool
        self.num_pool_members = len(pool)
        self.health_check = health_check
        self.health_check_interval = health_check_interval
        self.lb_method = lb_method
        self.recv_size = recv_size
        self.uid = uid
    
    def loadpool(self):
        for member in self.master_pool:
            self.lb_pool.append(member)
            self.connections[member] = 0

    def start(self):
        self.loadpool()
        self.s.bind((self.host, self.port))
        self.s.listen(self.listeners)
        self.start_health()
        self.server_start()

    def start_health(self):
        if self.health_check == True:
            self.health_thread = threading.Thread(target=self.health_checker).start()

    def health_checker(self, getstring="GET /index.html HTTP/1.1\nhost: %s\n\n"):
        while True:
            if len(self.offline) > 0:
                for member in self.offline:
                    respone = ""
                    server = member[0]
                    sport = member[1]
                    health_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:
                        health_socket.connect((server, sport))
                        health_socket.send(getstring)
                        response = health_socket.recv(self.recv_size)
                    except socket.error as er:
                        health_status = 0
                    else:
                        line = ""
                        for line in response.splitlines():
                            if "HTTP/1.1 200 OK" in line:
                                health_status = 1
                                self.lb_pool.append(member)
                                si = self.offline.index(member)
                                self.offline.pop(si)
                            else:
                                break
            num_members = len(self.lb_pool)
            for member in self.lb_pool:
                response = ""
                server = member[0]
                #getstring = "GET /index.html HTTP/1.1\nhost: %s\n\n" % server
                sport = member[1]
                health_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    health_socket.connect((server, sport))
                    health_socket.send(getstring)
                    response = health_socket.recv(self.recv_size)
                except socket.error as er:
                    health_status = 0
                    for index, member in enumerate(self.lb_pool):
                        if server == member[0]:
                            self.offline.append(self.lb_pool.pop(index))
                else:
                    line = ""
                    for line in response.splitlines():
                        if "HTTP/1.1 200 OK" in line:
                            health_status = 1
                        else:
                            health_status = 0
                            for index, member in enumerate(self.lb_pool):
                                if server == member[0]:
                                    self.offline.append(self.lb_pool.pop(index))
                        break
                time.sleep(self.health_check_interval)
                health_socket.close()

    def rotatepool(self):
        client = "null"
        nodecount = len(self.lb_pool)
        if self.lb_method == self.methods[0]:
            if nodecount >= 1:
                client = self.lb_pool.pop(0)
                self.lb_pool.append(client)
                self.connections[client] = self.connections[client] + 1
                return client
        elif self.lb_method == self.methods[1]:
            s = 1000000
            server = ("null",0)
            if nodecount >= 1:
                for member, conns in self.connections.iteritems():
                    if conns <= s:
                        s = conns
                        server = member
            self.connections[server] = self.connections[server] + 1
            return server

    def server_start(self):
        while True:
            c, addr = self.s.accept()
            client_handle = threading.Thread(target=self.client_handler, args=(c,)).start()

    def client_handler(self, c):
        os.setuid(self.uid)
        newpayload = ""
        payload = c.recv(self.recv_size)
        if len(payload) != 0:
            cnt = 0
            for line in payload.splitlines():
                if "User-Agent:" in line:
                    line = "User-Agent: hax0r"
                if newpayload == "":
                    newpayload = newpayload + line
                else:
                    newpayload = newpayload + "\r\n" + line
        newpayload = newpayload + "\r\n"
        member = self.rotatepool()
        client = member[0]
        cport = member[1]
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((client, cport))
            client_socket.send(newpayload)
        except socket.error as csock_err:
            c.send("Error: 500 No Server available\n")
            c.close()
        else:
            if len(payload) != 0:
                while True:
                    data_check = []
                    try:
                        data_check = select.select([client_socket], [], [], 2)
                    except select.error as sel_err:
                        pass
                    try:
                        if data_check[0]:
                            try:
                                cpayload = client_socket.recv(self.recv_size)
                            except socket.error as ser:
                                print ser
                            else:
                                if cpayload:
                                    try:
                                        c.send(cpayload)
                                    except socket.error as send_err:
                                        pass
                        #else:
                        #    break
                    except IndexError as ier:
                        pass
                    #if cpayload:
                    #    try:
                    ##        c.send(cpayload)
                    #    except socket.error as send_err:
                    #        pass
		
                c.close()
                client_socket.close()
                self.connections[member] = self.connections[member] - 1
            else:
                srv_unavailable = "HTTP 1.1 503 No Server Available\n"
                c.send(srv_unavailable)
                c.close()
