import socket
import threading
import random
import time
from datetime import datetime

HOST = "127.0.0.1" # Padrão localhost
PORT = 5000 # Portas a cima de 1023 são sem privilégio, ou seja, podem ser acessadas sem precisar pedir
# Estado de cada cliente: connection -> {"inicio":0, "fim":100, "qtd":5, "apostas":[...]}
clientes = {}
lock = threading.Lock()   # Evita race condition


# Cria thread que recebe dados do cliente (Lê do socket e usa como input para processamento) --> loop infinito de recebimento
def lerCliente(connection, address):
    # recebe dados enviados do cliente -> recv = receive é bloqueante e espera que aja alguma mensagem
    while True:
        data = connection.recv(1024).decode('utf-8')
        if not data:
            print(f" Cliente {address} desconectou.")
            break

        data = data.strip()
        if not data:
            continue

        # Mensagens que começam com ":" são comandos de configuração da loteria (:inicio, :fim, :qtd)
        if data.startswith(":"):
            partes = data.split()
            comando = partes[0]

            try:
                valor = int(partes[1])
            except (IndexError, ValueError):
                print(f"Comando inválido de {address}: {data}")
                continue

            # Atualiza a config apenas deste cliente (with lock evita race condition com a thread de sorteio)
            with lock:
                if comando == ":inicio":
                    clientes[connection]["inicio"] = valor
                elif comando == ":fim":
                    clientes[connection]["fim"] = valor
                elif comando == ":qtd":
                    clientes[connection]["qtd"] = valor
                else:
                    print(f"Comando desconhecido de {address}")
                    continue

            print(f"{address} configurou {comando} = {valor}")

        # Senão, é uma aposta: números separados por espaço
        else:
            partes = data.split()
            try:
                numeros = [int(p) for p in partes]
            except ValueError:
                print(f"Aposta inválida de {address}: {data}")
                continue

            # Guarda a aposta na lista deste cliente (with lock pelo mesmo motivo acima)
            with lock:
                clientes[connection]["apostas"].append(numeros)

            print(f"{address} apostou: {numeros}")

    connection.close()


# Cria thread que auxilia no envio de dados (envia o output do processamento do server para o cliente)
def enviarCliente(connection, address):

    while True:
        time.sleep(10) # depois troca para 60, 10 para testes
        try:
            connection.send(sorteados.encode('utf-8'))
        except ConnectionResetError:
            break
        

# socket.AF_INET = para definir que vamos usar IPv4 e socket.SOCK_STREAM para dizer que é TCP
# Com o with vc não precisa se preocupar em fechar o socket.close(), ele já gerencia no contexto.
# Cria socket servidor
def iniciarServer():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    # servidor está esperando o handshake
    server.listen()
    # timeout no accept: faz o accept() "acordar" a cada 0.5s e checar Ctrl+C, em vez de bloquear pra sempre
    server.settimeout(0.5)
    # connection recebe o socket atrelado ao cliente conectado. Já o endereço é uma tupla contendo o ip e a porta do client
    return server


def main():
    server = iniciarServer()
    try:
        # Fica esperando em um loop infinito os clientes
        while True:
            try:
                connection, address = server.accept() # aqui ele bloqueia a execução do código e espera um cliente (com timeout de 0.5s)
            except TimeoutError:
                # ninguém conectou nesse 0.5s, volta pro topo do loop e o Python consegue checar o Ctrl+C
                continue

            # Faz o registro do cliente com lock para evitar race condition
            with lock:
                clientes[connection] = {
                    "inicio": 0,
                    "fim": 100,
                    "qtd": 5,
                    "apostas": []
                }

            # Quando se conectar, cria as threads de auxílio para ele
            # Daemon true significa que quando o programa termina, a thread termina junto com ele. Logo, não precisamos esperar a thread com join, visto que o programa estará em um eterno loop de espera de clientes
            horario = datetime.now().strftime("%H:%M:%S")
            connection.send(f"{horario}: CONECTADO!!".encode('utf-8')) # Servidor irá enviar o horário

            t1 = threading.Thread(target=lerCliente, args=(connection, address), daemon=True)
            t1.start()

            t2 = threading.Thread(target=enviarCliente, args=(connection, address), daemon=True)
            t2.start()
    # Essa exeção acontece quando o usuário encerra o programa 
    except KeyboardInterrupt:
        print("\nServidor finalizado pelo teclado (Ctrl+C).")
    finally:
        server.close()


if __name__ == '__main__':
    main()