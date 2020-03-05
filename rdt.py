from network import Protocol, StreamSocket
import struct
import sys
import ipaddress

# Reserved protocol number for experiments; see RFC 3692
IPPROTO_RDT = 0xfe


class RDTSocket(StreamSocket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Other initialization her
        self.port = 0
        self.bound = False
        self.accepted = False 
        self.connected = False 


    def bind(self, port):
        if(self.bound): 
            return
        check = self.proto.addport(port)
        if(check == 1):
            raise StreamSocket.AddressInUse
        elif(check == 2):
            raise StreamSocket.AlreadyConnected
        self.port = port
        self.bound = True 

    def listen(self):
        check = self.proto.listen(self.port)
        if(check == 0):
            return
        elif(check == 1):
            raise StreamSocket.NotBound
        elif(check == 2):
            raise StreamSocket.AlreadyConnected

    def accept(self):
        check = self.proto.accept(0, "0")
        if(check == 1):
            raise StreamSocket.NotListening 
        buff = self.recv()
        tmp = self.proto.parseHdr(buff)
        self.proto.accept(str(ipaddress.IPv4Address(tmp[0])), tmp[1])
        return (self, (str(ipaddress.IPv4Address(tmp[0])), tmp[1]))

    def connect(self, addr):
        check = self.proto.connect(addr, self.port)
        if(check[0] == 1):
            raise StreamSocket.AlreadyConnected
        elif(check[0] == 2):
            raise StreamSocket.AlreadyListening
        elif(check[0] ==0):
            self.port = check[1]
        self.output(self.proto.buildHdr(addr[1], self.port, addr[0], "10.50.254.1", b""), addr[0])

    def send(self, data):
        check = self.proto.send(data, self.port)
        if(check == 1):
            raise StreamSocket.NotConnected 
        self.output(buildHdr + data)


class RDTProtocol(Protocol):
    PROTO_ID = IPPROTO_RDT
    SOCKET_CLS = RDTSocket

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bound = []
        self.conn = []
        self.list = []
        self.socks = {}
        self.nextport = 55555

    def buildHdr(self, dstport, srcport, dstip, srcip, data):
        chcksum = 0
        sq = 1
        srcip = int(ipaddress.IPv4Address(srcip))
        dstip = int(ipaddress.IPv4Address(dstip))
        #the hdr is(sequencenum, dstport, srcport, dstip, srcip, chksum)
        return struct.pack("=6i", sq, dstport, srcport, dstip, srcip, chcksum) #+ data

    def parseHdr(self, data):
        return struct.unpack("=6i", data)


    def addport(self, port):
        if(port in self.bound):
            return 1
        elif(port in self.conn):
            return 2
        else:
            self.bound.append(port)

    def listen(self, port):
        if(port not in self.bound):
            return 1
        elif(port in self.conn):
            return 2 
        else: 
            self.list.append(port)

    def connect(self, addr, port):
        if(port == 0):
            while(self.nextport in self.bound):
                self.nextport += 1
            port = self.nextport 
            self.nextport += 1 

        if(port in self.conn):
            return 1, 0
        elif(port in self.list):
            return 2, 0
        print(port)
        self.conn.append(port)
        self.socks[(port, addr[0])] = self.socket()
        print(self.socks)
        return 0, port

    def input(self, seg, rhost):
        (sequencenum, dstport, srcport, dstip, srcip, chksum) = self.parseHdr(seg)
        #print(self.socks)
        if self.conn.isEmpty():
            self.list[dstport].deliver(seg)
        self.socks[(dstport, dstip)].deliver(seg)

    def send(data, port):
        if(port not in self.conn):
            return 1 

    def accept(self, port, raddr):
        if(port not in self.bound):
            return 0
        if(port not in self.list):
            return 1
        elif(port in self.conn):
            return 2
        elif((port, raddr) in self.socks):
            print(error)
            return 3
        self.socks[(port, raddr)] = self.socket()
        print(self.socks)