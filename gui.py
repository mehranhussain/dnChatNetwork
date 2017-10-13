import sys
if not sys.hexversion > 0x03000000:
    version = 2
else:
    version = 3
if len(sys.argv) > 1 and sys.argv[1] == "-cli":
    print("Starting command line chat")
    isCLI = True
else:
    isCLI = False


if version == 2:
    from Tkinter import *
    from tkFileDialog import asksaveasfilename
if version == 3:
    from tkinter import *
    from tkinter.filedialog import asksaveasfilename
import threading
import socket
import random
import math
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
        if sck != server_socket and sck != sock:
            try:
                sck.send(message)
            except:
                # If chatClient pressed ctrl+c for example
                sck.close()
                CONNECTION_LIST.remove(sck)




# GLOBALS
conn_array = []  # stores open sockets
secret_array = dict()  # key: the open sockets in conn_array,
                        # value: integers for encryption
username_array = dict()  # key: the open sockets in conn_array,
                        # value: usernames for the connection
contact_array = dict()  # key: ip address as a string, value: [port, username]

username = "Self"

location = 0
port = 0
top = ""

main_body_text = 0
#-GLOBALS-

# So,
   #  x_encode your message with the key, then pass that to
   #  refract to get a string out of it.
   # To decrypt, pass the message back to x_encode, and then back to refract

def binWord(word):
    """Converts the string into binary."""
    master = ""
    for letter in word:
        temp = bin(ord(letter))[2:]
        while len(temp) < 7:
            temp = '0' + temp
        master = master + temp
    return master

def xcrypt(message, key):
    """Encrypts the binary message by the binary key."""
    count = 0
    master = ""
    for letter in message:
        if count == len(key):
            count = 0
        master += str(int(letter) ^ int(key[count]))
        count += 1
    return master

def x_encode(string, number):
    """Encrypts the string by the number."""
    return xcrypt(binWord(string), bin(number)[2:])

def refract(binary):
    """Returns the string representation of the binary.
    Has trouble with spaces.

    """
    master = ""
    for x in range(0, int(len(binary) / 7)):
        master += chr(int(binary[x * 7: (x + 1) * 7], 2) + 0)
    return master


def formatNumber(number):
    """Ensures that number is at least length 4 by
    adding extra 0s to the front.

    """
    temp = str(number)
    while len(temp) < 4:
        temp = '0' + temp
    return temp

def netThrow(conn, secret, message):
    """Sends message through the open socket conn with the encryption key
    secret. Sends the length of the incoming message, then sends the actual
    message.

    """
    try:
        conn.send(formatNumber(len(x_encode(message, secret))).encode())
        conn.send(x_encode(message, secret).encode())
    except socket.error:
        if len(conn_array) != 0:
            writeToScreen(
                "Connection issue. Sending message failed.", "System")
            processFlag("-001")

def netCatch(conn, secret):
    """Receive and return the message through open socket conn, decrypting
    using key secret. If the message length begins with - instead of a number,
    process as a flag and return 1.

    """
    try:
        data = conn.recv(4)
        if data.decode()[0] == '-':
            processFlag(data.decode(), conn)
            return 1
        data = conn.recv(int(data.decode()))
        return refract(xcrypt(data.decode(), bin(secret)[2:]))
    except socket.error:
        if len(conn_array) != 0:
            writeToScreen(
                "Connection issue. Receiving message failed.", "System")
        processFlag("-001")

def isPrime(number):
    """Checks to see if a number is prime."""
    x = 1
    if number == 2 or number == 3:
        return True
    while x < math.sqrt(number):
        x += 1
        if number % x == 0:
            return False
    return True

def processFlag(number, conn=None):
    """Process the flag corresponding to number, using open socket conn
    if necessary.

    """
    global statusConnect
    global conn_array
    global secret_array
    global username_array
    global contact_array
    global isCLI
    t = int(number[1:])
    if t == 1:  # disconnect
        # in the event of single connection being left or if we're just a
        # client
        if len(conn_array) == 1:
            writeToScreen("Connection closed.", "System")
            dump = secret_array.pop(conn_array[0])
            dump = conn_array.pop()
            try:
                dump.close()
            except socket.error:
                print("Issue with someone being bad about disconnecting")
            if not isCLI:
                statusConnect.set("Connect")
                connecter.config(state=NORMAL)
            return

        if conn != None:
            writeToScreen("Connect to " + conn.getsockname()
                          [0] + " closed.", "System")
            dump = secret_array.pop(conn)
            conn_array.remove(conn)
            conn.close()

    if t == 2:  # username change
        name = netCatch(conn, secret_array[conn])
        if(isUsernameFree(name)):
            writeToScreen(
                "User " + username_array[conn] + " has changed their username to " + name, "System")
            username_array[conn] = name
            contact_array[
                conn.getpeername()[0]] = [conn.getpeername()[1], name]

    # passing a friend who this should connect to (I am assuming it will be
    # running on the same port as the other session)
    if t == 4:
        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        Client(data.decode(),
               int(contact_array[conn.getpeername()[0]][0])).start()

def processUserCommands(command, param):
    """Processes commands passed in via the / text input."""
    global conn_array
    global secret_array
    global username

    if command == "nick":  # change nickname
        for letter in param[0]:
            if letter == " " or letter == "\n":
                if isCLI:
                    error_window(0, "Invalid username. No spaces allowed.")
                else:
                    error_window(root, "Invalid username. No spaces allowed.")
                return
        if isUsernameFree(param[0]):
            writeToScreen("Username is being changed to " + param[0], "System")
            for conn in conn_array:
                conn.send("-002".encode())
                netThrow(conn, secret_array[conn], param[0])
            username = param[0]
        else:
            writeToScreen(param[0] +
                          " is already taken as a username", "System")
    if command == "disconnect":  # disconnects from current connection
        for conn in conn_array:
            conn.send("-001".encode())
        processFlag("-001")
    if command == "connect":  # connects to passed in host port
        if(options_sanitation(param[1], param[0])):
            Client(param[0], int(param[1])).start()
    if command == "host":  # starts server on passed in port
        if(options_sanitation(param[0])):
            Server(int(param[0])).start()

def isUsernameFree(name):
    """Checks to see if the username name is free for use."""
    global username_array
    global username
    for conn in username_array:
        if name == username_array[conn] or name == username:
            return False
    return True

def passFriends(conn):
    """Sends conn all of the people currently in conn_array so they can connect
    to them.

    """
    global conn_array
    for connection in conn_array:
        if conn != connection:
            conn.send("-004".encode())
            conn.send(
                formatNumber(len(connection.getpeername()[0])).encode())  # pass the ip address
            conn.send(connection.getpeername()[0].encode())
            # conn.send(formatNumber(len(connection.getpeername()[1])).encode()) #pass the port number
            # conn.send(connection.getpeername()[1].encode())

#--------------------------------------------------------------------------

def client_options_window(master):
    """Launches client options window for getting destination hostname
    and port.

    """
    top = Toplevel(master)
    top.title("Connection options")
    top.protocol("WM_DELETE_WINDOW", lambda: optionDelete(top))
    top.grab_set()
    Label(top, text="Server IP:").grid(row=0)
    location = Entry(top)
    location.grid(row=0, column=1)
    location.focus_set()
    Label(top, text="Port:").grid(row=1)
    port = Entry(top)
    port.grid(row=1, column=1)
    go = Button(top, text="Connect", command=lambda:
                client_options_go(location.get(), port.get(), top))
    go.grid(row=2, column=1)

def client_options_go(dest, port, window):
    "Processes the options entered by the user in the client options window."""
    if options_sanitation(port, dest):
        if not isCLI:
            window.destroy()
        Client(dest, int(port)).start()
    elif isCLI:
        sys.exit(1)

def options_sanitation(por, loc=""):
    """Checks to make sure the port and destination ip are both valid.
    Launches error windows if there are any issues.

    """
    global root
    if version == 2:
        por = unicode(por)
    if isCLI:
        root = 0
    if not por.isdigit():
        error_window(root, "Please input a port number.")
        return False
    if int(por) < 0 or 65555 < int(por):
        error_window(root, "Please input a port number between 0 and 65555")
        return False
    if loc != "":
        if not ip_process(loc.split(".")):
            error_window(root, "Please input a valid ip address.")
            return False
    return True

def ip_process(ipArray):
    """Checks to make sure every section of the ip is a valid number."""
    if len(ipArray) != 4:
        return False
    for ip in ipArray:
        if version == 2:
            ip = unicode(ip)
        if not ip.isdigit():
            return False
        t = int(ip)
        if t < 0 or 255 < t:
            return False
    return True

#------------------------------------------------------------------------------

def server_options_window(master):
    """Launches server options window for getting port."""
    top = Toplevel(master)
    top.title("Connection options")
    top.grab_set()
    top.protocol("WM_DELETE_WINDOW", lambda: optionDelete(top))
    Label(top, text="Port:").grid(row=0)
    port = Entry(top)
    port.grid(row=0, column=1)
    port.focus_set()
    go = Button(top, text="Launch", command=lambda:
                server_options_go(port.get(), top))
    go.grid(row=1, column=1)

def server_options_go(port, window):
    """Processes the options entered by the user in the
    server options window.

    """
    if options_sanitation(port):
        if not isCLI:
            window.destroy()
        Server(int(port)).start()
    elif isCLI:
        sys.exit(1)

#-------------------------------------------------------------------------

def username_options_window(master):
    """Launches username options window for setting username."""
    top = Toplevel(master)
    top.title("Username options")
    top.grab_set()
    Label(top, text="Username:").grid(row=0)
    name = Entry(top)
    name.focus_set()
    name.grid(row=0, column=1)
    go = Button(top, text="Change", command=lambda:
                username_options_go(name.get(), top))
    go.grid(row=1, column=1)


def username_options_go(name, window):
    """Processes the options entered by the user in the
    server options window.

    """
    processUserCommands("nick", [name])
    window.destroy()

#-------------------------------------------------------------------------

def error_window(master, texty):
    """Launches a new window to display the message texty."""
    global isCLI
    if isCLI:
        writeToScreen(texty, "System")
    else:
        window = Toplevel(master)
        window.title("ERROR")
        window.grab_set()
        Label(window, text=texty).pack()
        go = Button(window, text="OK", command=window.destroy)
        go.pack()
        go.focus_set()

def optionDelete(window):
    connecter.config(state=NORMAL)
    window.destroy()

#-----------------------------------------------------------------------------
# Contacts window

def contacts_window(master):
    """Displays the contacts window, allowing the user to select a recent
    connection to reuse.

    """
    global contact_array
    cWindow = Toplevel(master)
    cWindow.title("Contacts")
    cWindow.grab_set()
    scrollbar = Scrollbar(cWindow, orient=VERTICAL)
    listbox = Listbox(cWindow, yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    buttons = Frame(cWindow)
    cBut = Button(buttons, text="Connect",
                  command=lambda: contacts_connect(
                                      listbox.get(ACTIVE).split(" ")))
    cBut.pack(side=LEFT)
    dBut = Button(buttons, text="Remove",
                  command=lambda: contacts_remove(
                                      listbox.get(ACTIVE).split(" "), listbox))
    dBut.pack(side=LEFT)
    aBut = Button(buttons, text="Add",
                  command=lambda: contacts_add(listbox, cWindow))
    aBut.pack(side=LEFT)
    buttons.pack(side=BOTTOM)

    for person in contact_array:
        listbox.insert(END, contact_array[person][1] + " " +
                       person + " " + contact_array[person][0])
    listbox.pack(side=LEFT, fill=BOTH, expand=1)

def contacts_connect(item):
    """Establish a connection between two contacts."""
    Client(item[1], int(item[2])).start()

def contacts_remove(item, listbox):
    """Remove a contact."""
    if listbox.size() != 0:
        listbox.delete(ACTIVE)
        global contact_array
        h = contact_array.pop(item[1])


def contacts_add(listbox, master):
    """Add a contact."""
    aWindow = Toplevel(master)
    aWindow.title("Contact add")
    Label(aWindow, text="Username:").grid(row=0)
    name = Entry(aWindow)
    name.focus_set()
    name.grid(row=0, column=1)
    Label(aWindow, text="IP:").grid(row=1)
    ip = Entry(aWindow)
    ip.grid(row=1, column=1)
    Label(aWindow, text="Port:").grid(row=2)
    port = Entry(aWindow)
    port.grid(row=2, column=1)
    go = Button(aWindow, text="Add", command=lambda:
                contacts_add_helper(name.get(), ip.get(), port.get(),
                                    aWindow, listbox))
    go.grid(row=3, column=1)


def contacts_add_helper(username, ip, port, window, listbox):
    """Contact adding helper function. Recognizes invalid usernames and
    adds contact to listbox and contact_array.

    """
    for letter in username:
        if letter == " " or letter == "\n":
            error_window(root, "Invalid username. No spaces allowed.")
            return
    if options_sanitation(port, ip):
        listbox.insert(END, username + " " + ip + " " + port)
        contact_array[ip] = [port, username]
        window.destroy()
        return

def load_contacts():
    """Loads the recent chats out of the persistent file contacts.dat."""
    global contact_array
    try:
        filehandle = open("data\\contacts.dat", "r")
    except IOError:
        return
    line = filehandle.readline()
    while len(line) != 0:
        temp = (line.rstrip('\n')).split(" ")  # format: ip, port, name
        contact_array[temp[0]] = temp[1:]
        line = filehandle.readline()
    filehandle.close()

def dump_contacts():
    """Saves the recent chats to the persistent file contacts.dat."""
    global contact_array
    try:
        filehandle = open("data\\contacts.dat", "w")
    except IOError:
        print("Can't dump contacts.")
        return
    for contact in contact_array:
        filehandle.write(
            contact + " " + str(contact_array[contact][0]) + " " +
            contact_array[contact][1] + "\n")
    filehandle.close()

#-----------------------------------------------------------------------------

# places the text from the text bar on to the screen and sends it to
# everyone this program is connected to
def placeText(text):
    """Places the text from the text bar on to the screen and sends it to
    everyone this program is connected to.

    """
    global conn_array
    global secret_array
    global username
    writeToScreen(text, username)
    for person in conn_array:
        netThrow(person, secret_array[person], text)

def writeToScreen(text, username=""):
    """Places text to main text body in format "username: text"."""
    global main_body_text
    global isCLI
    if isCLI:
        if username:
            print(username + ": " + text)
        else:
            print(text)
    else:
        main_body_text.config(state=NORMAL)
        main_body_text.insert(END, '\n')
        if username:
            main_body_text.insert(END, username + ": ")
        main_body_text.insert(END, text)
        main_body_text.yview(END)
        main_body_text.config(state=DISABLED)

def processUserText(event):
    """Takes text from text bar input and calls processUserCommands if it
    begins with '/'.

    """
    data = text_input.get()
    if data[0] != "/":  # is not a command
        placeText(data)
    else:
        if data.find(" ") == -1:
            command = data[1:]
        else:
            command = data[1:data.find(" ")]
        params = data[data.find(" ") + 1:].split(" ")
        processUserCommands(command, params)
    text_input.delete(0, END)


def processUserInput(text):
    """ClI version of processUserText."""
    if text[0] != "/":
        placeText(text)
    else:
        if text.find(" ") == -1:
            command = text[1:]
        else:
            command = text[1:text.find(" ")]
        params = text[text.find(" ") + 1:].split(" ")
        processUserCommands(command, params)


#-------------------------------------------------------------------------

class Server (threading.Thread):
    "A class for a Server instance."""
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port

    def run(self):

        port = self.port

        # List to keep track of socket descriptors`
        CONNECTION_LIST = []
        AUTH_LIST = []
        SRVR_LIST = []
        SRVR_LIST_ADDR = []
        RECV_BUFFER = 4029
        PORT = port
        backlog =  10
        HOST =  ""#get_ip_address('wlp2s0') #"10.9.24.36"

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address = (HOST, PORT)
        server_socket.bind(server_address)
        server_socket.listen(backlog)

        # Add server socket to the list of readable connections
        CONNECTION_LIST.append(server_socket)

        print ("chatServer started on port" + str(PORT))

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
                    print ("(%s, %s) connected" % addr)

                    #-----------------------------

                # Some incoming message from a client      
                elif sock == sys.stdin:     
                    srv_in = sys.stdin.readline().split()       
                    if srv_in[0] == "connect":      
                        srv_in_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       
                        # Connect to chatServer     
                        try:        
                            srv_in_socket.connect((srv_in[1], int(srv_in[2])))
                        except socket.error as msg:     
                            print( "Socket Error: %s", msg)
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
                        print( "Enter the correct command e.g. connect 133.0.9.3 42015")


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

                            for sck in AUTH_LIST:
                                sck.send("LEFT " + clientSocket[sock])

                            for srvr in SRVR_LIST:
                                srvr.send("LEFT " + clientSocket[sock])

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
                                        msg +=  m

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
                                if com_str[1] in ackLoopRef:
                                    pass
                                else:
                                    ackLoopRef[com_str[1]] = True
                                    try:
                                        if clientSocket[sock]:
                                            try:
                                                if clientRefNo[com_str[2]]:
                                                    clientRefNo[com_str[2]].send("ACKN "+ com_str[1])
                                            except:
                                                for srvr in SRVR_LIST:
                                                    srvr.send("ACKN "+ com_str[1] + "\r\n" + com_str[2] + "\r\n" + clientSocket[sock])
                                            
                                    except:
                                        try:
                                            if clientRefNo[com_str[2]]:
                                                clientRefNo[com_str[2]].send("ACKN "+ com_str[1])
                                        except:
                                            for srvr in SRVR_LIST:
                                                srvr.send("ACKN "+ com_str[1] + "\r\n" + com_str[2])
                            
                            
                            elif com_str[0] == "SRVR":     

                                serverSocket[sock] = com_str[1]     
                                SRVR_LIST.append(sock)      
                                SRVR_LIST_ADDR.append(str(sock.getsockname()[1]))       
                                print ("The communication is from server")


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
                                    del clientRefNo[ref]
                                    del clientSocket[sk]

                                    print ("The following user is not reachable" + com_str[1])

                            elif com_str[0] == "SEND" and this_is_server: 

                                if com_str[1] in sendLoopRef:
                                    pass
                                else:
                                    sendLoopRef[com_str[1]] = True
                                    print ("send and this is server")

                                    msg = ""        
                                    for m in com_str[4:]:       
                                        msg +=  m

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
                                            sck.send("SEND "+ com_str[1] + "\r\n" + com_str[3] + "\r\n" + msg)      
                                                
                                        #Broadcast to servers     
                                        for srvr in SRVR_LIST:
                                            if srvr != sock:     
                                                srvr.send("SEND "+ com_str[1] + "\r\n" + com_str[2] + "\r\n" + com_str[3] + "\r\n" + msg)     
                                   


                            elif com_str[0] == "INVD" and com_str[1] == 0:
                                print ("server close connection")
                                sock.close()

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
                        print ("Client (%s, %s) is offline", addr)
                        sock.close()
                        CONNECTION_LIST.remove(sock)
                        continue

        server_socket.close()


        passFriends(CONNECTION_LIST)
        threading.Thread(target=Runner, args=(conn, secret)).start()
        Server(self.port).start()


class Client (threading.Thread):
    """A class for a Client instance."""
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.port = port
        self.host = host

    def run(self):
        # Declaring socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        host = self.host
        port = self.port

        # State of the connection
        CONNECTED = False
        AUTHENTICATED = False
      
        s.settimeout(2)

        # Connect to chatServer
        try:
            s.connect((host, port))
        except:
            print ('Unable to connect to chatServer.')
            sys.exit()

        CONNECTED = True
        print ('Connected to chatServer.')

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
                chatClientName = input("Enter name: ")
                chatClientPassword = input("Enter password: ")

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
                    print( authResponse)

                    # If OKAY
                    if data == commands[3] + " " + str(chatClientReference):
                       
                        authFlag = False
                        AUTHENTICATED = True
                        break

                    # If FAIL
                    elif authResponse[0] == commands[4]:
                        if authResponse[2] == "PASSWORD":
                            print (authResponse[0] + " " + authResponse[1] + " " + authResponse[2] + ": The password is not acceptable for authentication on this server.")
                        elif authResponse[2] == "NAME":
                            print (authResponse[0] + " " + authResponse[1] + " " + authResponse[2] + ": The specified name is already in use by another client.")
                        elif authResponse[2] == "NUMBER":
                            print (authResponse[0] + " " + authResponse[1] + " " + authResponse[2] + ": A number is not valid, either because it has already been used for another entity in case it was newly generated by the client, or there is no relevant entity that the number refers to.")

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
                        
                        s.send("ACKN " + authResponse[1]  + "\r\n" + authResponse[2])

                    # If ARRV
                    elif authResponse[0] == commands[6]:
                        print ("The following user is connected now.\r\nUser Reference: " + authResponse[1] + "\r\nUsername: " + authResponse[2] + "\r\nIpAddress: " + authResponse[3])

                    # If LEFT
                    elif authResponse[0] == commands[7]:
                        print ("The following user has left.\r\nUser Reference: " + authResponse[1])

                    # If FAIL
                    elif authResponse[0] == commands[4]:
                       if authResponse[2] == "LENGHT":
                           print (authResponse[0] + " " + authResponse[1] + " " + authResponse[2] + ": The chat message text is too long.")
                       elif authResponse[2] == commands[5]:
                            print (authResponse[0] + " " + authResponse[1] + " " + authResponse[2] + ": A malformed message or a message that is not valid in the current state of the client.")
                            s.close()
                            print ("Connection to chatServer closed.")
                    else:
                        print (data)

                else:
                    if AUTHENTICATED == True:
                        chatMessageInput = sys.stdin.readline()
                        chatMessageRcvr = input("Enter * for broadcasting or Reference Number of specific client: ")

                        chatMessage = commands[1]
                        chatMessage += " "
                        chatMessage += str(chatMessageReference)
                        chatMessage += " \r\n"
                        chatMessage += chatMessageRcvr
                        chatMessage += "\r\n"
                        chatMessage += chatMessageInput

                    s.send(chatMessage)

        threading.Thread(target=Runner, args=(conn, secret)).start()
        # Server(self.port).start()
        # ##########################################################################THIS
        # IS GOOD, BUT I CAN'T TEST ON ONE MACHINE

def Runner(conn, secret):
    global username_array
    while 1:
        data = netCatch(conn, secret)
        if data != 1:
            writeToScreen(data, username_array[conn])

#-------------------------------------------------------------------------
# Menu helpers

def QuickClient():
    """Menu window for connection options."""
    window = Toplevel(root)
    window.title("Connection options")
    window.grab_set()
    Label(window, text="Server IP:").grid(row=0)
    destination = Entry(window)
    destination.grid(row=0, column=1)
    go = Button(window, text="Connect", command=lambda:
                client_options_go(destination.get(), "9999", window))
    go.grid(row=1, column=1)


def QuickServer():
    """Quickstarts a server."""
    Server(9999).start()

def saveHistory():
    """Saves history with Tkinter's asksaveasfilename dialog."""
    global main_body_text
    file_name = asksaveasfilename(
        title="Choose save location",
        filetypes=[('Plain text', '*.txt'), ('Any File', '*.*')])
    try:
        filehandle = open(file_name + ".txt", "w")
    except IOError:
        print("Can't save history.")
        return
    contents = main_body_text.get(1.0, END)
    for line in contents:
        filehandle.write(line)
    filehandle.close()


def connects(clientType):
    global conn_array
    connecter.config(state=DISABLED)
    if len(conn_array) == 0:
        if clientType == 0:
            client_options_window(root)
        if clientType == 1:
            server_options_window(root)
    else:
        # connecter.config(state=NORMAL)
        for connection in conn_array:
            connection.send("-001".encode())
        processFlag("-001")


def toOne():
    global clientType
    clientType = 0


def toTwo():
    global clientType
    clientType = 1


#-------------------------------------------------------------------------


if len(sys.argv) > 1 and sys.argv[1] == "-cli":
    print("Starting command line chat")

else:
    root = Tk()
    root.title("Chat")

    menubar = Menu(root)

    file_menu = Menu(menubar, tearoff=0)
    file_menu.add_command(label="Save chat", command=lambda: saveHistory())
    file_menu.add_command(label="Change username",
                          command=lambda: username_options_window(root))
    file_menu.add_command(label="Exit", command=lambda: root.destroy())
    menubar.add_cascade(label="File", menu=file_menu)

    connection_menu = Menu(menubar, tearoff=0)
    connection_menu.add_command(label="Quick Connect", command=QuickClient)
    connection_menu.add_command(
        label="Connect on port", command=lambda: client_options_window(root))
    connection_menu.add_command(
        label="Disconnect", command=lambda: processFlag("-001"))
    menubar.add_cascade(label="Connect", menu=connection_menu)

    server_menu = Menu(menubar, tearoff=0)
    server_menu.add_command(label="Launch server", command=QuickServer)
    server_menu.add_command(label="Listen on port",
                            command=lambda: server_options_window(root))
    menubar.add_cascade(label="Server", menu=server_menu)

    menubar.add_command(label="Contacts", command=lambda:
                        contacts_window(root))

    root.config(menu=menubar)

    main_body = Frame(root, height=20, width=50)

    main_body_text = Text(main_body)
    body_text_scroll = Scrollbar(main_body)
    main_body_text.focus_set()
    body_text_scroll.pack(side=RIGHT, fill=Y)
    main_body_text.pack(side=LEFT, fill=Y)
    body_text_scroll.config(command=main_body_text.yview)
    main_body_text.config(yscrollcommand=body_text_scroll.set)
    main_body.pack()

    main_body_text.insert(END, "Welcome to the chat program!")
    main_body_text.config(state=DISABLED)

    text_input = Entry(root, width=60)
    text_input.bind("<Return>", processUserText)
    text_input.pack()

    statusConnect = StringVar()
    statusConnect.set("Connect")
    clientType = 1
    Radiobutton(root, text="Client", variable=clientType,
                value=0, command=toOne).pack(anchor=E)
    Radiobutton(root, text="Server", variable=clientType,
                value=1, command=toTwo).pack(anchor=E)
    connecter = Button(root, textvariable=statusConnect,
                       command=lambda: connects(clientType))
    connecter.pack()

    load_contacts()

#------------------------------------------------------------#

    root.mainloop()

    dump_contacts()