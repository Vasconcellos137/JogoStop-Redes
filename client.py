import socket

# HOST = "127.0.0.1"
HOST = "192.168.100.107"
# HOST = " "
PORT = 9002

# HOST = input("Digite o IP do servidor: ")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
    cliente.connect((HOST, PORT))

    nome = input("Nickname: ")
    cliente.send(nome.encode())

    for rodada in range(3): 
        
        letra = cliente.recv(1024).decode()
        print("Letra: ", letra)

        resposta = input("Respostas: ")
        cliente.send(resposta.encode())

        pontos = cliente.recv(1024).decode()
        print("Pontuação: ", pontos)


    final = cliente.recv(1024).decode()
    print("Placar final: ", final)

    cliente.close()