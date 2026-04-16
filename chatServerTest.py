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
respostas = [{} for i in range(n_jogadores)] #cria espaço p guardar infos diversas, esse tipo d lista é como um registro, possui categorias para cada coisa  
pontuacoes = [0] * n_jogadores #cria lista p guadar pontos p cada jogador

# Sincronização
semaforo_inicio = threading.Semaphore(0) #inicia em red
semaforo_fim = [threading.Semaphore(0) for i in range(n_jogadores)] #cria um semáfaro fechado p cada jogador 

lock = threading.Lock() #controlar qm entra, uma chave/fechadura 

#Função p imprimir com hr, nome e ip as msg
def imprimirMsg(msg, nome, addr):
    hora = datetime.now().strftime("%H:%M:%S") #pega hr e formata no padrão 
    print(f"[{hora}] {nome} ({addr[0]}): {msg}") #printa as infos hr, nome e IP junto à msg 


def atenderCliente(conn, addr, tid): #tid -> pos do jogador na lista, ordem d qm joga 1°
    global respostas #"global" serve p poder usar os valores d variavel q está fora d função
 
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
            respostas_jogador = {}
            for item in data.split(";"):
                chave, valor = item.split("=")
                respostas_jogador[chave] = valor

            # Protege acesso, usa "chave" p entrar e fazer o que precisa
            with lock:
                respostas[tid] = respostas_jogador

            # Avisa que terminou
            semaforo_fim[tid].release()

            # Espera resultado do server p continuar
            resultado = conn.recv(1024)  

        # Envia placar final
        vencedor = nomes[pontuacoes.index(max(pontuacoes))] #pega lista d nomes e pontos, compara p decobrir qm tem mais pontos dentre eles e imprime o nome 
        conn.sendall(f"Placar final: {pontuacoes} - Vencedor: {vencedor}".encode()) 


def calcularPontos():
    global pontuacoes

    categorias = respostas[0].keys() #pega os nomes das categorias dentre as respostas dos jogadores p poder fazer comparação entre os resultados.

    for categoria in categorias:
        valores = [respostas[i][categoria] for i in range(n_jogadores)] #percorre todas as resp d uma msm categoria, e percorre isso d todos os jogadores

        for i in range(n_jogadores):
            if valores.count(valores[i]) == 1: #.count() -> conta quantas vezes a msm resposta aparece dentre as respostas percorridas
                pontuacoes[i] += 3 
            else:
                pontuacoes[i] += 1


def iniciarServidor():
    global LETRA

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()

        print(f"Servidor ouvindo em {HOST}:{PORT}")

        threads = []

        # Conectar jogadores
        for i in range(n_jogadores):
            conn, addr = server.accept()
            t = threading.Thread(target=atenderCliente, args=(conn, addr, i))
            t.start()
            threads.append(t)

        # Rodadas
        for rodada in range(n_rodadas):
            print(f"\n--- Rodada {rodada+1} ---")

            respostas.clear()
            respostas.extend([{} for i in range(n_jogadores)]) #".extend()" -> coloca infos dentro da lista d jogadores, paa cada um, um espaço diferente

            LETRA = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") #".choice()" -> serve p sortear alguma letra aleatória dentro da lista 
            print(f"Letra sorteada: {LETRA}")

            # Libera jogadores, um por um
            for i in range(n_jogadores):
                semaforo_inicio.release()

            # Espera todos responderem
            for sem in semaforo_fim:
                sem.acquire()

            # Calcula pontos
            calcularPontos()

            print("Pontuação: ", pontuacoes)

        # Espera threads
        for t in threads:
            t.join()


if __name__ == "__main__":
    iniciarServidor()