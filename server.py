import socket
import threading
import random
import time

HOST = "127.0.0.1" # Padrão localhost
PORT = 5000 # Portas a cima de 1023 são sem privilégio, ou seja, podem ser acessadas sem precisar pedir

# Configurando a loteria
loteria = []
sorteados = []

# Adiciona 5 numeros aleatórios na lista de numeros sorteados
for i in range(5):
    sorteados.append(random.randint(0, 100))


# Cria thread que recebe dados do cliente (Lê do socket e usa como input para processamento) --> loop infinito de recebimento
def lerCliente(connection, address):
    # recebe dados enviados do cliente -> recv = receive é bloqueante e espera que aja alguma mensagem
    while True:
        data = connection.recv(1024).decode('utf-8')
        if not data:
            print(f" Cliente {address} desconectou.")
            break

        print(f"{data}")

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
    # connection recebe o socket atrelado ao cliente conectado. Já o endereço é uma tupla contendo o ip e a porta do client
    return server


def main():
    server = iniciarServer()
    try:
        # Fica esperando em um loop infinito os clientes
        while True:
            connection, address = server.accept() # aqui ele bloqueia a execução do código e espera um cliente
            # Quando se conectar, cria as threads de auxílio para ele
            # Daemon true significa que quando o programa termina, a thread termina junto com ele. Logo, não precisamos esperar a thread com join, visto que o programa estará em um eterno loop de espera de clientes
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