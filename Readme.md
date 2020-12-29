# Socket Programming with Python

## Sockets

Sockets and socket API are used to send messges across a network. They provided a form of inter-process communication (IPC). Example is the internet, which we connect to via our ISP.

The most common type of socket applications are client-server applications, where one side acts as the server and waits for connections from clients.

## Socket API Overview

Python's socket [module](https://docs.python.org/3/library/socket.html) provides an interface to the Berkeyly Sockets [API](https://en.wikipedia.org/wiki/Berkeley_sockets). The primary socket API functions and methods in this module are:

- `socket()`: creates a new socket and allocates resources to it
- `bind()`: associates a socket with a socket address structure, i.e. a specified local IP address and a port number. It is used on the server side.
- `listen()`: causes a bound Transmission Control Protocol (TCP) socket to enter a listening state. It is used on the server side.
- `connect()`:assigns a free local port number to a socket. In case of a TCP socket, it causes an attempt to establish a new TCP connection. It is used on the client side.
- `accept()`: accepts a received incoming attempt to create a new TCP connection from the remote client, and creates a new socket associated with the socket address pair of this connection. It is used on the server side.
- `connect_ex()`: like `connect()`, but returns an error indicator instead of raising an exception for errors returned by the C-level connect() call ( other problems, such as "host not found", can still raise exceptions). The error indicator is `0` if the operation succeeded, otherwise the value of the `errno` variable. This is useful to support for example, asynchronous connects.
- `send()` : to send data
- `recv()` : to receive data
- `close()`: causes teh system to release resources allocated to a socket. In case of TCP, the connection is terminated.

As part of its standard library, Python also has [classes](https://docs.python.org/3/library/socketserver.html) that make using these low-level socket functions easier. Read about implementing internet protocols like HTTP and SMTP [here](https://docs.python.org/3/library/internet.html).

## TCP Socket Flow

We are going to use TCP socket here.
![tcp-socket-fow](sockets-tcp-flow.webp)

Here on the server side, `socket()` creates new socket, `bind()` associates the new socket with an address, and `listen()` listens to a connection request. Whena client connects using `connect()`, the server calls `accept()` to accept the connection.

TCP uses three-way [handsake](https://en.wikipedia.org/wiki/Handshaking) to establish a connection.

1. The client sends the server a synchronize (SYN) message with its own sequence number `x`.
2. The server replies with a synchronize-acknowledgment(SYN-ACK) message with its own sequence number `y` and acknowledgement number `x + 1`.
3. The client replies with an acknowledgement (ACK) message with acknowledge number `y + 1`.

The middle is the round-trip section, where data is exchanged between the client and server using cals to `send()` and `recv()`.

In the end, the client and server `close()` their respective sockets to end the connection.

## Echo Client and Server

Here, the server will simply echo whatever it receives back to the client.

### Echo Server

`echo-server.py`

```python
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
```

### Echo Client

create file `echo-client.py`

```python
import socket

HOST = '127.0.0.1' # The server's hostname or IP address
PORT = 65432 # The port used by the server


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Hello, world')
    data = s.recv(1024)

print('Received', repr(data))
```

### Run

in one terminal run

```
python echo-server.py
```

in the next terminal run

```
python echo-client.py
```

### Outputs

server:

```
Connected by ('127.0.0.1', 54803)
```

client:

```
Received b'Hello, world'
```

## Viewing Socket State

On Windows, macOS and linux, we can see the current state of the host by using `netstat` which is available in all of the platforms:

```
netstat -an
```

The output look like

```
Proto  Local Address          Foreign Address        State
  TCP    0.0.0.0:557           0.0.0.0:0              LISTENING
  TCP    0.0.0.0:544           0.0.0.0:0              LISTENING
  TCP    127.0.0.1:65432       0.0.0.0:0              LISTENING # this one is our server
```

Note: [loopback](https://en.wikipedia.org/wiki/Localhost) interface or IP address 127.0.0.1 or ::1 is also refferred to as "localhost". The data never leaves the host or touches the external network.

## Multi-Connection Client and Server

Here, we will create a server and client that handles multiple connections using a `selector` object created from the [selectors](https://docs.python.org/3/library/selectors.html) module.

Some keywords:

- `select` module is a direct interface to the underlying operating system implementation. It monitors sockets, open files, and pipes (anything with a fileno() method that returns a valid file descriptor) until they become readable or writable, or a communication error occurs.
- `selectors` is a python module which allows high-level and efficient I/O multiplexing, built upon the select module primitives. It defines a [BaseSelector](https://docs.python.org/3/library/selectors.html#selectors.BaseSelector) abstract base class, along with several concrete implementations (KqueueSelector, EpollSelector, etc), that can be used to wait for I/O readiness notification on multiple filie objects.

### Multi-Connection Server

The main objective of a multi-connection server is to be non-blocking so that it can establish connection to other sockets.

Create `multiconn-server.py`:

```python
import selectors
import socket
import types
import sys

sel = selectors.DefaultSelector()


def accept_wrapper(sock):
    # since listening socket was registered for the event selectors.EVENT_READ, it should be
    # ready to read
    # Hence we can call sock.accept()
    conn, addr = sock.accept()
    print('accepted connection from', addr)

    # we set socket in non-blocking mode again
    conn.setblocking(False)

    # creates an object to hold the data we want included along with the socket
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')

    # monitors to check when the client connection is ready for reading and writing
    events = selectors.EVENT_READ | selectors.EVENT_WRITE

    # the arguments are socket, mask, and data
    sel.register(conn, events, data=data)


def service_connection(key, mask):
    # key is the 'namedtuple' returned from select() that contains
    # - sockobject: fileobj
    # - data object - data
    sock = key.fileobj
    data = key.data

    # 'mask' contains the events taht are ready

    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024) # should be ready to read
        if recv_data:
            # any data that's read is appended to data.outb so it can be sent later
            data.outb += recv_data
        # block if no data is received
        # this means that the client has closed their socket
        else:
            print('closing connection to', data.addr)

            # unregister so that it's no longer monitered by select()
            sel.unregister(sock)

            # close the socket
            sock.close()

    # a healthy socket should always be ready for writing
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print('echoing', repr(data.outb), 'to', data.addr)

            # any received data stored in data.outb is echoed to the client
            sent = sock.send(data.outb) # should be ready to write

            # the bytes sent are then removed from the buffer
            data.outb = data.outb[sent:]



if len(sys.argv) != 3:
    print("usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])


# ...
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print("listening on", (host, port))

# this is different from 'echo-server.py' as lsock is set to non-blocking mode
# when it's used with sel.select() below, we can wait for events on one or more sockets
# and read and write data when it's ready
# - key: a SelectorKey 'namedtuple' that contains a 'fileobj' attribute
# - mask: an event mask of the operations that are ready
lsock.setblocking(False)

# this registers the socket to be monitored with sel.select() for the events we are
# interested in
# data - is used to store whatever arbitrary data we'd like along with the socket.
# It's returned when select() returns. data will be used to keep track what's been sent
# and received on the socket.
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:

        # sel.select(timeout=None) blocks until there are sockets ready for I/O.
        # It returns a list of (key, event) tuples, one for each socket.
        events = sel.select(timeout=None)
        for key, mask in events:
            # if key.data 'None', we know it's from the listening socket and we need to accept()
            # the connection
            if key.data is None:
                accept_wrapper(key.fileobj)
            # if key.data is not 'None', we know it's a client that's already been accepted, and
            # we need to service it.
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()
```

### Multi-Connection Client

It is similar to `multiconn-server.py` but instead of listening for connections, it starts by initiating connections via `start_connections()`:

```python
import socket
import selectors
import types
import sys

sel = selectors.DefaultSelector()

messages = [b'Message 1 from client.', b'Message 2 from client.']


# 'num_conns' is read from the command-line, which is the number of connections to create to the server
def start_connections(host, port, num_conns):
    server_addr = (host, port)
    for i in range(0, num_conns):
        connid = i + 1
        print("starting connection", connid, "to", server_addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # each socket is set to non-blocking mode
        sock.setblocking(False)

        # 'connect_ex()' is used instead of 'connect()' since 'connect()' would immediately raise a
        # 'BlockingIOError' exception.
        # 'connect_ex()' initially returns an erro indicator 'errno.EINPROGRESS', instead of raising
        # an exception while the connection is in progress
        sock.connect_ex(server_addr)

        # once the connection is completed, the socket is ready for reading and writing
        # the status is returned by 'select()'
        events = selectors.EVENT_READ | selectors.EVENT_WRITE

        # creates data we want stored in the socket
        # messages the client will send to the server are copied using 'list(messages)' since each
        # connection will call 'socket.sent()' and modify the list.
        # connid - connection id
        # msg_total - total bytes of messages sent
        # recv_total - total bytes of messages received
        # messages - message contents sent
        # outb - message that is sent per 'send()' operation
        data = types.SimpleNamespace(connid=connid, msg_total=sum(len(m) for m in messages), recv_total=0, messages=list(messages), outb=b'')
        sel.register(sock, events, data=data)


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024) # should be ready to read
        if recv_data:
            print('received', repr(recv_data), 'from connection', data.connid)

            # keeps track of the number of bytes received from the server
            data.recv_total += len(recv_data)

        # when it is not receiving any data or when 'data.recv_total' == 'data.msg_total', close connection
        if not recv_data or data.recv_total == data.msg_total:
            print('closing connection', data.connid)
            sel.unregister(sock)
            sock.close()

    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            # takes out the last element in the list and saves it to 'data.outb'
            data.outb = data.messages.pop(0)
        if data.outb:
            print('sending', repr(data.outb), 'to connection', data.connid)

            # sends 'data.outb'
            sent = sock.send(data.outb) # should be ready to write

            # empties 'data.outb'
            data.outb = data.outb[sent:]


if len(sys.argv) != 4:
    print("usage:", sys.argv[0], "<host> <port> <num_connections>")
    sys.exit(1)


start_connections(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))

try:
    while True:
        events = sel.select(timeout=1)
        if events:
            for key, mask in events:
                service_connection(key, mask)

            # Check for a socket being monitored to continue
            if not sel.get_map():
                break
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()
```

Our client here keeps track of the number of bytes it's received from the server so it can close its side of the connection. When the server detects this, it also closes its side of the connection.

Hence, here, the server depends on the client being well-behaved. If the client doesn't close, the server will leave the connection open. In a real application, we may want to guard against this and prevent client connections from accumulating if they don't send a request after a certain amount of time or if a specific data usage limit has reached.

### Outputs

Start the server first

```cmd
// usage: ./multiconn-server.py <host> <port>
python multiconn-server.py 127.0.0.1 65432
```

Then, start the client:

```cmd
// usage: ./multiconn-client.py <host> <port> <num_connections>
python multiconn-client.py 127.0.0.1 5
``
```

Sample Client output:

```
starting connection 1 to ('127.0.0.1', 65432)
starting connection 2 to ('127.0.0.1', 65432)
starting connection 3 to ('127.0.0.1', 65432)
starting connection 4 to ('127.0.0.1', 65432)
starting connection 5 to ('127.0.0.1', 65432)
sending b'Message 1 from client.' to connection 4
sending b'Message 1 from client.' to connection 5
sending b'Message 1 from client.' to connection 1
sending b'Message 1 from client.' to connection 2
sending b'Message 1 from client.' to connection 3
received b'Message 1 from client.' from connection 4
sending b'Message 2 from client.' to connection 4
received b'Message 1 from client.' from connection 5
sending b'Message 2 from client.' to connection 5
sending b'Message 2 from client.' to connection 1
sending b'Message 2 from client.' to connection 2
sending b'Message 2 from client.' to connection 3
received b'Message 2 from client.' from connection 4
closing connection 4
received b'Message 2 from client.' from connection 5
closing connection 5
received b'Message 1 from client.Message 2 from client.' from connection 1
closing connection 1
received b'Message 1 from client.Message 2 from client.' from connection 2
closing connection 2
received b'Message 1 from client.Message 2 from client.' from connection 3
closing connection 3
```

Sample Server output:

```
listening on ('127.0.0.1', 65432)
accepted connection from ('127.0.0.1', 53242)
accepted connection from ('127.0.0.1', 53243)
accepted connection from ('127.0.0.1', 53244)
accepted connection from ('127.0.0.1', 53245)
accepted connection from ('127.0.0.1', 53246)
echoing b'Message 1 from client.' to ('127.0.0.1', 53245)
echoing b'Message 1 from client.' to ('127.0.0.1', 53246)
echoing b'Message 1 from client.' to ('127.0.0.1', 53242)
echoing b'Message 1 from client.' to ('127.0.0.1', 53243)
echoing b'Message 1 from client.' to ('127.0.0.1', 53244)
echoing b'Message 2 from client.' to ('127.0.0.1', 53245)
echoing b'Message 2 from client.' to ('127.0.0.1', 53246)
echoing b'Message 2 from client.' to ('127.0.0.1', 53242)
echoing b'Message 2 from client.' to ('127.0.0.1', 53243)
echoing b'Message 2 from client.' to ('127.0.0.1', 53244)
closing connection to ('127.0.0.1', 53245)
closing connection to ('127.0.0.1', 53246)
closing connection to ('127.0.0.1', 53242)
closing connection to ('127.0.0.1', 53243)
closing connection to ('127.0.0.1', 53244)
```

## Application Client and Server

Apart from `OSError`, timeout etc, the main error can occur can processing the data itself. TCP only understands that it is receiving and sending raw bytes to and form the network. But doesn't understand the kind of data being transferred. Hence, this is where application-layer comes in.
According to Bitesize, **Application Layer** is a networking layer which encodes or decodes a message in a form that is understood by the sender and the receipient ([link](https://www.bbc.co.uk/bitesize/guides/z666pbk/revision/5)). It is used to understand the length and format of the application.

When we're reading bytes with recv(), we need to keep up with how many bytes were read and figure out where the message boundaries are. How is this done?

- One way is to always send fixed-length message. This is not a inefficient messages or insufficient for if the data is larger than the size we defined.
- Another way is what HTTP also does. We use a header that includes the content length as well as any other fields we need. Once we've read the header, we can process it to determine the length of the message's content and then allocate resources to consume the expected number of bytes.

We'll implement this by creating a custom header class that can send and receive messages that contain text or binary data.

Another problem can occuer with data interpretation. For example, if we receive data and want to use it in a context where it's interpreted as multiple bytes, for example a 4-byte integer, we'll need to take into account that it could be in a format that's not native to our machine's CPU. IF this is the case, we'll need to convert it to the host's native byte before using it. We'll avoid this by taking advantage of [Unicode](https://realpython.com/python-encodings-guide/) for our message and using the encoing UTF-8. Since UTF-8 uses an 8-bit encoding, there are no byte ordering issues. Read more in python's Encodings and Unicode documentation [here](https://docs.python.org/3/library/codecs.html#encodings-and-unicode).

The byte oder is referred to as CPU's [endianness](https://en.wikipedia.org/wiki/Endianness). Depending on where the the system stores most significant byte of a word (smallest memory address or largest memory address), the endianness is categorized as big-endian(BE) or little-endian(LE).
We can determine the byte oder of our machine using `sys.byteorder` by doing:

```cmd
python -c 'import sys; print(repr(sys.byteorder))'
'little' # output on my laptop
```

My laptop has little-endian byte ordering

More on the application, the UTF-8 encoding will only be used for header. FOr the acutal content in the message, we might have to swap the byte order manually if needed. This will depend on the application and whether or not it needs to process multi-byte binary data form a machine with different endianness.

### Application Protocol Header

More will be added soon..

Thanks to [RealPython](https://realpython.com/python-sockets/).
