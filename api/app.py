import time
import random
import requests
import json

from redis import Sentinel, Redis
from redis.sentinel import MasterNotFoundError
from flask import Flask, request, render_template
from datetime import datetime

# Configurações intancias disponiveis dos sentinelas
SENTINELS = ["sentinel", "sentinel2", "sentinel3"]
SENTINEL_PORT = 26379
SENTINEL_MASTER_GROUP = "master"

# Configurações dos Redis-Serves
SERVER_PORT  = 6379

# App flask
app = Flask(__name__)

# Instancias do redis com e sem persistencia
mem_cache = Redis(host="redis_mem", port=SERVER_PORT)
persistence_cache = Redis(host="master", port=SERVER_PORT)


def get_hit_count() -> int:
    """
    Método que incrementa uma key chamada hits, que salva quantas vezes a rota '/home' da api foi acessada.
    """
    return persistence_cache.incr('hits')


def get_github_user(username: str) -> bytes:
    """
    Método que retorna os dados do usuário do github dado um username. Os dados são buscados na API do Github.
    :param: username
        Nome do usuário do github a ser buscado

    :return: Dict com o timestam em que o registro foi localizado e os dados resgatados da API do github
    """
    # Faz a requisicao para a API do github
    response_api = requests.get(f'https://api.github.com/users/{username}')
    # Tempo para simular uma chamada mais demorada
    time.sleep(random.randint(3, 6))
    # Decodifica a resposta da API
    api_response_content = json.loads(response_api.content.decode('utf-8'))

    # Cria objeto de resposta, salvando a data da ultima vez que o registro foi atualizado
    user_dict = {"updated_at": datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), "user_data": api_response_content}

    return json.dumps(user_dict, indent=2).encode('utf-8')


@app.route('/', methods=['GET'])
def home():
    count = get_hit_count()
    return render_template('index.html', count=count)


@app.route('/mem/github_user', methods=['GET'])
def mem_github_user():
    """
    Rota que resgata os dados de um usuário do github dado seu username. Essa rota utiliza o cache do redis sem persistência.
    :param: username
        Nome de usuário a ser buscado
    :param: expire
        Tempo sem segundos para expiração do cache
    """
    username = request.args.get('username')
    expire_seconds = request.args.get('expire', type=int, default=None)
    if mem_cache.get(username) is None:
        user_data = get_github_user(username)
        mem_cache.set(name=username, value=user_data, ex=expire_seconds)

    data = json.loads(mem_cache.get(username))

    return render_template('github_page.html', data=data)


@app.route('/github_user', methods=['GET'])
def github_user():
    """
    Rota que resgata os dados de um usuário do github dado seu username. Essa rota utiliza o cache do redis com persistência.
    :param: username
        Nome de usuário a ser buscado
    :param: expire
        Tempo sem segundos para expiração do cache
    """
    username = request.args.get('username')
    expire_seconds = request.args.get('expire', type=int, default=None)
    if persistence_cache.get(username) is None:
        user_data = get_github_user(username)
        persistence_cache.set(name=username, value=user_data, ex=expire_seconds)

    data = json.loads(persistence_cache.get(username))

    return render_template('github_page.html', data=data)


@app.route('/clear_cache', methods=['GET', 'POST'])
def clear_cache():
    """
    Rota que limpa o cache, apagando todos os dados nos servidores do redis.
    """

    persistence_cache.flushall()
    mem_cache.flushall()

    return "Cache has been clear."


@app.route('/get_data', methods=['GET', 'POST'])
def get_data():

    search_key = request.args.get('key')

    for sentinel_name in SENTINELS:
        try:
            sentinel = Sentinel([(sentinel_name, SENTINEL_PORT)], socket_timeout=0.1)
            master = sentinel.master_for(SENTINEL_MASTER_GROUP, socket_timeout=0.1)
            data = master.get(search_key)
        except MasterNotFoundError:
            pass
        else:
            return render_template('get_data.html', key=search_key, value=data)

    return render_template('error.html')


@app.route('/set_data', methods=['GET', 'POST'])
def set_data():

    key = request.args.get('key')
    value = request.args.get('value')

    for sentinel_name in SENTINELS:
        try:
            sentinel = Sentinel([(sentinel_name, SENTINEL_PORT)], socket_timeout=0.1)
            master = sentinel.master_for(SENTINEL_MASTER_GROUP, socket_timeout=0.1)
            master.set(key, value)
        except MasterNotFoundError:
            pass
        else:
            return render_template('set_data.html', key=key, value=value)

    return render_template('error.html')


if __name__ == "__main__":
    app.run(debug=True)
