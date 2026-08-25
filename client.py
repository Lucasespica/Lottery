import socket
import threading
import sys

HOST = "127.0.0.1"
PORT = 5000

# Conecta o cliente no socket
def conectarCliente():
    try: 
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        return client
    except ConnectionRefusedError:
        print("Servidor não encontrado")
        sys.exit(1)


# Cria thread que lê input do usuário e envia para o server em loop infinito
def enviarServer(client):
    while True:
        try:
            mensagem = input()
            if mensagem.strip(): # se tiver mensagem
                # Envia a mensagem codificada em bytes
                client.send(mensagem.encode('utf-8'))
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando cliente...")
            client.close()
            break

    

# Cria thread que lê do socket e imprime na tela
def receberServer(client):
    while True:
        data = client.recv(1024).decode('utf-8')
        if not data:
            print("Conexão encerrada pelo servidor") 
            break
        print(data)
            


def main():
    client = conectarCliente() # se a conexão for bem sucedida, imprimir o horário dela
    horario = client.recv(1024).decode('utf-8')
    print(horario)

    print("\n------------------------------------------------------------")
    print("Você pode:")
    print(" • Configurar: :inicio <num> | :fim <num> | :qtd <num>")
    print(" • Apostar: Digite os números separados por espaço (ex: 5 12 30)")
    print("------------------------------------------------------------")

    # Ao passar os args da função ele espera uma tupla, logo, precisa colocar em (x,y)
    t1 = threading.Thread(target=enviarServer, args=(client,), daemon=True)
    # Inicia a thread
    t1.start()

    t2 = threading.Thread(target=receberServer, args=(client,), daemon=False)
    # Inicia a thread
    t2.start()
    t2.join()


# se tiver neste arquivo rodando executa a main. Evita que ao importar ele rode automaticamente
if __name__ == '__main__':
    main()