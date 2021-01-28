import select, socket, sys

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)
server.bind(('localhost', 50000))
server.listen(5)
inputs = [server]
outputs = []
message_queues = {}

while inputs:
    readable, writable, exceptional = select.select(inputs, outputs, inputs)
    for s in readable:
        if s is server:
            connection, client_address = s.accept()
            connection.setblocking(0)
            inputs.append(connection)
            message_queues[connection] = []
        else:
            data = s.recv(1024)
            if data:
                message_queues[s].append(data)
                if s not in outputs:
                    outputs.append(s)
            else:
                if s in outputs:
                    outputs.remove(s)
                inputs.remove(s)
                s.close()
                del message_queues[s]

    for s in writable:
        if message_queues[s] == []:
            outputs.remove(s)
        else:
            next_msg = message_queues[s].pop(0)
            s.send(next_msg)

    for s in exceptional:
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()
        del message_queues[s]