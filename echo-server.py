import socket

# host can be a hostname, IP address or empty string
# IP address usually needs to be IPv4 formatted address string, for ex. 127.0.0.1
# empty string - server will accept connection from all available IPv interfaces
HOST = '127.0.0.1' # Standard loopback interface address (localhost)

# port should an integer between 1-65535 (0 is reserved)
PORT = 65432 # Port to listen on (non-privileged ports are > 1023)

# socket.socket() creates a socket object that supports the context manager type, so we can use with statement. Hence, there is no need to call s.close().
# context manager type - https://docs.python.org/3/reference/datamodel.html#context-managers
# with statement - https://docs.python.org/3/reference/compound_stmts.html#with
# The arguments passed to socket() specify the address family.
# AF_INET - internet address family for IPv4 https://en.wikipedia.org/wiki/IPv4
# SOCK_STREAM - socket type for TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # the value tha tis passed to bind() depends on the address family of the socket
    # for AF_INET(IPv4), bind() expects a tuple (host, port)
    s.bind((HOST, PORT))
    s.listen()

    # When a client connects, it returns
    # conn - a new socket object representing the connection
    # addr - a tuple holding the address of the client (host, port) for IPv4 or (host, port, flowinfo, scopeid) for IPv6
    conn, addr = s.accept()

    # conn is a different socket from 's' which was the original socket used to listen to and accept new connections
    with conn:
        print("Connected by", addr)

        # an infinite while loop is used to loop over blocking calls to conn.recv().
        # here it will read whatever data the client send and echoes it back using conn.sendall()
        while True:
            data = conn.recv(1024)
            
            # if conn.recv() returns an empty bytes object, b'', then the loop is terminated
            if not data:
                break
            conn.sendall(data)