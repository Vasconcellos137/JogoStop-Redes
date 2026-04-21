import socket

# HOST = "127.0.0.1"
HOST = "192.168.100.107"
# HOST = " "
PORT = 9002

# HOST = input("Digite o IP do servidor: ")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
    cliente.connect((HOST, PORT))

    nome = input("Nickname: ")
    cliente.send((nome + "\n").encode())

    print("Categorias do jogo:")
    print("- nome")
    print("- animal")
    print("- cidade")
    print("- objeto")
    print("Formato de digitação:")
    print("nome=...;animal=...;cidade=...;objeto=...")

    while True:
        msg = cliente.recv(1024).decode().strip() #remove espaços e quebras de linha, msm coisa -> \n, \r 
        
        if msg.startswith("LETRA:"): #verifica se o texto começa com algo específico
            letra = msg.split(":")[1] #divide o texto em partes, usando como base ":" 
            print("\nLetra:", letra)

            resposta = input("Respostas: ")
            cliente.send(("RESPOSTAS: ", resposta).encode())

        elif msg.startswith("Placar parcial:"):
            print(msg)

        elif msg.startswith("Resultado Final:"):
            print(msg)
            break
       