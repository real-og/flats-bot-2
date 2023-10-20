import sys
import os
ROOT_PATH = str(os.environ.get("ROOT_PATH"))
sys.path.append(ROOT_PATH)

from src.shared import db
import csv

def write_users_csv():
    users = db.get_all_users()
    data_to_write = [] 
    for user in users:
        data_to_write.append([
            user['jointime'].strftime("%d.%m.%Y %H:%M:%S"),
            user['id_tg'],
            user['username'],
            user['isactive'],
            user['params']['town'],
            f"{user['params']['minCost']} - {user['params']['maxCost']}",
            user['params']['rooms'],
            user['params']['isSubwayNeed'],
            user['params']['isPointNeed'],
            user['params']['landlord'],
        ])

    with open('src/analytics/users.csv', mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(['date','id','username','isactive','town','cost','rooms','subway','point','landlord'])
        for row in data_to_write:
            writer.writerow(row)

