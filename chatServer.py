# chatServer.py
# Usage: python chatServer.py

import socket
import select
from enum import Enum
import sys
import fcntl
import struct

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
    for socket in CONNECTION_LIST:
        if socket != server_socket and socket != sock:
            try:
                socket.send(message)
                print "sent"
            except:
                # If chatClient pressed ctrl+c for example
                socket.close()
                CONNECTION_LIST.remove(socket)


if __name__ == "__main__":

    # List to keep track of socket descriptors
    CONNECTION_LIST = []
    AUTH_LIST = []
    RECV_BUFFER = 4096
    PORT = 42015
    backlog =  10
    HOST =  get_ip_address('wlp2s0') #"10.9.24.36"

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
    userName = {}
    userPassword = {}
    userDescription = {}
    cur_state = -1

    while True:
        CONNECTION_LIST.append(sys.stdin)

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
                command = sys.stdin.readline().split()
                srv_in = []
                for m in command:
                    srv_in.append(m)

                print srv_in[]
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))

                s.send("SRVR")


            else:
                # Data recieved from client, process it
                try:
                    # In Windows, sometimes when a TCP program closes abruptly,
                    # a "Connection reset by peer" exception will be thrown
                    data = sock.recv(RECV_BUFFER)
                    if data == "CLOSED":
                        AUTH_LIST.remove(sock)
                        for socket in AUTH_LIST:
                            socket.send("LEFT " + clientSocket[sock])


                    # command = com_str[0]
                    # ref_no = com_str[1]
                    # line2 = com_str[2]
                    # line3 = com_str[3]

                    com_str =[]
                    for cmd in data.split():
                         com_str.append(cmd)


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
                                for socket in AUTH_LIST:
                                    if socket != sock:
                                        socket.send("ARRV " + clientSocket[sock] + "\r\n" + userName[sock] + "\r\n" + "disconnected")
                            else:
                                sock.send("FAIL "+com_str[1]+"\r\nPASSWORD")

                        elif com_str[0] == "SEND" and cur_state == state.AUTH:
                            cur_state == state.SEND
                            sock.send("OKAY "+com_str[1])

                            if com_str[2] == "*":
                                print com_str[3]
                                broadcast_data(sock, "\r" + '<' + str(sock.getpeername()) + '> ' + com_str[3])

                            else:
                                msg = ""
                                for m in com_str[3:]:
                                    msg += " "+m
                                clientRefNo[com_str[2]].send("SEND " + com_str[1] + "\r\n" + clientSocket[sock] + "\r\n" + msg)

                        elif com_str[0] == "ACKN" and cur_state == state.AUTH:
                            clientRefNo[com_str[2]].send("ACKN "+ com_str[1])
                            #broadcast_data(sock, "\r" + '<' + str(sock.getpeername()) + '> ' + com_str[3])

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