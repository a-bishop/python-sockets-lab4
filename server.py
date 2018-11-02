# ICS 226 Lab 4
# Andrew Bishop
# Nov 2 /18

import sys
import socket
import os
import collections
import time
from threading import Thread, Lock

# Your server, when it receives a new client connection with the sock.accept() method,
# creates a client handler thread but does not start it! It simply hands the waiting client thread to
# the “manager”.
class ClientHandler(Thread):

    def __init__(self, conn):
        Thread.__init__(self)
        self.conn = conn

    def run(self):
        conn = self.conn
        print ("\n\nStarting " + self.name)

        # function definitions
        def recvWriteFile(filename, conn, size):
            with open(filename, "wb") as f:
                dataRemaining = size
                while dataRemaining > 0:
                    data = conn.recv(min(1024, dataRemaining))
                    if (dataRemaining == len(data)):
                        f.write(data)
                        conn.send("DONE".encode("utf-8"))
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
                        conn.send("DONE".encode("utf-8"))
                        break
                    else:
                        conn.send(data)

            # send READY message
        conn.send('READY'.encode("utf-8"))

        try:
            data = conn.recv(1024).decode("utf-8")
            data = data.split(' ')
            request = data[0]
            filename = data[1]
            filepath = './'
            if verbose >= 1:
                print('server receiving request: ' + request)
                print('filename', filename)
        except:
            if verbose >= 1:
                print("did not receive a request")

        ### ---- handle GET requests ----- ###
        if request == 'GET':
            # check if file requested is on server
            if os.path.isfile(filename) == True:
                conn.send('OK'.encode("utf-8"))
                response = conn.recv(1024).decode("utf-8")
                if response == 'READY':
                    size = os.path.getsize(filename)
                    size_bytes = size.to_bytes(8, byteorder='big', signed=False)
                    conn.send(size_bytes)
                    response = conn.recv(1024).decode("utf-8")
                    if response == 'OK':
                        if verbose >= 1:
                            print('server sending %d bytes' % size)
                        readSendFile(filename, conn, size)
                else:
                    print("notOK")
            else:
                msg = 'ERROR: file %s does not exist' % filename
                conn.send(msg.encode("utf-8"))
                
        ### --- Handle PUT Requests --- ###
        elif request == 'PUT':
            # check if OS can create file (permissions, etc)
            if os.access(filepath, os.X_OK):
                conn.send('OK'.encode("utf-8"))
                # receive number of bytes
                size = int.from_bytes(conn.recv(8), byteorder='big', signed=False)
                if verbose >= 1:
                    print('server receiving %d bytes' % size)
                conn.send('OK'.encode("utf-8"))
                # receive bytes in 1024 blocks
                recvWriteFile(filename, conn, size)
            else:
                msg = 'ERROR: unable to create file %s' % filename
                conn.send(msg.encode("utf-8"))
            

        ### --- Handle DEL Requests --- ###
        elif request == 'DEL':
            # check permissions
            try:
                print('server deleting file %s' % filename)
                os.remove(filename)
                conn.send('DONE'.encode("utf-8"))
            except:
                msg = 'ERROR: unable to delete %s' % filename
                conn.send(msg.encode("utf-8"))
    
        print ("Exiting " + self.name)

class Manager(Thread):

    def __init__(self, numClients):
        Thread.__init__(self)
        self.q = collections.deque()
        self.running = set()
        self.numClients = numClients
        self.lock = Lock()

    def checkRunning(self):
        kick = []
        if verbose >= 2:
            print("num running clients in checkRunning()", len(self.running))
        for t in self.running:
            if not t.isAlive(): kick.append(t)
        for t in kick:
            self.running.remove(t)
            if verbose >= 1:
                print("kicked a thread")

    def run(self):
        while True:
            self.checkRunning()
            if (len(self.q) > 0):
                if (len(self.running) < self.numClients):
                    if verbose >= 1:
                        print("num queued ", len(self.q))
                        print("num running clients", len(self.running))
                    thread = self.q.popleft()
                    thread.start()
                    if verbose >= 1:
                        print("num running clients now", len(self.running))
                    self.running.add(thread)
                    time.sleep(1)
                else:
                    if verbose >= 2:
                        print("sleeping, running set too big")
                    time.sleep(1)
            else:
                if verbose >= 2:
                    print("sleeping, nothing in queue")
                time.sleep(1)

    def add(self, conn):
        self.q.append(conn)

if __name__ == '__main__':
    # declare variables
    port = int(sys.argv[1])
    numClients = int(sys.argv[2])
    if "-v" in sys.argv:
        verbose = 1
    elif "-vv" in sys.argv:
        verbose = 2
    else:
        verbose = False

    # open socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # bind socket to host and port
    s.bind(('', port))
    # listen
    s.listen(4) # <-- how many concurrent clients can be 
                # queued, waiting for handshake

    if verbose >= 1:
        print('server waiting on port %s' % port)
        print('number of concurrent clients: %s' % numClients)

    clientManager = Manager(numClients)
    clientManager.start()

    while True:
        conn, addr = s.accept()
        if verbose >= 1:
            print('server connected to client at ' + addr[0] + ':' + str(addr[1]))
        thread = ClientHandler(conn)
        clientManager.add(thread)
    

# The ClientHandler class

# You must create a subclass of threading.Thread to handle all communication with a single
# client.



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
# kick = []
# for t in self.running:
#     if not t.isAlive(): kick.append(t)
# for t in kick:
#     self.running.remove(t)

# check the waiting queue:
    # if empty, sleep for 1 second and return to the top of the loop;
    # if it has an item:
        # check the size of the running set:
            # if it is full, sleep for 1 second and return to the top of the loop;
            # if it has space:      
                # remove the next client thread from the queue
                # start the thread
                # add the thread to the running set

# Note: Main program won't terminate while it has a child thread still running.
# To force all the threads to stop, you will have to use an operating-system kill. 
# On linux/mac, you can do the following:
    # ps aux | grep python - gives a list of python processes; find the
    # server.py process, and note the pid (second column) number (e.g. 12573)
    # kill <pid> - forces all threads under that process id to stop.



            
