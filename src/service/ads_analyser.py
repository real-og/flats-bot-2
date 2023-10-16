import csv
from pprint import pprint


csv_file_path = 'src/service/ads.csv'
urls = []

with open(csv_file_path, 'r', newline='') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        urls.append(row[8])
        
input_array = urls
element_count = {}


for element in input_array:
    if element in element_count:
        element_count[element] += 1
    else:
        element_count[element] = 1

# Создаем массив с количеством включений для каждого элемента
result_array = [element_count[element] for element in input_array]



pprint(result_array)
