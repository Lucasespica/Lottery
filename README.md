# Loteria — Projeto Prático 1 (Redes de Computadores)

Aplicação cliente/servidor em Python que implementa uma loteria em que o cliente configura uma faixa de números e faz apostas, e o servidor realiza sorteios periódicos, informando os acertos de cada aposta.

- Comunicação em rede com a biblioteca `socket` (TCP);
- Concorrência com `threading` (múltiplas threads por conexão);

## Como funciona

Ao conectar, o cliente recebe do servidor uma mensagem de confirmação. A partir daí, cada lado passa a rodar duas threads:

| | Thread 1 | Thread 2 |
|---|---|---|
| **Cliente** | Lê o teclado e envia comandos/apostas ao servidor | Recebe dados do servidor e imprime na tela |
| **Servidor** | Lê o socket, processa comandos e registra apostas | A cada X segundos, sorteia números e envia o resultado |

A configuração da loteria e a lista de apostas são estado **compartilhado** entre as duas threads do servidor, protegido por um `threading.Lock` para evitar condição de corrida.

## Protocolo

**Servidor → Cliente**, assim que a conexão é aceita:
```
<HORARIO>: CONECTADO!!
```

**Cliente → Servidor**, a qualquer momento (uma linha = um comando ou uma aposta):

| Mensagem | Efeito |
|---|---|
| `:inicio N` | Define o início da faixa de números sorteáveis |
| `:fim N` | Define o fim da faixa de números sorteáveis |
| `:qtd N` | Define quantos números são sorteados por ciclo |
| `N1 N2 N3 ...` | Registra uma aposta com esses números |
| `:sair` | Encerra a conexão |

Se a loteria não for configurada, o padrão é faixa de `0` a `100`, sorteando `5` números.

**Servidor → Cliente**, ao final de cada ciclo de sorteio:
```
SORTEIO: [5, 6, 12, 18, 20]
Aposta 1 [3, 7, 9] -> acertos: [] (0)
Aposta 2 [1, 2, 3, 4, 5] -> acertos: [5] (1)
```

## Estrutura do projeto

```
.
├── servidor.py   # Aceita conexões, processa comandos/apostas e roda os sorteios
├── cliente.py    # Conecta ao servidor, envia comandos/apostas e exibe resultados
└── README.md
```

## Autores
- Guilherme Eid Godoy
- Lucas Espica Rezende
- Rafael Martiniano Nogueira Filho