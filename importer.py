import csv
import sys

from rethinkdb import RethinkDB
import requests

r = RethinkDB()


def db_connect():
    config = open("login.txt").readlines()
    try:
        conn = r.connect(host="localhost", port=28015, db="SG", user=config[0].rstrip(), password=config[1].rstrip())
    except:
        print("Could not connect to database")
        sys.exit()
    return conn


conn = db_connect().repl()


with open("strikes.csv") as strikefile:
    reader = csv.reader(strikefile)
    for i in reader:
        print(i)
        print(r.table("strikes").insert({"user": i[0], "hr": i[1], "type": i[2], "reason": i[3], "evidence": i[4]}).run())


with open("signallers.csv") as signallerfile:
    reader = csv.reader(signallerfile)
    next(reader)
    for i in reader:
        id = requests.get("https://api.roblox.com/users/get-by-username?username=" + i[0]).json()["Id"]
        print(r.table("signallers").insert({"id": id, "user": i[0], "date": i[1], "notes": i[2], "updated": i[3]}).run())
