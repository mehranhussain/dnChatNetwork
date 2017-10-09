# chatServer.py
# Usage: python chatServer.py

import socket
import select
from enum import Enum
import sys
import fcntl
import struct
from random import randint
from collections import defaultdict

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])



class state(Enum):
    CONN = 0
    AUTH = 1
    SEND = 2
    ACKN = 3
    ARRV = 4
    LEFT = 5


# Function to broadcast chat messages to all connected clients
def broadcast_data(sock, message):
    # Do not send the message to the client who has send us the message
    for sck in CONNECTION_LIST:
        print "in loop"
        if sck != server_socket and sck != sock:
            try:
                sck.send(message)
                print "sent"
            except:
                # If chatClient pressed ctrl+c for example
                sck.close()
                CONNECTION_LIST.remove(sck)


if __name__ == "__main__":

    # List to keep track of socket descriptors
    CONNECTION_LIST = []
    AUTH_LIST = []
    SRVR_LIST = []
    RECV_BUFFER = 4096
    PORT = 42016
    backlog =  10
    HOST =  ""#get_ip_address('wlp2s0') #"10.9.24.36"

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = (HOST, PORT)
    server_socket.bind(server_address)
    server_socket.listen(backlog)


    # Add server socket to the list of readable connections
    CONNECTION_LIST.append(server_socket)

    print "chatServer started on port " + str(PORT)

    clientRefNo = {}
    clientSocket = {}
    serverRefNo = {}
    serverSocket = {}
    userName = {}
    userPassword = {}
    userDescription = {}
    cur_state = -1

    CONNECTION_LIST.append(sys.stdin)

    while True:
        
        # Get the list sockets which are ready to be read through select
        read_sockets, write_sockets, error_sockets = select.select(CONNECTION_LIST, [], [])

        for sock in read_sockets:
            # New connection
            if sock == server_socket:
                # Handle the case in which there is a new connection recieved through server_socket
                sockfd, addr = server_socket.accept()
                userDescription[sockfd] = addr

                CONNECTION_LIST.append(sockfd)
                cur_state = state.CONN
                print "Client (%s, %s) connected" % addr

                #broadcast_data(sockfd, "[%s:%s] entered room\n" % addr)

            # Some incoming message from a client
            elif sock == sys.stdin:

                srv_in = sys.stdin.readline().split()
                if srv_in[0] == "connect":
                    srv_in_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # Connect to chatServer
                    try:
                        srv_in_socket.connect((srv_in[1], int(srv_in[2])))
                    except socket.error as msg:
                        print "Socket Error: %s" % msg


                    # Random number generated for chatClient Reference, ask for name and password
                    rfn = randint(1, 10000)
                    ok = False
                    while not ok:
                        try:
                            while serverRefNo[rfn]:
                                rfn = randint(1, 10000)
                        except KeyError:
                            ok = True

                    serverRefNo[rfn] =  srv_in_socket
                    SRVR_LIST.append(srv_in_socket)
                    serverSocket[srv_in_socket] = True
                    CONNECTION_LIST.append(srv_in_socket)
 
                    srv_in_socket.send("SRVR " + str(rfn))

                else:
                    print "Enter the correct command e.g. connect 133.0.9.3 42015"

            else:
                # Data recieved from client, process it
                try:
                    # In Windows, sometimes when a TCP program closes abruptly,
                    # a "Connection reset by peer" exception will be thrown
                    data = sock.recv(RECV_BUFFER)
                    if data == "CLOSED":
                        AUTH_LIST.remove(sock)
                        for sck in AUTH_LIST:
                            sck.send("LEFT " + clientSocket[sock])


                    # command = com_str[0]
                    # ref_no = com_str[1]
                    # line2 = com_str[2]
                    # line3 = com_str[3]

                    com_str =[]
                    for cmd in data.split():
                         com_str.append(cmd)
                    try:
                        if serverSocket[sock]:
                            this_is_server = True
                    except:
                        this_is_server = False
                    print this_is_server

                    try:
                        if com_str[0] == "AUTH":

                            # if clientRefNo[com_str[1]]:
                            #     sock.send("FAIL "+com_str[1]+"\r\nNUMBER")
                            # else:
                            clientRefNo[com_str[1]] = sock
                            clientSocket[sock] = com_str[1]
                            userName[sock] = com_str[2]
                            userPassword[sock] = com_str[3]

                            if com_str[3] == "dnServer":
                                cur_state = state.AUTH
                                AUTH_LIST.append(sock)
                                sock.send("OKAY "+com_str[1])
                                for sck in AUTH_LIST:
                                    if sck != sock:
                                        sck.send("ARRV " + clientSocket[sock] + "\r\n" + userName[sock] + "\r\n" + "disconnected")
                                
                                for srvr in SRVR_LIST:
                                    srvr.send("ARRV " + clientSocket[sock] + "\r\n" + userName[sock] + "\r\n" + "disconnected" + "\r\n" + "1")

                            else:
                                sock.send("FAIL "+com_str[1]+"\r\nPASSWORD")

                        elif com_str[0] == "SEND" and cur_state == state.AUTH and not this_is_server:

                            cur_state == state.SEND
                            sock.send("OKAY "+com_str[1])

                            if com_str[2] == "*":
                                msg = ""
                                for m in com_str[3:]:
                                    msg += m

                                #Broadcast to clients
                                for sck in AUTH_LIST:
                                    if sck != sock:
                                        sck.send("SEND "+ com_str[1] + "\r\n" + clientSocket[sock] + "\r\n" + msg)
                                
                                #Broadcast to servers
                                for srvr in SRVR_LIST:
                                    srvr.send("SEND "+ com_str[1] + "\r\n" + com_str[2] + "\r\n" + clientSocket[sock] + "\r\n" + msg)

                                #broadcast_data(sock, "SEND "+ com_str[1] + "\r\n" + clientSocket[sock] + "\r\n" + msg)
                            else:
                                msg = ""
                                for m in com_str[3:]:
                                    msg += m
                                clientRefNo[com_str[2]].send("SEND " + com_str[1] + "\r\n" + clientSocket[sock] + "\r\n" + msg)

                        elif com_str[0] == "ACKN" and cur_state == state.AUTH :
                            clientRefNo[com_str[2]].send("ACKN "+ com_str[1])
                            #broadcast_data(sock, "\r" + '<' + str(sock.getpeername()) + '> ' + com_str[3])

                        elif com_str[0] == "SRVR":
                            serverSocket[sock] = com_str[1]
                            SRVR_LIST.append(sock)
                            print "The communication is from server"

                        elif com_str[0] == "ARRV":
                            uReferenceNumber = com_str[1]
                            uName = com_str[2]
                            uDescription = com_str[3]
                            uhops = com_str[4]

                            print "arrived"
                            if int(uhops) > 15:
                                for clnt in AUTH_LIST:
                                    clnt.send("LEFT " + uReferenceNumber)
                                for srvr in SRVR_LIST:
                                    srvr.send("LEFT " + uReferenceNumber)
                            else:
                                print "arv sent"
                                for sck in AUTH_LIST:
                                    sck.send("ARRV " + uReferenceNumber + "\r\n" + uName + "\r\n" + uDescription)
                                for srvr in SRVR_LIST:
                                    if srvr != sock:
                                        srvr.send("ARRV " + uReferenceNumber + "\r\n" + uName + "\r\n" + uDescription + "\r\n" + str(int(uhops)+1))

                        elif com_str[0] == "LEFT":
                            print "The following user is not reachable" + com_str[1]

                        elif com_str[0] == "SEND" and this_is_server:
                            print com_str
                         #Broadcast to clients
                            for sck in AUTH_LIST:
                                sck.send("SEND "+ com_str[1] + "\r\n" + com_str[3] + "\r\n" + com_str[4])
                            
                         #    #Broadcast to servers
                         #    for srvr in SRVR_LIST:
                         #        srvr.send("SEND "+ com_str[1] + "\r\n" + com_str[2] + "\r\n" + clientSocket[sock] + "\r\n" + msg)

                            print "SEND"

                        elif com_str[0] == "ACKN":
                            print "ACKN"

                        elif com_str[0] == "INVD" and com_str[1] == 0:
                            print "close connection"

                    except:
                        # If chatClient pressed ctrl+c for example
                        sock.close()
                        CONNECTION_LIST.remove(sock)

                except:
                    broadcast_data(sock, "Client (%s, %s) is offline" % addr)
                    print "Client (%s, %s) is offline" % addr
                    sock.close()
                    CONNECTION_LIST.remove(sock)
                    continue

    server_socket.close()