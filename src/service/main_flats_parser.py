import sys
import os
ROOT_PATH = str(os.environ.get("ROOT_PATH"))
sys.path.append(ROOT_PATH)

import threading
import logging
from kufar_parser import poll_kufar
from onliner_parser import poll_onliner


logging.basicConfig(level=logging.WARNING, filename="src/service/errors.log", filemode='w',
                    format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    thread1 = threading.Thread(target=poll_kufar)
    thread2 = threading.Thread(target=poll_onliner)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
