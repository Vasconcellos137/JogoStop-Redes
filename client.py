import socket

HOST = "127.0.0.1"
PORT = 9002

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
    cliente.connect((HOST, PORT))

    letra = cliente.recv(1024).decode()
    print(f"[Letra sorteada:", letra)

    #CEP
    msg = cliente.recv(1024).decode()
    res = input(msg)
    cliente.sendall(res.encode())


    #NOME
    msg = cliente.recv(1024).decode()
    res = input(msg)
    cliente.sendall(res.encode())