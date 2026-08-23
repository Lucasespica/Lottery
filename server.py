import socket
import threading
import random
from datetime import datetime

HOST = '0.0.0.0'
PORTA = 5000
INTERVALO_SORTEIO = 60


class SessaoLoteria:

    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.arquivo = conn.makefile('r', encoding='utf-8', newline='\n')

        #estado compartilhado entre as threads
        self.lock = threading.Lock()
        self.inicio = 0
        self.fim = 100
        self.qtd = 5
        self.apostas = [] #lista de apostas; cada aposta e uma lista de ints
        self.stop_event = threading.Event()

    #ciclo
    def iniciar(self):
        hora = datetime.now().strftime('%H:%M:%S')
        msg1 = f"{hora}: CONECTADO!!\n"
        try:
            self.conn.sendall(msg1.encode('utf-8'))
        except OSError:
            return

        t1 = threading.Thread(target=self.thread_recebe, daemon=True)
        t2 = threading.Thread(target=self.thread_sorteio, daemon=True)
        t1.start()
        t2.start()

        t1.join() # thread 1 termina quando o cliente desconecta ou ":sair"
        self.stop_event.set() # avisa a thread 2 para terminar também
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        t2.join()
        self.conn.close()
        print(f"[{self.addr}] desconectado. (todas as threads terminaram)")

    #T1 le comandos do cliente
    def thread_recebe(self):
        while True:
            try:
                linha = self.arquivo.readline()
            except OSError:
                break
            if not linha:
                break
            linha = linha.strip()
            if not linha:
                continue
            self._processa_linha(linha)
            if linha.lower() == ':sair':
                break

    def _processa_linha(self, linha):
        if linha.startswith(':'):
            self._processa_comando(linha[1:])
        else:
            self._processa_aposta(linha)

    def _processa_comando(self, texto):
        partes = texto.split()
        if not partes:
            return
        cmd = partes[0].lower()
        valor = partes[1] if len(partes) > 1 else None

        if cmd == 'inicio' and valor and valor.lstrip('-').isdigit():
            with self.lock:
                self.inicio = int(valor)
        elif cmd == 'fim' and valor and valor.lstrip('-').isdigit():
            with self.lock:
                self.fim = int(valor)
        elif cmd == 'qtd' and valor and valor.isdigit():
            with self.lock:
                self.qtd = int(valor)
        elif cmd == 'sair':
            pass
        else:
            print(f"[{self.addr}] comando desconhecido: :{texto}")

    def _processa_aposta(self, linha):
        try:
            numeros = [int(tok) for tok in linha.split()]
        except ValueError:
            print(f"[{self.addr}] entrada invalida ignorada: {linha}")
            return
        if not numeros:
            return
        with self.lock:
            self.apostas.append(numeros)

    #T2 sorteia e envia o resultado
    def thread_sorteio(self):
        while not self.stop_event.is_set():
            interrompido = self.stop_event.wait(INTERVALO_SORTEIO)
            if interrompido:
                break

            with self.lock:
                inicio, fim, qtd = self.inicio, self.fim, self.qtd
                apostas, self.apostas = self.apostas, []

            faixa = fim - inicio + 1
            if faixa <= 0:
                print(f"[{self.addr}] faixa invalida (fim < inicio), sorteio pulado")
                continue
            qtd = min(qtd, faixa)
            sorteio = sorted(random.sample(range(inicio, fim + 1), qtd))

            linhas = [f"SORTEIO: {sorteio}"]
            if apostas:
                for i, aposta in enumerate(apostas, start=1):
                    acertos = sorted(set(aposta) & set(sorteio))
                    linhas.append(
                        f"Aposta {i} {aposta} -> acertos: {acertos} ({len(acertos)})"
                    )
            else:
                linhas.append("Nenhuma aposta neste ciclo.")

            mensagem = "\n".join(linhas) + "\n"
            try:
                self.conn.sendall(mensagem.encode('utf-8'))
            except OSError:
                break


def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORTA))
    servidor.listen(5)
    print(f"Servidor de Loteria ouvindo em {HOST}:{PORTA}")

    try:
        while True:
            conn, addr = servidor.accept()
            print(f"[{addr}] conectado.")
            sessao = SessaoLoteria(conn, addr)
            threading.Thread(target=sessao.iniciar, daemon=True).start()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
    finally:
        servidor.close()


if __name__ == '__main__':
    main()