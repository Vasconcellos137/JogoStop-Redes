import socket
import threading
import random
from datetime import datetime #pegar data e hr

HOST = "0.0.0.0"
PORT = 9002

n_jogadores = 3 #fixo por enquanto
n_rodadas = 3

LETRA = " " #guardar letra sorteada

# Dados d jogadores
nomes = [""] * n_jogadores #cria lista c/ quant d jogadores certa
enderecos = [None] * n_jogadores #guarda IP dos jogadores. "None" -> cria espaço na memória
respostas = [{} for i in range(n_jogadores)] #cria espaço p guardar infos diversas
pontuacoes = [0] * n_jogadores #cria lista p guadar pontos p cada jogador

# Sincronização
semaforo_inicio = threading.Semaphore(0) #inicia em red
semaforo_fim = [threading.Semaphore(0) for i in range(n_jogadores)] #cria um semáfaro fechado p cada jogador 

lock = threading.Lock() #controlar qm entra, uma chave/fechadura 

#Função p imprimir com hr, nome e ip as msg
def imprimirMsg(msg, nome, addr):
    hora = datetime.now().strftime("%H:%M:%S") #pega hr e formata no padrão 
    print(f"[{hora}] {nome} ({addr[0]}): {msg}") #printa as infos hr, nome e IP junto à msg 


def atenderCliente(conn, addr, tid):
    global respostas
 
    with conn:
        # Recebe nome primeiro
        nome = conn.recv(1024).decode()
        nomes[tid] = nome
        enderecos[tid] = addr

        print(f"{nome} conectado de {addr}")

        for rodada in range(n_rodadas):
            # Espera início da rodada
            semaforo_inicio.acquire()

            # Envia letra
            conn.sendall(f"LETRA:{LETRA}".encode())

            # Recebe respostas (formato simples)
            data = conn.recv(1024).decode()

            imprimirMsg(data, nome, addr)

            #Divide a msg do jogador p ficar certo na lista, cada coisa em seu lugar
            # Exemplo esperado: CEP=Toledo;NOME=Tiago
            respostas_jogador = {}
            for item in data.split(";"):
                chave, valor = item.split("=")
                respostas_jogador[chave] = valor

            # Protege acesso, usa "chave" p entrar e fazer o que precisa
            with lock:
                respostas[tid] = respostas_jogador

            # Avisa que terminou
            semaforo_fim[tid].release()

            # Espera resultado
            resultado = conn.recv(1024)  # só pra sincronizar

        # Envia placar final
        vencedor = nomes[pontuacoes.index(max(pontuacoes))]
        conn.sendall(f"FINAL:{pontuacoes};VENCEDOR:{vencedor}".encode())


def calcular_pontos():
    global pontuacoes

    categorias = respostas[0].keys()

    for categoria in categorias:
        valores = [respostas[i][categoria] for i in range(n_jogadores)]

        for i in range(n_jogadores):
            if valores.count(valores[i]) == 1:
                pontuacoes[i] += 3
            else:
                pontuacoes[i] += 1


def iniciar_servidor():
    global LETRA

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()

        print(f"Servidor ouvindo em {HOST}:{PORT}")

        threads = []

        # Conectar jogadores
        for i in range(n_jogadores):
            conn, addr = server.accept()
            t = threading.Thread(target=atender_cliente, args=(conn, addr, i))
            t.start()
            threads.append(t)

        # Rodadas
        for rodada in range(n_rodadas):
            print(f"\n--- Rodada {rodada+1} ---")

            respostas.clear()
            respostas.extend([{} for _ in range(n_jogadores)])

            LETRA = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            print(f"Letra sorteada: {LETRA}")

            # Libera jogadores
            for _ in range(n_jogadores):
                semaforo_inicio.release()

            # Espera todos responderem
            for sem in semaforo_fim:
                sem.acquire()

            # Calcula pontos
            calcular_pontos()

            print("Pontuação:", pontuacoes)

        # Espera threads
        for t in threads:
            t.join()


if __name__ == "__main__":
    iniciar_servidor()