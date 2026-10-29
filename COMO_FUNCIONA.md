# 🎮🎵 Como o Streamify funciona (explicado do zero)

Fala! Esse arquivo é pra você entender **tudo** que tem nesse projeto: o que é cada pasta,
o que cada pedaço de código faz e por que as coisas foram feitas desse jeito.
Não precisa saber muito de programação, a ideia é ir passo a passo.

---

## 1. A ideia geral

O Streamify é um **mini Spotify de trilhas sonoras de games**. Só que, em vez de ser um
programa gigante que faz tudo, ele foi dividido em **3 programinhas separados**, cada um
com uma função. Isso se chama **arquitetura de microsserviços**.

Pensa numa lanchonete:

- Um funcionário só anota os pedidos (🎵 **music_service**: sabe quais músicas existem)
- Outro só monta os lanches (📋 **playlist_service**: cuida das playlists)
- Outro só entrega (▶️ **playback_service**: controla o play/pause)

Se o da entrega ficar doente, os outros continuam trabalhando. Com software é igual:
se um serviço cair, os outros seguem de pé, e dá pra mexer em um sem quebrar os outros.

---

## 2. Mapa das pastas

```
Streamify/
├── .github/workflows/deploy.yml   → robô que testa (e, se você mandar, publica) o projeto
├── music_service/                 → serviço 1: catálogo de músicas (porta 5001)
├── playlist_service/              → serviço 2: playlists (porta 5002)
├── playback_service/              → serviço 3: tocar/pausar (porta 5003)
├── terraform/                     → "receita" pra criar um servidor na nuvem (AWS)
├── docker-compose.yml             → liga os 3 serviços de uma vez no seu PC
├── requirements-dev.txt           → ferramentas só pra desenvolvimento (o pytest)
├── .gitignore                     → lista de arquivos que o Git deve ignorar
└── README.md                      → resumo rápido do projeto
```

Dentro de **cada** serviço tem sempre os mesmos arquivos:

| Arquivo             | Pra que serve |
|---------------------|---------------|
| `app.py`            | O código do serviço em si |
| `requirements.txt`  | Lista das bibliotecas Python que ele precisa (aqui, só o Flask) |
| `Dockerfile`        | Receita pra empacotar o serviço numa "caixinha" (container) |
| `.dockerignore`     | O que **não** colocar dentro da caixinha (testes, lixo do Python) |
| `tests/test_app.py` | Testes automáticos que conferem se o serviço funciona |

---

## 3. Conceitos que você precisa saber antes

### 🌐 API e HTTP
Os serviços não têm tela. Eles são **APIs**: programas que recebem pedidos pela internet e
respondem com dados. Esses pedidos usam o protocolo **HTTP**, o mesmo que o seu navegador usa.

Cada pedido tem um **método** (o que você quer fazer) e uma **rota** (o endereço):

| Método   | Significa       | Exemplo |
|----------|-----------------|---------|
| `GET`    | "me mostra"     | `GET /music` → lista as músicas |
| `POST`   | "cria/faz isso" | `POST /playlists` → cria uma playlist |
| `DELETE` | "apaga"         | `DELETE /playlists/1/tracks/3` → tira a música 3 da playlist 1 |

### 📦 JSON
É o formato em que os dados vão e voltam. Parece um dicionário do Python:

```json
{"id": 1, "title": "Cyberpunk Night", "game": "Cyberpunk 2077"}
```

### 🔢 Códigos de status
Toda resposta vem com um número que diz como foi:

| Código | Quer dizer |
|--------|------------|
| `200`  | Deu certo ✅ |
| `201`  | Deu certo e algo novo foi criado ✅ |
| `400`  | Você mandou o pedido errado (faltou informação) ❌ |
| `404`  | Não achei o que você pediu ❌ |
| `409`  | Não dá pra fazer isso agora (ex: pausar algo que não está tocando) ❌ |

### 🚪 Porta
Um computador pode rodar vários serviços ao mesmo tempo. A **porta** é tipo o número do
apartamento: `localhost:5001` é o music, `5002` é o playlist e `5003` é o playback.

### 🧪 Flask
É a biblioteca Python que transforma funções normais em rotas de API. Você escreve
`@app.route('/music')` em cima de uma função e pronto: quando alguém acessar `/music`,
essa função roda.

---

## 4. Os serviços, linha por linha

### 🎵 Serviço 1: `music_service/app.py` (o catálogo)

```python
from flask import Flask, jsonify
app = Flask(__name__)
```
Importa o Flask e cria o "app", que é o servidor. O `jsonify` transforma dados do Python em JSON.

```python
TRACKS = [
    {"id": 1, "title": "Cyberpunk Night", "game": "Cyberpunk 2077", ...},
    ...
]
```
É o nosso **"banco de dados de mentira"**: só uma lista na memória. Num projeto real isso
ficaria num banco de dados de verdade (tipo PostgreSQL). Aqui é simples de propósito.
⚠️ Como fica na memória, **tudo some quando o serviço reinicia**.

```python
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "music_service"}), 200
```
Rota de **"tá vivo?"**. Não faz nada útil pro usuário, mas serve pra ferramentas checarem se
o serviço está funcionando. Os 3 serviços têm essa rota.

```python
@app.route('/music/<int:track_id>', methods=['GET'])
def get_music_by_id(track_id):
    track = next((t for t in TRACKS if t["id"] == track_id), None)
```
O `<int:track_id>` pega o número da URL. Se você acessar `/music/2`, `track_id` vira `2`.
O `next(...)` percorre a lista e devolve a primeira música com aquele id, ou `None` se
não achar nenhuma. Aí o código responde `200` com a música ou `404` com erro.

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
```
"Se esse arquivo foi executado diretamente, liga o servidor na porta 5001."
O `0.0.0.0` significa "aceita conexão de qualquer lugar", o que é necessário dentro do Docker.

---

### 📋 Serviço 2: `playlist_service/app.py` (as playlists)

Começa com uma playlist de exemplo:
```python
PLAYLISTS = [{"id": 1, "name": "Boss Fights", "track_ids": [3]}]
```
Repara que a playlist guarda só os **ids** das músicas (`[3]`), e não a música inteira.
Quem sabe os detalhes da música é o music_service. Cada serviço cuida só do que é dele.

Tem duas **funções ajudantes** pra não repetir código:
- `find_playlist(id)` → procura a playlist pelo id
- `not_found()` → monta a resposta de erro 404

As rotas:

| Rota | O que faz |
|------|-----------|
| `GET /playlists` | Lista todas |
| `GET /playlists/<id>` | Mostra uma |
| `POST /playlists` | Cria uma nova. Precisa mandar `{"name": "..."}` |
| `POST /playlists/<id>/tracks` | Adiciona uma música. Manda `{"track_id": 2}` |
| `DELETE /playlists/<id>/tracks/<track_id>` | Remove uma música |

Um pedaço importante, que é a **validação**:
```python
data = request.get_json(silent=True) or {}
name = data.get("name")
if not name:
    return jsonify({...}), 400
```
- `request.get_json(silent=True)` lê o JSON que o usuário mandou. O `silent=True` faz
  ele não explodir se vier algo inválido, e o `or {}` garante que vira um dicionário vazio.
- Se não tiver `name`, responde `400`. **Nunca confie no que o usuário manda**: sempre confere.

Pra criar o id novo:
```python
new_id = max((p["id"] for p in PLAYLISTS), default=0) + 1
```
Pega o maior id que existe e soma 1. O `default=0` cobre o caso da lista estar vazia.

---

### ▶️ Serviço 3: `playback_service/app.py` (o player)

Guarda o estado atual do player:
```python
STATE = {"track_id": None, "status": "stopped"}
```

Funciona como uma **máquina de estados**, ou seja, o player só pode estar em um
destes estados, e só pode mudar de um pro outro por certos caminhos:

```
            play                pause
 stopped ─────────► playing ─────────► paused
    ▲                 ▲                  │
    │                 └──── resume ──────┘
    └──────────── stop (de qualquer estado)
```

Por isso, se você tentar `pause` com nada tocando, ele responde `409` (conflito):
```python
if STATE["status"] != "playing":
    return jsonify({"status": "error", "message": "Nenhuma música tocando"}), 409
```

| Rota | O que faz |
|------|-----------|
| `GET /playback/status` | Mostra o que está tocando |
| `POST /playback/play` | Toca uma música. Manda `{"track_id": 1}` |
| `POST /playback/pause` | Pausa |
| `POST /playback/resume` | Continua de onde parou |
| `POST /playback/stop` | Para tudo |

> 💡 Obs: ele não toca áudio de verdade, só **simula** o controle. Tocar áudio seria o próximo nível.

---

## 5. Testes automáticos (`tests/test_app.py`)

Testes são **códigos que testam o seu código**. Em vez de você abrir o navegador e conferir
na mão toda vez, o computador faz isso em segundos. Usamos o **pytest**.

```python
@pytest.fixture
def client():
    return app.test_client()
```
Uma **fixture** é uma preparação que roda antes de cada teste. Aqui ela cria um
"cliente de mentira" que faz pedidos pro serviço **sem precisar ligar o servidor de verdade**.

```python
def test_music_not_found(client):
    assert client.get('/music/999').status_code == 404
```
O `assert` quer dizer "eu garanto que isso é verdade". Se não for, o teste falha e avisa você.
Toda função que começa com `test_` é encontrada e executada automaticamente pelo pytest.

No playlist e no playback a fixture também **reseta os dados** depois de cada teste.
Isso porque um teste cria uma playlist, e sem resetar o próximo teste ia encontrar
essa playlist a mais e dar errado. **Cada teste tem que começar do zero.**

Pra rodar (dentro da pasta de um serviço):
```bash
pip install -r requirements.txt -r ../requirements-dev.txt
python -m pytest -v
```

---

## 6. Docker: as "caixinhas"

Problema clássico: *"no meu PC funciona!"* 😅. O **Docker** resolve isso empacotando o
programa junto com **tudo** que ele precisa (Python, bibliotecas...) numa caixinha
chamada **container**, que roda igual em qualquer computador.

### O `Dockerfile` (a receita da caixinha)
```dockerfile
FROM python:3.10-slim          # começa de uma imagem que já tem Python 3.10
WORKDIR /app                   # entra na pasta /app dentro da caixinha
COPY requirements.txt .        # copia a lista de bibliotecas
RUN pip install --no-cache-dir -r requirements.txt   # instala elas
COPY . .                       # copia o resto do código
EXPOSE 5001                    # avisa que usa a porta 5001
CMD ["python", "app.py"]       # comando que roda quando a caixinha liga
```
💡 Por que copiar o `requirements.txt` **antes** do resto? Porque o Docker guarda cada etapa
em cache. Se você só mudar o `app.py`, ele não precisa reinstalar as bibliotecas e o build fica muito mais rápido.

### O `docker-compose.yml` (o maestro)
Em vez de ligar os 3 containers um por um, o compose liga todos com um comando:
```bash
docker compose up --build
```
`"5001:5001"` quer dizer "porta 5001 do seu PC → porta 5001 da caixinha".
Depois é só abrir `http://localhost:5001/music` no navegador. 🎉

---

## 7. Terraform: criando servidor na nuvem com código

Em vez de entrar no site da AWS e clicar em mil botões pra criar um servidor, você
**escreve** o que quer num arquivo e o Terraform cria pra você. Isso se chama
**Infraestrutura como Código (IaC)**. A vantagem é que fica salvo, versionado no Git
e dá pra repetir igualzinho quantas vezes quiser.

### `terraform/main.tf`: o que ele cria
Pensa como montar uma casa:

| Recurso | Na analogia da casa |
|---------|---------------------|
| `aws_vpc` | O **terreno** cercado. É a sua rede privada na AWS |
| `aws_subnet` | Um **cômodo** dentro do terreno |
| `aws_internet_gateway` | O **portão** pra rua (internet) |
| `aws_route_table` + `association` | A **placa** dizendo "pra sair, use o portão" |
| `aws_security_group` | O **porteiro**: decide quem pode entrar e em qual porta |
| `aws_instance` | A **casa** em si, ou seja, o computador (EC2) que roda os serviços |

- `data "aws_ami" "ubuntu"` busca automaticamente a versão mais nova do Ubuntu 22.04
  (no guia original o id estava fixo, e esses ids mudam com o tempo).
- O `user_data` é um script que roda **na primeira vez que o servidor liga**: ele instala o Docker.
- O porteiro (security group) libera as portas 5001 a 5003 pra todo mundo, mas o
  **SSH (porta 22) só pro IP que você configurar**. Deixar SSH aberto pro mundo inteiro é
  pedir pra ser atacado por robôs.

### `terraform/variables.tf`: as configurações
São os "campos editáveis": região, tipo da máquina, nome da chave SSH e qual IP pode
acessar o SSH. Assim dá pra mudar sem mexer no código principal.

### `terraform/outputs.tf`: o que ele mostra no final
Depois de criar tudo, ele imprime o IP do servidor e as URLs dos serviços.

### ⚠️ O tal do "estado"
O Terraform anota num arquivo (`terraform.tfstate`) tudo o que ele já criou. Se esse arquivo
se perder, ele "esquece" e cria **tudo de novo** (e a AWS cobra em dobro 💸).
No GitHub Actions cada execução começa numa máquina limpa, então o arquivo se perde sempre.
Por isso tem um bloco `backend "s3"` comentado: ele guarda o estado num bucket da AWS.
**Tem que configurar isso antes de usar o deploy de verdade.**

---

## 8. GitHub Actions: o robô (`.github/workflows/deploy.yml`)

É um robô do GitHub que roda sozinho quando algo acontece no repositório. Isso se chama
**CI/CD**:
- **CI (Integração Contínua)**: toda vez que alguém manda código, roda os testes automaticamente.
- **CD (Entrega Contínua)**: se os testes passarem, publica o projeto.

### Quando ele roda
```yaml
on:
  push:              # quando alguém dá push na main
  pull_request:      # quando alguém abre um PR pra main
  workflow_dispatch: # quando você clica "Run workflow" na aba Actions
```

### Job 1: `test`
```yaml
strategy:
  matrix:
    service: [ music_service, playlist_service, playback_service ]
```
A **matrix** faz o robô rodar o mesmo job 3 vezes, uma pra cada serviço, em paralelo.
Em cada uma ele: baixa o código → instala o Python → instala as bibliotecas → roda os testes.

### Job 2: `deploy-infra`
```yaml
needs: test
if: github.event_name == 'workflow_dispatch'
```
- `needs: test` → só roda se os testes passarem.
- `if: ...` → só roda se alguém disparar **manualmente**. Assim um push qualquer não cria
  servidor na AWS sem querer.

Ele usa `secrets.AWS_ACCESS_KEY_ID`, que são **senhas guardadas no GitHub** (em Settings →
Secrets). Nunca, jamais, coloque senha direto no código! 🔐

---

## 9. O que foi corrigido em relação ao guia original

| Problema no guia | O que foi feito |
|------------------|-----------------|
| Só o serviço de músicas tinha código | Criados o playlist e o playback no mesmo estilo |
| Faltavam os `requirements.txt` e os testes | Criados pros 3 serviços (14 testes, todos passando) |
| `python-python: '3.10'` no workflow (erro de digitação) | Corrigido pra `python-version` |
| `pytest` rodava sem nenhum teste e falhava | Agora roda os testes de cada serviço |
| Deploy na AWS a cada push | Agora só manual |
| Subnet sem acesso à internet (o Docker nem instalava) | Adicionados internet gateway e rota |
| SSH aberto pro mundo todo | Restrito a um IP configurável |
| ID fixo da imagem do Ubuntu | Busca automática da versão mais nova |
| Faltava o `outputs.tf` | Criado |
| `version` e `FLASK_ENV` obsoletos no compose | Removidos |

---

## 10. Testando na mão 🕹️

Com tudo rodando (`docker compose up --build`), abre outro terminal e brinca com o `curl`:

```bash
# Ver todas as músicas
curl http://localhost:5001/music

# Criar uma playlist
curl -X POST http://localhost:5002/playlists -H "Content-Type: application/json" -d '{"name": "Chill"}'

# Colocar a música 1 na playlist 2
curl -X POST http://localhost:5002/playlists/2/tracks -H "Content-Type: application/json" -d '{"track_id": 1}'

# Dar play na música 1
curl -X POST http://localhost:5003/playback/play -H "Content-Type: application/json" -d '{"track_id": 1}'

# Ver o que está tocando
curl http://localhost:5003/playback/status
```

---

## 11. Ideias pra evoluir o projeto 🚀

1. **Banco de dados de verdade** (SQLite ou PostgreSQL) pra nada sumir quando reiniciar.
2. **Serviços conversando entre si**: o playlist perguntar pro music se a música existe antes de adicionar.
3. **Tocar áudio de verdade** com arquivos `.mp3` na rota `/stream/<id>`.
4. **Login de usuário**, pra cada um ter suas próprias playlists.
5. **Um front-end** (HTML/React) pra ter uma tela bonita em vez de usar `curl`.

Bons estudos! Qualquer dúvida, lê o código com calma: ele foi escrito pra ser simples. 💪
