
from drone_callback.config import config


import bottle
import drone_callback


if __name__ == '__main__':
    drone_callback.run(host=config.HOST, port=config.PORT)


app = bottle.default_app()
