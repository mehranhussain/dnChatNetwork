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
import traceback
import copy

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

       # Usage of the chatClient.py
    if len(sys.argv) < 1:
        print 'Usage : python chatServer.py port(optional)'
        sys.exit()
    elif len(sys.argv) < 2:
        port = 42015
    else:
        port = int(sys.argv[1])
   

    # List to keep track of socket descriptors`
    CONNECTION_LIST = []
    AUTH_LIST = []
    SRVR_LIST = []
    SRVR_LIST_ADDR = []
    RECV_BUFFER = 4029
    PORT = port
    backlog =  10
    HOST =  "127.0.0.1"#get_ip_address('wlp2s0') #"10.9.24.36"

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
    serverSocketList = {}
    serverNetwork = {}
    userName = {}
    userPassword = {}
    userDescription = {}
    sendLoopRef = {}
    ackLoopRef = {}
    arvLoopRef = {}
    lftLoopRef = {}

    cur_state = -1

    CONNECTION_LIST.append(sys.stdin)
    failure = False

    while True:
        
        # Get the list sockets which are ready to be read through select
        read_sockets, write_sockets, error_sockets = select.select(CONNECTION_LIST, [], [])

        for sock in read_sockets:
            # New connection
            if sock == server_socket:
                # Handle the case in which there is a new connection recieved through server_socket
                sockfd, addr = server_socket.accept()

                userDescription[sockfd] = addr                      
                # srv_addr = ""       
                # for v in SRVR_LIST_ADDR:        
                #     srv_addr += " " + str(v)        
                # #sockfd.send("SARRV " + str(server_socket.getsockname()[1]) + " " + srv_addr)                   
                # for srvr in SRVR_LIST:      
                #     print "SARRV " + str(server_socket.getsockname()[1]) + " " + srv_addr       
                #     srvr.send("SARRV " + str(server_socket.getsockname()[1]) + " " + srv_addr)      
                #sockfd.send("SARRV " + str(server_socket.getsockname()[1]) + " " + srv_addr)   
               

                CONNECTION_LIST.append(sockfd)
                cur_state = state.CONN
                print "(%s, %s) connected" % addr

                #-----------------------------

            # Some incoming message from a client      
            elif sock == sys.stdin:     
                srv_in = sys.stdin.readline().split()  
                 
                if len(srv_in) > 2:
                    port = srv_in[2]
                else:
                    port = 42015
         
                if srv_in[0] == "connect":      
                    srv_in_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       
                    # Connect to chatServer     
                    try:        
                        srv_in_socket.connect((srv_in[1], int(port)))
  
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
                    SRVR_LIST_ADDR.append(str(srv_in_socket.getsockname()[1]))      
                    serverSocket[srv_in_socket] = True      
                    CONNECTION_LIST.append(srv_in_socket) 

                    srv_in_socket.send("SRVR " + str(rfn))   

                    # srv_addr = ""       
                    # for v in SRVR_LIST_ADDR:        
                    #     srv_addr += " " + str(v) 

                    # for srvr in SRVR_LIST:      
                    #     print "SARRV " + str(server_socket.getsockname()[1]) + " " + srv_addr       
                    #     srvr.send("SARRV " + str(server_socket.getsockname()[1]) + " " + srv_addr)      
                    # for svd in SRVR_LIST_ADDR:        
                    #     serverSocketList[svd] = [str(server_socket.getsockname()[1])]     
                        
                
                elif srv_in[0] == "exit":
                    server_socket.close()
                    sys.exit()
                else:
                    print "Enter the correct command e.g. connect 133.0.9.3 42015"


                #------------------------------

                #broadcast_data(sockfd, "[%s:%s] entered room\n" % addr)

            else:
                # Data recieved from client, process it
                try:
                    # In Windows, sometimes when a TCP program closes abruptly,
                    # a "Connection reset by peer" exception will be thrown
                    data = sock.recv(RECV_BUFFER)
                    if data == "CLOSED":
                        AUTH_LIST.remove(sock)
                        ref = clientSocket[sock]

                        print "closed"

                        for sck in AUTH_LIST:
                            sck.send("LEFT " + clientSocket[sock])

                        for srvr in SRVR_LIST:
                            srvr.send("LEFT " + clientSocket[sock])
                            print "srvr left sent"

                        del userName[sock]
                        del clientSocket[sock]
                        del clientRefNo[ref]

            

                    # command = com_str[0]
                    # ref_no = com_str[1]
                    # line2 = com_str[2]
                    # line3 = com_str[3]

                    com_str =[]
                    for cmd in data.split():
                         com_str.append(cmd)

                    #----------------

                    try:             
                        if serverSocket[sock]:      
                            this_is_server = True       
                    except:     
                        this_is_server = False      
                    #----------------
      
                    try:
                        if com_str[0] == "AUTH":
                            try:
                                if clientRefNo[com_str[1]]:
                                    sock.send("FAIL "+com_str[1]+"\r\nNUMBER")
                            except:

                                for s, name in userName.iteritems():
                                    if name == com_str[2]:
                                        sock.send("FAIL "+com_str[2]+"\r\nNAME")
                                        failure = True
                                        break


                                if not com_str[3].isalnum():
                                    sock.send("FAIL "+com_str[1]+"\r\nPASSWORD")
                                    failure = True

                                if failure:
                                    failure = False
                                    break


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
                                            sck.send("ARRV " + clientSocket[sock] + "\r\n" + userName[sock] + "\r\n" + "description...")

                                    for srvr in SRVR_LIST:
                                        srvr.send("ARRV " + com_str[1] + "\r\n" + com_str[2] + "\r\n" + "description..." + "\r\n" + "1")

                                else:
                                    sock.send("FAIL "+com_str[1]+"\r\nPASSWORD")

                        elif com_str[0] == "SEND" and cur_state == state.AUTH and not this_is_server:

                            if  com_str[1] in sendLoopRef:
                                pass
                            else:
                                sendLoopRef[com_str[1]] = True
                                sock.send("OKAY "+com_str[1])

                                #SRVR_LIST = list(set(CONNECTION_LIST) - set(set([sys.stdin, server_socket]) | set(AUTH_LIST)))

                                msg = ""
                                for m in com_str[3:]:
                                    msg +=  m + " "


                                if len(msg) > 4096:
                                    sock.send("FAIL "+com_str[1]+"\r\nLENGHT")
                                    break

                                elif "*" in msg:
                                    sock.send("INVD 0")
                                    break

                                if com_str[2] == "*":
                                   
                                    #Broadcast to clients
                                    for sck in AUTH_LIST:
                                        if sck != sock:
                                            sck.send("SEND "+ com_str[1] + "\r\n" + clientSocket[sock] + "\r\n" + msg)

                                    #Broadcast to servers     
                                    for srvr in SRVR_LIST:      
                                        srvr.send("SEND "+ com_str[1] + "\r\n" + com_str[2] + "\r\n" + clientSocket[sock] + "\r\n" + msg)       
                                    #broadcast_data(sock, "SEND "+ com_str[1] + "\r\n" + clientSocket[sock] + "\r\n" + msg)
                                    
                                else:
                                    if com_str[2] in clientRefNo:
                                        clientRefNo[com_str[2]].send("SEND " + com_str[1] + "\r\n" + clientSocket[sock] + "\r\n" + msg)
                                    else:       
                                        for srvr in SRVR_LIST:      
                                            srvr.send("SEND "+ com_str[1] + "\r\n" + com_str[2] + "\r\n" + clientSocket[sock] + "\r\n" + msg)

                        elif com_str[0] == "ACKN" and cur_state == state.AUTH:

                            if com_str[3] in ackLoopRef:
                                pass
                            else:
                                ackLoopRef[com_str[3]] = True
                                try:
                                    if clientSocket[sock]:
                                        try:
                                            if clientRefNo[com_str[2]]:
                                                clientRefNo[com_str[2]].send("ACKN "+ com_str[1])
                                        except:
                                            for srvr in SRVR_LIST:
                                                srvr.send("ACKN "+ com_str[1] + "\r\n" + com_str[2] + "\r\n" + com_str[3])

                                except:
                                    try:
                                        if clientRefNo[com_str[2]]:
                                            clientRefNo[com_str[2]].send("ACKN "+ com_str[1])
                                    except:
                                        for srvr in SRVR_LIST:
                                            srvr.send("ACKN "+ com_str[1] + "\r\n" + com_str[2] + "\r\n" + com_str[3])
                            
                            
                        elif com_str[0] == "SRVR":     

                            serverSocket[sock] = com_str[1]     
                            SRVR_LIST.append(sock)      
                            SRVR_LIST_ADDR.append(str(sock.getsockname()[1]))       
                            print "The communication is from server"


                        elif com_str[0] == "ARRV":
                            if com_str[1] in arvLoopRef:
                                pass
                            else:
                                arvLoopRef[com_str[1]] = True
                                uReferenceNumber = com_str[1]
                                uName = com_str[2]
                                uDescription = com_str[3]
                                uhops = com_str[4]

                                for sck in AUTH_LIST:
                                    sck.send("ARRV " + uReferenceNumber + "\r\n" + uName + "\r\n" + uDescription)

                                for srvr in SRVR_LIST:      
                                    if srvr != sock:
                                        srvr.send("ARRV " + uReferenceNumber + "\r\n" + uName + "\r\n" + uDescription + "\r\n" + "1")     

                

                        elif com_str[0] == "LEFT":
                            if com_str[1] in lftLoopRef:
                                pass
                            else:
                                lftLoopRef[com_str[1]] = True
                                ref = com_str[1]

                                for sck in AUTH_LIST:
                                    sck.send("LEFT " + ref)

                                for srvr in SRVR_LIST:
                                    srvr.send("LEFT " + ref)

                                sk = clientRefNo[ref]
                                del userName[sk]
                                del clientRefNo[ref]
                                del clientSocket[sk]

                                print "The following user is not reachable" + com_str[1]

                        elif com_str[0] == "SEND" and this_is_server: 

                            if com_str[1] in sendLoopRef:
                                pass
                            else:
                                sendLoopRef[com_str[1]] = True
                                print com_str       
                                print "send and this is server"   

                                msg = ""        
                                for m in com_str[4:]:       
                                    msg +=  m + " "

                                if com_str[2] != "*":       
                                    if com_str[2] in clientRefNo:
                                        clientRefNo[com_str[2]].send("SEND " + com_str[1] + "\r\n" + com_str[3] + "\r\n" + msg)
                                    else:       
                                        for srvr in SRVR_LIST:
                                            if srvr != sock:     
                                                srvr.send("SEND "+ com_str[1] + "\r\n" + com_str[2] + "\r\n" + com_str[3] + "\r\n" + msg)       
                                else:       
                                 #Broadcast to clients       
                                    for sck in AUTH_LIST:       
                                        print "sent client"     
                                        sck.send("SEND "+ com_str[1] + "\r\n" + com_str[3] + "\r\n" + msg)      
                                            
                                    #Broadcast to servers     
                                    for srvr in SRVR_LIST:
                                        if srvr != sock:     
                                            srvr.send("SEND "+ com_str[1] + "\r\n" + com_str[2] + "\r\n" + com_str[3] + "\r\n" + msg)     
                                
                                print "SEND"


                        elif com_str[0] == "INVD" and com_str[1] == 0:
                            print "server close connection"
                            sock.close()
                        elif com_str[0] == "CLTS":

                            clts = ""
                            for s, name in userName.iteritems():
                                clts += "\r\n" + name

                            sock.send("CLTS" + clts)



                        # elif com_str[0] == "SARRV":  
                        #     print "sr arrival"     
                        #     srv_list = ""       
                        #     for s in com_str[2:]:       
                        #         srv_list += " " + s     
                        #     srv_list =  srv_list.split()        
                        #     serverSocketList[str(com_str[1])] = str(srv_list)       
                        #     print "recv"        
                        #     for srvr in SRVR_LIST:      
                        #         if srvr != sock:        
                        #             srvr.send("SARRV " + com_str[1] + " "+ srv_list)


                    except:
                        # If chatClient pressed ctrl+c for example
                        sock.close()
                        CONNECTION_LIST.remove(sock)

                except:
                    #broadcast_data(sock, "Client (%s, %s) is offline" % addr)
                    print "Client (%s, %s) is offline" % addr
                    sock.close()
                    CONNECTION_LIST.remove(sock)
                    continue

    server_socket.close()
