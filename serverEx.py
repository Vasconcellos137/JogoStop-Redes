import socket
import threading
from time import sleep

HOST = "0.0.0.0"
PORT = 9002

LETRA = " "

CEP = [" ", " "]
NOME = [" ", " "]

semaforo = threading.Semaphore(0)

semaforo_jogadores = [
    threading.Semaphore(0),
    threading.Semaphore(0)
]

def atender_cliente(conn, addr, tid):
    global CEP, NOME

    semaforo.acquire()

    with conn:
        #Envia letra sorteada aos clientes
        conn.sendall(LETRA.encode())

        #Envia msg a cliente
        conn.sendall("CEP: ".encode())
        #Aguarda resp
        res = conn.recv(1024).decode()
        CEP[tid] = res

        #Envia msg a cliente
        conn.sendall("NOME: ".encode())
        #Aguarda resp
        res = conn.recv(1024).decode()
        NOME[tid] = res

        semaforo_jogadores[tid].release()


def iniciar_servidor():
    global LETRA
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  
        server.bind((HOST, PORT))                                            
        server.listen()

        print(f"Servidor ouvindo em {HOST}:{PORT}")

        #Aguarda jog1
        conn_1, addr_1 = server.accept()
        thread_1 = threading.Thread(target=atender_cliente, args=(conn_1, addr_1, 0), daemon=True)
        thread_1.start()

        #Aguarda jog2
        conn_2, addr_2 = server.accept()
        thread_2 = threading.Thread(target=atender_cliente, args=(conn_2, addr_2, 1), daemon=True)
        thread_2.start()

        #Sortea uma letra
        LETRA = "T"

        #Libera semáforo
        semaforo.release()
        semaforo.release()

        #Aguarda os jogadores responderem
        for sem_i in semaforo_jogadores:
            sem_i.acquire()

        #Printa a jogadas dos clientes
        print(CEP)
        print(NOME)

        #Aguarda os clientes jogar
        thread_1.join()
        thread_2.join()

if __name__ == "__main__":
    iniciar_servidor()