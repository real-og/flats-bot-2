import sys
sys.path.append('/Users/friend/Desktop/flats-bot-2')

import threading
import logging
from kufar_parser import poll_kufar
from onliner_parser import poll_onliner
import sys

logging.basicConfig(level=logging.WARNING, filename="src/service/errors.log", filemode='w',
                    format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    thread1 = threading.Thread(target=poll_kufar)
    thread2 = threading.Thread(target=poll_onliner)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
