# dnClient.py
# Example Usage: python chatClient.py localhost 42015

import socket
import select
import sys
from random import randint


def prompt():
    sys.stdout.write('<!--YOU--!> ')
    sys.stdout.flush()


# Main function
if __name__ == "__main__":

    if len(sys.argv) < 3:
        print 'Usage : python chatClient.py hostname port'
        sys.exit()

    host = sys.argv[1]
    port = int(sys.argv[2])

    # State of the connection
    CONNECTED = False
    AUTHENTICATED = False

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)

    # Connect to chatServer
    try:
        s.connect_ex((host, port))
    except:
        print 'Unable to connect to chatServer.'
        sys.exit()

    CONNECTED = True
    print 'Connected to chatServer.'

    # Protocol implementation

    commands = ['AUTH', 'SEND', 'ACKN', 'OKAY', 'FAIL', 'ARRV', 'LEFT', 'SRVR']

    prompt()

    authFlag = True

    while 1:
        if not authFlag:
            break
        if CONNECTED == True:
            # Random number generated for chatClient Reference, ask for name and password
            chatClientReference = randint(1, 100)
            chatClientName = raw_input("Enter name: ")
            chatClientPassword = raw_input("Enter password: ")

            authMessage = commands[0]
            authMessage += " "
            authMessage += str(chatClientReference)
            authMessage += " \r\n"
            authMessage += chatClientName
            authMessage += "\r\n"
            authMessage += chatClientPassword

            s.send(authMessage)

        socket_list = [sys.stdin, s]

        # Get the list sockets which are readable
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])

        for sock in read_sockets:
            # Incoming message from chatServer
            if sock == s:
                data = sock.recv(4096)
                authResponse = data.splitlines()

                # If OKAY
                if authResponse[0] == commands[3] + " " + str(chatClientReference):
                    print authResponse
                    authFlag = False
                    break

                # If FAIL
                elif authResponse[0] == commands[4] + " " + str(chatClientReference):
                    print authResponse[0]
                    print "\n"
                    print authResponse[1]
                    print "  : The password is not acceptable for authentication on this server"



