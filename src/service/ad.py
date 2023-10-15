import datetime
import csv

class Ad:
    def __init__(self,
                town: str,
                cost: int,
                link: str,
                source: str):
        self.town = town
        self.cost = cost
        self.link = link
        self.source = source


    def save(self):
        data_to_write = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         self.source,
                         self.town,
                         self.cost,
                         self.link,
                         ]
        with open('service/ads.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data_to_write)


    def broadcast(self):
        print(f'разослал {self}')
