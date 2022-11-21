import redis
import json
import random
import time

r = redis.Redis(host='redis_mem', port=6379, db=0)


def produce():
    while True:
        # Opening JSON file
        f = open('trocadilhos.json')

        # returns JSON object as a dictionary
        data = json.load(f)["trocadilhos"]

        option = random.randint(0, len(data)-1)

        r.publish('trocadilhos', json.dumps(data[option], indent=2).encode('utf-8'))

        print("Message has been send.")

        time.sleep(10)


if __name__ == "__main__":
    produce()
