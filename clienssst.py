import socket

HOST = "192.168.247.135"
PORT = 9002

mensagem = input("[Cliente] Nickname: ")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
    cliente.connect((HOST, PORT))
    cliente.sendall(mensagem.encode("utf-8"))

    resposta = cliente.recv(1024).decode("utf-8")
    print(f"[Server] {resposta}")
    while True:
        msg = input("Mensagem: ")
        cliente.sendall(msg.encode("utf-8"))
        resposta = cliente.recv(1024).decode("utf-8") 
        print(resposta)