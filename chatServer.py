# chatServer.py
# Usage: python chatServer.py

import socket
import select
from enum import Enum


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
    RECV_BUFFER = 4096
    PORT = 42015
    backlog =  10

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = ("0.0.0.0", PORT)
    server_socket.bind(server_address)
    server_socket.listen(backlog)

    # Add server socket to the list of readable connections
    CONNECTION_LIST.append(server_socket)

    print "chatServer started on port " + str(PORT)

    clientRefNo = {}
    cur_state = -1

    while True:
        # Get the list sockets which are ready to be read through select
        read_sockets, write_sockets, error_sockets = select.select(CONNECTION_LIST, [], [])

        for sock in read_sockets:
            # New connection
            if sock == server_socket:
                # Handle the case in which there is a new connection recieved through server_socket
                sockfd, addr = server_socket.accept()

                CONNECTION_LIST.append(sockfd)
                cur_state = state.CONN
                print "Client (%s, %s) connected" % addr

                #broadcast_data(sockfd, "[%s:%s] entered room\n" % addr)

            # Some incoming message from a client
            else:
                # Data recieved from client, process it
                try:
                    # In Windows, sometimes when a TCP program closes abruptly,
                    # a "Connection reset by peer" exception will be thrown
                    data = sock.recv(RECV_BUFFER)
                    auth_str = data.split()
                    command = auth_str[0]
                    ref_no = auth_str[1]
                    line2 = auth_str[2]
                    line3 = auth_str[3]
                    

                    try:
                        if command == "AUTH":

                            # if clientRefNo[ref_no]:
                            #     sock.send("FAIL "+ref_no+"\r\nNUMBER")
                            # else:
                            clientRefNo[ref_no] = sock
                        
                            if line3 == "dnServer":
                                cur_state = state.AUTH
                                sock.send("OKAY "+ref_no)
                            else:
                                sock.send("FAIL "+ref_no+"\r\nPASSWORD")

                        elif command == "SEND" and cur_state == state.AUTH:
                            cur_state == state.SEND
                            sock.send("OKAY "+ref_no)

                            if line2 == "*":
                                print line3
                                broadcast_data(sock, "\r" + '<' + str(sock.getpeername()) + '> ' + line3)

                            else:
                                clientRefNo[line2].send(line3)

                        elif command == "ACKN" and cur_state == state.AUTH:
                            sock.send("ACKN "+ref_no)

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