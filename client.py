import socket
import sys
import threading

HOST_PADRAO = '127.0.0.1'
PORTA_PADRAO = 5000

def thread_teclado(sock): #Envia
    while True:
        try:
            linha = input()
        except EOFError:
            break
        try:
            sock.sendall((linha + '\n').encode('utf-8'))
        except OSError:
            break
        if linha.strip().lower() == ':sair':
            break

def thread_recebe(arquivo): #Recebe
    while True:
        linha = arquivo.readline()
        if not linha:
            print("[conexao encerrada pelo servidor]")
            break
        print(linha.rstrip('\n'))

def main(): #Execução
    host = sys.argv[1] if len(sys.argv) > 1 else HOST_PADRAO
    porta = int(sys.argv[2]) if len(sys.argv) > 2 else PORTA_PADRAO

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, porta))
    arquivo = sock.makefile('r', encoding='utf-8', newline='\n') #Entender pq do arquivo

    msg1 = arquivo.readline() #Aguarda ":CONECTADO!!"
    print(msg1.rstrip('\n')) #Imprime boas-vindas
    print("Comandos: :inicio N | :fim N | :qtd N | numeros separados por espaco para apostar | :sair para encerrar")

    #Cria e inicia as duas threads
    t1 = threading.Thread(target=thread_teclado, args=(sock,))
    t2 = threading.Thread(target=thread_recebe, args=(arquivo,))
    t1.start()
    t2.start()

    t1.join() #usuario digitou ":sair" ou fechou o terminal
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    t2.join()
    sock.close()
    print("Fim")

if __name__ == '__main__':
    main()