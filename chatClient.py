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

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)

    # Connect to chatServer
    try:
        s.connect((host, port))
    except:
        print 'Unable to connect to chatServer.'
        sys.exit()

    print 'Connected to chatServer.'

    #Protocol implementation

    commands = ['AUTH', 'SEND', 'ACKN']
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


    prompt()

    while 1:
        socket_list = [sys.stdin, s]

        # Get the list sockets which are readable
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])

        for sock in read_sockets:
            # Incoming message from chatServer
            if sock == s:
                data = sock.recv(4096)
                authResponse = data.decode('utf-8')
                if authResponse == "OKAY "+ str(chatClientReference):
                    print "Goto next step"
                    sys.stdout.write(authResponse)
                elif authResponse == "FAIL " + str(chatClientReference):
                    sys.stdout.write(authResponse)
                if not data:
                    print '\nDisconnected from chatServer'
                    sys.exit()
                #else:
                  #  # Print data
                   # sys.stdout.write(data)
                   # prompt()

            # User entered a message
            else:
                msg = sys.stdin.readline()
                s.send(msg)
                prompt()