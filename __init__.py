import socket, threading, select
import os, time

class Robin:
    offline = []
    lb_pool = []
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    def __init__(self, host="0.0.0.0", port=80, listeners=10000, pool={}):
        self.host = host
        self.port = port
        self.listeners = listeners
        self.master_pool = pool

    def start(self):
        self.s.bind((self.host, self.port))
        self.s.listen(self.listeners)
        self.server_start()

    def start_health(self):
        self.health_thread = threading.Thread(target=self.health_check).start()

    def health_check(self):
        while True:
            if len(offline.keys()) > 0:
                for member in sorted(offline.keys()):
                    respone = ""
                    server = offline[str(member)]
                    getstring = "GET /index.html HTTP/1.1\nhost: %s\n\n" % server
                    sport = 80
                    health_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:
                        health_socket.connect((server, sport))
                        health_socket.send(getstring)
                        response = health_socket.recv(512)
                    except socket.error as er:
                        health_status = 0
                    else:
                        line = ""
                        for line in response.splitlines():
                            if "HTTP/1.1 200 OK" in line:
                                health_status = 1
                                self.master_pool[str(member)] = server
                                del offline[str(member)]
                            else:
                                health_status = 0
                                break
            num_members = len(self.master_pool.keys())
            for member in sorted(self.master_pool.keys()):
                response = ""
                server = self.master_pool[str(member)]
                getstring = "GET /index.html HTTP/1.1\nhost: %s\n\n" % server
                sport = 80
                health_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    health_socket.connect((server, sport))
                    health_socket.send(getstring)
                    response = health_socket.recv(512)
                except socket.error as er:
                    health_status = 0
                    del self.master_pool[str(member)]
                    self.offline[member] = server
                else:
                    line = ""
                    for line in response.splitlines():
                        if "HTTP/1.1 200 OK" in line:
                            health_status = 1
                        else:
                            health_status = 0
                            del self.master_pool[str(member)]
                            self.offline[member] = server
                        break
                time.sleep(2)
                health_socket.close()

    def rotatepool(self):
        client = "null"
        nodecount = len(self.lb_pool)
        master_pool_count = len(self.master_pool)
        if (nodecount == 0):
            for member in reversed(sorted(self.master_pool.keys())):
                self.lb_pool.append(self.master_pool[str(member)])
        if master_pool_count > 0:
            client = self.lb_pool.pop()
        return client

    def server_start(self):
        while True:
            c, addr = self.s.accept()
            client_handle = threading.Thread(target=self.client_handler, args=(c,)).start()

    def client_handler(self, c):
        os.setuid(33)
        newpayload = ""
        cport = 80
        payload = c.recv(1024)
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
        client = self.rotatepool()
        if client != "null":
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect((client, cport))
                client_socket.send(newpayload)
            except socket.error as csock_err:
                c.send("Error: 500 No Server available")
                c.close()
            else:
                if len(payload) != 0:
                    while True:
                        try:
                            data_check = select.select([client_socket], [], [], 2)
                        except IOError as sel_err:
                             pass
                        if data_check[0]:
                            #try:
                            cpayload = client_socket.recv(8192)
                            #except socket.error as recv_err:
                            #    pass
                        if not cpayload:
                            break
                        elif cpayload == "":
                            break

                        try:
                            c.send(cpayload)
                        except socket.error as send_err:
                            pass
		
                    c.close()
                    client_socket.close()
        else:
            srv_unavailable = "HTTP 1.1 503 No Server Available\n"
            c.send(srv_unavailable)
            c.close()
