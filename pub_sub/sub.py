import redis
import json
import time

r = redis.Redis(host='redis_mem', port=6379, db=0)
client = r.pubsub()
# subscribe to trocadilhos channel
client.subscribe('trocadilhos')


def consume():
    while True:

        # Opening JSON file
        message = client.get_message()

        if not message or type(message['data']) == int:
            print("Not messages yet...")
            time.sleep(2)
            continue

        # Decodifica mensagem
        decoded_message = json.loads(message['data'].decode('utf-8'))

        print("< Trocadilho >")
        print(decoded_message["pergunta"])
        print("\n")
        print(f"R: {decoded_message['resposta']}\n")


if __name__ == "__main__":
    consume()
