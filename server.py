# ICS 226 Lab 4
# Andrew Bishop

import sys
import socket
import os
import collections

# declare variables
port = int(sys.argv[1])
if len(sys.argv) > 2:
    verbose = True if sys.argv[2] == '-v' else False
else:
    verbose = False

# The ClientHandler class

    # You must create a subclass of threading.Thread to handle all communication with a single
    # client.

    # Your server, when it receives a new client connection with the sock.accept() method,
    # creates a client handler thread but does not start it! It simply hands the waiting client thread to
    # the “manager”.

# The Manager class

    # This class will maintain two data structures: a queue (implemented with a Python
    # collections.deque() object), and a set (implemented with a Python set() object).

    # The queue will hold all the waiting client connections; they haven’t started yet, they’ve just been
    # added to the queue, waiting to be executed. The main program calls a method of this class to
    # add new client threads to the queue.

    # When the manager decides it is time to start one of the waiting client threads, it issues the
    # t.start() command, and then adds it to the “ running ” set.

    # (Sets are kind of like queues, except they don’t maintain any particular order; you add items,
    # remove items, and iterate efficiently, but you can’t expect any particular order when you iterate.)

    # We will impose a limit on how big the “ running ” set may be, so that the clients are limited to
    # how much of the server’s resources they can collectively use. The server will now take an
    # additional commandline parameter ( sys.argv[2] ) that says how many clients may actually be
    # actively running concurrently (e.g. 5 -- don’t make it too big!). Note that sys.argv[1] will still
    # be the server’s binding port. You can implement a -v flag if you like, but it’s not required and will
    # not be graded; your server should not have any output as the default option.


# The manager sits in an infinite loop, executing the following pseudocode:

# check the “ running ” threads; if any of them have stopped, remove them from the set.
# check the waiting queue:
    # if empty, sleep for 1 second and return to the top of the loop;
    # if it has an item:
        # check the size of the running set:
            # if it is full, sleep for 1 second and return to the top of the loop;
            # if it has space:      
                # remove the next client thread from the queue
                # start the thread
                # add the thread to the running set

# declare functions
def recvWriteFile(filename, conn, size):
    with open(filename, "wb") as f:
        dataRemaining = size
        while dataRemaining > 0:
            data = conn.recv(min(1024, dataRemaining))
            if (dataRemaining == len(data)):
                f.write(data)
                conn.send("DONE".encode())
                dataRemaining = 0
            else:
                f.write(data)
                dataRemaining -= len(data)

def readSendFile(filename, conn, size):
    with open(filename, "rb") as f:
        dataRemaining = size
        while dataRemaining > 0:
            data = f.read(min(1024, dataRemaining))
            dataRemaining -= len(data)
            if (dataRemaining == 0):
                conn.send(data)
                conn.send("DONE".encode())
                break
            else:
                conn.send(data)

# open socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind socket to host and port
s.bind(('', port))
# listen
s.listen(0) # <-- how many concurrent clients can be 
            # queued, waiting for handshake

if verbose:
    print('server waiting on port %s' % port)

while True:

    # accept and send READY message
    conn, addr = s.accept() # creates a new socket, connected to client
    if verbose:
        print('server connected to client at ' + addr[0] + ':' + str(addr[1]))
    conn.send('READY'.encode())

    data = conn.recv(1024).decode()
    data = data.split(' ')
    request = data[0]
    filename = data[1]
    filepath = './'

    ### ---- handle GET requests ----- ###
    if request == 'GET':
        if verbose:
            print('server receiving request: ' + request)
        # check if file requested is on server
        if os.path.isfile(filename) == True:
            conn.send('OK'.encode())
            response = conn.recv(1024).decode()
            if response == 'READY':
                size = os.path.getsize(filename)
                size_bytes = size.to_bytes(8, byteorder='big', signed=False)
                conn.send(size_bytes)
                response = conn.recv(1024).decode()
                if response == 'OK':
                    if verbose:
                        print('server sending %d bytes' % size)
                    readSendFile(filename, conn, size)
        else:
            msg = 'ERROR: file %s does not exist' % filename
            conn.send(msg.encode())
            
    ### --- Handle PUT Requests --- ###
    elif request == 'PUT':
        if verbose:
            print('server receiving request: ' + request)
        # check if OS can create file (permissions, etc)
        if os.access(filepath, os.X_OK):
            conn.send('OK'.encode())
            # receive number of bytes
            size = int.from_bytes(conn.recv(8), byteorder='big', signed=False)
            if verbose:
                print('server receiving %d bytes' % size)
            conn.send('OK'.encode())
            # receive bytes in 1024 blocks
            recvWriteFile(filename, conn, size)
        else:
            msg = 'ERROR: unable to create file %s' % filename
            conn.send(msg.encode())
        

    ### --- Handle DEL Requests --- ###
    elif request == 'DEL':
        if verbose:
            print('server receiving request: ' + request)
        # check permissions
        try:
            print('server deleting file %s' % filename)
            os.remove(filename)
            conn.send('DONE'.encode())
        except:
            msg = 'ERROR: unable to delete %s' % filename
            conn.send(msg.encode())

            
