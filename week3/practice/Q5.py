import json
with open("jeg.json","r") as file:
    data=json.load(file)
print(f"Data from json file : {data}\n")
for i in data :
        print(f"Name: {i['name']},Age: {i['age']},Course: {i['course']}")