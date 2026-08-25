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
INTERVALO = 60

# Cria thread que recebe dados do cliente (Lê do socket e usa como input para processamento) --> loop infinito de recebimento
def lerCliente(connection, address):
    # recebe dados enviados do cliente -> recv = receive é bloqueante e espera que haja alguma mensagem
    while True:
        data = connection.recv(1024).decode('utf-8')
        if not data:
            print(f" Cliente {address} desconectou.")
            break # sai do loop

        data = data.strip() # limpa espaços antes e depois do texto, sem mexer nos espaços do meio
        if not data:
            continue # pula a iteração atual

        # Mensagens que começam com ":" são comandos de configuração da loteria (:inicio 1, :fim 10, :qtd 3)
        if data.startswith(":"):
            partes = data.split()
            if len(partes) < 2:
                    continue
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
                numeros = []
                for p in partes:
                    numeros.append(int(p)) # guarda todos os inteiros numa nova lista
            except ValueError:
                print(f"Aposta inválida de {address}: {data}")
                continue

            # Guarda a aposta na lista deste cliente (with lock pelo mesmo motivo acima)
            with lock:
                clientes[connection]["apostas"].append(numeros)

            print(f"{address} apostou: {numeros}")

    with lock:
        if connection in clientes:
            del clientes[connection]
    connection.close()


# Cria thread que auxilia no envio de dados (envia o output do processamento do server para o cliente)
def enviarCliente(connection, address):

    while True:
        time.sleep(INTERVALO) # depois troca para 60, 10 para testes

        # Pega as configs atuais 
        with lock:
            if connection not in clientes:
                break  # Cliente já desconectou, encerra thread de envio

            inicio = clientes[connection]["inicio"]
            fim = clientes[connection]["fim"]
            qtd = clientes[connection]["qtd"]
            apostas = list(clientes[connection]["apostas"])
            # Zera a lista de apostas para o novo ciclo
            clientes[connection]["apostas"].clear()
    
        # Valida se os numeros de apostas sao válidos para o total de numeros
        tam = (fim - inicio) + 1
        if tam < qtd or qtd <= 0:
            msg_erro = f"\n Erro no sorteio: O intervalo [{inicio}, {fim}] não comporta {qtd} números distintos.\n"
            try:
                connection.send(msg_erro.encode('utf-8'))
            except (ConnectionResetError, BrokenPipeError):
                break
            continue

        # Realiza os sorteios 
        sorteados = set(random.sample(range(inicio, fim + 1), qtd)) # de 'inicio' ao 'fim' pega 'qnd' numeros numa amostra de forma aleatória

        # Manda mensagem pro cliente
        msg_enviada = f"\n--- Sorteio: {sorted(list(sorteados))} ---\n"
        if not apostas:
            msg_enviada += "Sem apostas feitas neste ciclo.\n"
        else:
            # Percorre cada aposta individualmente (evita o erro do set)
            for aposta in apostas:
                acertos = set(aposta).intersection(sorteados)
                msg_enviada += f"Aposta: {aposta} | Acertos ({len(acertos)}): {sorted(list(acertos))}\n"

        try:
            connection.send(msg_enviada.encode('utf-8'))
        except (ConnectionResetError, BrokenPipeError):
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
                    "apostas": [] # isso é uma lista de listas de numeros apostados
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