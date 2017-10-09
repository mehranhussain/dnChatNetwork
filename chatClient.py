# dnClient.py
# Example Usage: python chatClient.py localhost 42015

# importing required modules
import socket
import select
import sys
from random import randint

# Declaring socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Main function
def main():

    # Usage of the chatClient.py
    if len(sys.argv) < 3:
        print 'Usage : python chatClient.py hostname port'
        sys.exit()

    host = sys.argv[1]
    port = int(sys.argv[2])

    # State of the connection
    CONNECTED = False
    AUTHENTICATED = False
  
    s.settimeout(2)

    # Connect to chatServer
    try:
        s.connect((host, port))
    except:
        print 'Unable to connect to chatServer.'
        sys.exit()

    CONNECTED = True
    print 'Connected to chatServer.'

    # Protocol implementation

    commands = ['AUTH', 'SEND', 'ACKN', 'OKAY', 'FAIL', 'INVD', 'ARRV', 'LEFT', 'SRVR']

    authFlag = True

    # Authentication Stage
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
                authResponse = data.split()
                print authResponse

                # If OKAY
                if data == commands[3] + " " + str(chatClientReference):
                    print data
                    authFlag = False
                    AUTHENTICATED = True
                    break

                # If FAIL
                elif authResponse[0] == commands[4]:
                    if authResponse[2] == "PASSWORD":
                        print authResponse[0] + " " + authResponse[1] + " " + authResponse[2] + ": The password is not acceptable for authentication on this server."
                    elif authResponse[2] == "NAME":
                        print authResponse[0] + " " + authResponse[1] + " " + authResponse[2] + ": The specified name is already in use by another client."
                    elif authResponse[2] == "NUMBER":
                        print authResponse[0] + " " + authResponse[1] + " " + authResponse[2] + ": A number is not valid, either because it has already been used for another entity in case it was newly generated by the client, or there is no relevant entity that the number refers to."

    # When client is connected and authenticated
    while 1:
        socket_list = [sys.stdin, s]
        # Get the list sockets which are readable
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])

        # Random number generated for chatMesssageReference
        chatMessageReference = randint(1, 10000)

        for sock in read_sockets:

            # Incoming message from chatServer

            if sock == s:
                data = sock.recv(4096)
                authResponse = data.split()

                # If OKAY
                if data == commands[3] + " " + str(chatMessageReference):
                    sys.stdout.write(data)

                # If SEND
                elif authResponse[0] == commands[1]:
                    print data
                    s.send("ACKN " + authResponse[1]  + "\r\n" + authResponse[2])

                # If ARRV
                elif authResponse[0] == commands[6]:
                    print "The following user is connected now.\r\nUser Reference: " + authResponse[1] + "\r\nUsername: " + authResponse[2] + "\r\nIpAddress: " + authResponse[3]

                # If LEFT
                elif authResponse[0] == commands[7]:
                    print "The following user has left.\r\nUser Reference: " + authResponse[1]

                # If FAIL
                elif authResponse[0] == commands[4]:
                   if authResponse[2] == "LENGHT":
                       print authResponse[0] + " " + authResponse[1] + " " + authResponse[2] + ": The chat message text is too long."
                   elif authResponse[2] == commands[5]:
                        print authResponse[0] + " " + authResponse[1] + " " + authResponse[2] + ": A malformed message or a message that is not valid in the current state of the client."
                        s.close()
                        print "Connection to chatServer closed."
                else:
                    print data

            else:
                if AUTHENTICATED == True:
                    chatMessageInput = sys.stdin.readline()
                    chatMessageRcvr = raw_input("Enter * for broadcasting or Reference Number of specific client: ")

                    chatMessage = commands[1]
                    chatMessage += " "
                    chatMessage += str(chatMessageReference)
                    chatMessage += " \r\n"
                    chatMessage += chatMessageRcvr
                    chatMessage += "\r\n"
                    chatMessage += chatMessageInput

                s.send(chatMessage)

# Run the main method, If user presses ctrl+c close the socket connection
if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        s.send("CLOSED")
        s.close()


