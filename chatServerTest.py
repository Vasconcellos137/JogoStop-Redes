import socket
import threading
import random
from datetime import datetime #pegar data e hr
import time #serve p contar tempo, é como um cronômetro msm

HOST = "0.0.0.0"
PORT = 9002

n_jogadores = 3 
n_rodadas = 3
tempoJogo = 60 #tempo d duração, em seg

LETRA = " " #guardar letra sorteada
FILA = []

# Dados d jogadores
nomes = [""] * n_jogadores #cria lista c/ quant d jogadores certa
ips = [None] * n_jogadores #guarda IP dos jogadores. "None" -> cria espaço vazio na memória
respostas = [{} for i in range(n_jogadores)] #cria espaço p guardar infos diversas, esse tipo d lista é como um registro, possui categorias para cada coisa  
pontuacoes = [0] * n_jogadores #cria lista p guadar pontos p cada jogador

# Sincronização
semaforo_inicio = threading.Semaphore(0) #inicia 
SEMAFORO_ACESSO = threading.Semaphore(1) # controla acesso à fila
SEMAFORO_ITENS = threading.Semaphore(0)  # quantos itens existem

lock = threading.Lock() #controlar qm entra, uma chave/fechadura 

#Pra controle d tempo e termino das rodadas
fim = False     
tempoInicial = 0

#P/ imprimir com hr, nome e ip as msg
def imprimirMsg(msg, nome, addr):
    hora = datetime.now().strftime("%H:%M:%S") #pega hr e formata no padrão 
    print(f"[{hora}] {nome} ({addr[0]}): {msg}") #printa as infos hr, nome e IP junto à msg 

#Fila's métodos
def produzir(tid, respostas_jogador):
    SEMAFORO_ACESSO.acquire()
    FILA.append((tid, respostas_jogador))
    SEMAFORO_ACESSO.release()
    SEMAFORO_ITENS.release()

def consumir():
    SEMAFORO_ITENS.acquire()
    SEMAFORO_ACESSO.acquire()
    msg = FILA.pop(0)
    SEMAFORO_ACESSO.release()
    return msg

def threadConsumidora():
    global respostas
    while True:
        tid, resp = consumir()
        with lock:
            respostas[tid] = resp


def atenderCliente(conn, addr, tid): #tid -> pos do jogador na lista, ordem d qm joga 1°
    global fim #"global" serve p poder usar os valores d variavel q está fora d função
 
    with conn:
        # Recebe nome primeiro
        nome = conn.recv(1024).decode("utf-8")
        nomes[tid] = nome
        ips[tid] = addr

        print(f"{nome} conectado de {addr}")

        for rodada in range(n_rodadas):
            # Espera início da rodada
            semaforo_inicio.acquire()

            # Verifica se fim d rodada == true
            if fim:
                break

            # Envia letra sorteada
            conn.sendall(f"LETRA:{LETRA}".encode())

            try:
            # Recebe respostas
                data = conn.recv(1024).decode()
            except: 
                break

            #Verifica se fim d rodada == true, novamente
            if fim:
                break

            imprimirMsg(data, nome, addr)

            #Divide a msg do jogador p ficar certo na lista, cada coisa em seu lugar
            respostas_jogador = {}
            for item in data.split(";"):
                chave, valor = item.split("=")
                respostas_jogador[chave] = valor

            # jogador produz, coloca na fila
            produzir(tid, respostas_jogador)
 
            # primeiro que terminar encerra rodada
            with lock:
                if not fim:
                    fim = True

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
    global LETRA, fim, tempoInicial

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()

        print(f"Servidor ouvindo em {HOST}:{PORT}")

        threading.Thread(target=threadConsumidora, daemon=True).start()

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
            FILA.clear()

            LETRA = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") #".choice()" -> serve p sortear alguma letra aleatória dentro da lista 
            print(f"Letra sorteada: {LETRA}")

            fim = False
            tempoInicial = time.time() #guarda o momento em que o jogo começou, começa a contar a partir daí

            # Libera jogadores, um por um, por isso percorre
            for i in range(n_jogadores):
                semaforo_inicio.release()

            #Espera alguém terminar ou tempo acabar
            while True:
                if fim:   #Se true == stop
                    print("STOP!")
                    break

                #time.time() - tempoInicial -> ver quanto tempo já passou desde o começo
                if time.time() - tempoInicial >= tempoJogo: #Se tempo acabou == stop
                    print("Tempo esgotado!")
                    fim = True
                    break

                #Tempinho antes d rodar d novo
                time.sleep(0.2)

            # Calcula pontos
            calcularPontos()

            print("Pontuação: ", pontuacoes)

        # Espera threads
        for t in threads:
            t.join()


if __name__ == "__main__":
    iniciarServidor()