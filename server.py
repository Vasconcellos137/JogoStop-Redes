import socket
import threading
import random
from datetime import datetime #pegar data e hr
import time #serve p contar tempo, é como um cronômetro msm

HOST = "0.0.0.0"
PORT = 9002

n_jogadores = 3 
n_rodadas = 3
tempoJogo = 180 #tempo d duração, em seg -> 3min

# LETRA = " " #guardar letra sorteada

# Dados d jogadores
nomes = [""] * n_jogadores #cria lista c/ quant d jogadores certa
ips = [None] * n_jogadores #guarda IP dos jogadores. "None" -> cria espaço vazio na memória
conexoes = [None] * n_jogadores # mesma coisa q ips, mas p guardar a conexão
respostas = [{} for i in range(n_jogadores)] #cria espaço p guardar infos diversas, esse tipo d lista é como um registro, possui categorias para cada coisa  
pontuacoes = [0] * n_jogadores #cria lista p guadar pontos p cada jogador

# Sincronização das threds
FILA = []
SEMAFORO_ACESSO = threading.Semaphore(1) # controla acesso à fila
SEMAFORO_ITENS = threading.Semaphore(0)  # quantos itens existem

lock = threading.Lock() #controlar qm entra, uma chave/fechadura 

#Pra controle d tempo e termino das rodadas
fim = False     
resposRecv = 0 #contar quantas respostas já foram recebidas -> p saber quando parar a rodada

#P/ imprimir com hr, nome e ip as msg
def imprimirMsg(msg, nome, addr):
    hora = datetime.now().strftime("%H:%M:%S") #pega hr e formata no padrão 
    print(f"[{hora}] {nome} ({addr[0]}): {msg}") #printa as infos hr, nome e IP junto à msg 

def enviarAtodos(msg):
    for conn in conexoes:
        try:
            conn.sendall((msg + "\n").encode())
        except:
            pass

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
    global respostas, resposRecv
    while True:
        tid, resp = consumir()
        with lock:
            respostas[tid] = resp
            resposRecv += 1


def atenderCliente(conn, addr, tid): #tid -> pos do jogador na lista, ordem d qm joga 1°
    global fim #"global" serve p poder usar os valores d variavel q está fora d função
 
    with conn:
        # Recebe nome primeiro
        nome = conn.recv(1024).decode("utf-8").strip() #decodifica a msg recebida e tira espaços e quebras de linha, msm q \n, \r
        nomes[tid] = nome
        ips[tid] = addr #guarda o IP do jogador na lista, na posição correspondente ao jogador
        conexoes[tid] = conn

        print(f"{nome} conectado de {addr}")

        while True:
            try:
                msg = conn.recv(1024).decode().strip() #tenta enviar msg
            except:
                break #se der erro, fecha a conexão e para a thread 

            if not msg: #se a msg for vazia, break
                break
            
            if msg.startswith("RESPOSTAS:"):
                data = msg.split(":", 1)[1] #divide a msg em 2 partes, usando ":" como base, e pega a parte d resposta
                imprimirMsg(data, nome, addr)

                #Divide a msg do jogador p ficar certo na lista, cada coisa em seu lugar
                respostas_jogador = {}
                for item in data.split(";"):
                    if "=" in item:
                        chave, valor = item.split("=")
                        respostas_jogador[chave] = valor

            # jogador produz, coloca na fila 
            produzir(tid, respostas_jogador)

def calcularPontos():
    global pontuacoes

    if not respostas[0]:
        return

    categorias = respostas[0].keys() #pega os nomes das categorias dentre as respostas dos jogadores p poder fazer comparação entre os resultados.

    for categoria in categorias:
        valores = [respostas[i][categoria] for i in range(n_jogadores)] #percorre todas as resp d uma msm categoria, e percorre isso d todos os jogadores

        for i in range(n_jogadores):
            if valores.count(valores[i]) == 1: #.count() -> conta quantas vezes a msm resposta aparece dentre as respostas percorridas
                pontuacoes[i] += 3 
            else:
                pontuacoes[i] += 1

def iniciarServidor():
    global fim, respostas, resposRecv

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

            time.sleep(1.0)  

        # Rodadas
        for rodada in range(n_rodadas):
            print(f"\n><>< Rodada {rodada+1} ><><")

            # respostas.clear()
            respostas.extend([{} for i in range(n_jogadores)]) #".extend()" -> coloca infos dentro da lista d jogadores, pra cada um, um espaço diferente
            FILA.clear()
            resposRecv = 0 #reset contador
            fim = False

            LETRA = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") #".choice()" -> serve p sortear alguma letra aleatória dentro da lista 
            print("Letra sorteada:", LETRA)

            enviarAtodos("Letra: ", LETRA)

            tempoInicial = time.time() #guarda o momento em que o jogo começou, começa a contar a partir daí

            #Espera alguém terminar ou tempo acabar
            while True:
                with lock:
                    if resposRecv == n_jogadores:  #Se true == stop
                        print("STOP!")
                        break

                #time.time() - tempoInicial -> ver quanto tempo já passou desde o começo
                if time.time() - tempoInicial >= tempoJogo: #Se tempo acabou == stop
                    print("Tempo esgotado!")
                    break

                #Tempinho antes d rodar d novo
                time.sleep(1.0)

            fim = True

            # Calcula pontos
            calcularPontos()
            enviarAtodos("Placar: ", pontuacoes)

            # Envia placar final
            vencedor = nomes[pontuacoes.index(max(pontuacoes))] #pega lista d nomes e pontos, compara p decobrir qm tem mais pontos dentre eles e imprime o nome 
            enviarAtodos(f"Placar Final: {pontuacoes}, Vencedor: {vencedor}")

        # Espera threads
        for t in threads:
            t.join()


if __name__ == "__main__":
    iniciarServidor()