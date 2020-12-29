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