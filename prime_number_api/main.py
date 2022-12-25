import json
import datetime
from typing import List, Union

from bson.json_util import dumps
from decouple import config

from fastapi import FastAPI, Query, HTTPException
from pymongo import MongoClient

app = FastAPI()

client = MongoClient(config('DB_URI'))

@app.on_event("startup")
async def startup() -> None:
    app.mongodb_client = client
    app.database = app.mongodb_client["numbers_db"]
    app.numbers = app.database["numbers"]

@app.on_event("shutdown")
async def shutdown() -> None:
    await app.mongodb_client.close()

def get_max_prime_entry() -> dict:
    cursor = app.numbers.find().sort('number',-1).limit(1)
    return cursor[0]


@app.get("/")
async def get_about() -> dict:
    max_prime_entry = get_max_prime_entry()
    return {
        "about": "Prime Number API: a self-updating API where you can get basic information about number's prime-ness.",
        "last_updated": max_prime_entry['_id'].generation_time.strftime('%Y-%m-%d'),
        "max_prime_number": max_prime_entry['number'],
        "max_prime_order": max_prime_entry['order']
    }

@app.get("/checkIfPrime")
async def check_prime(num: List[str] = Query(default=None)):
    try:
        num = [int(i) for i in num]
    except:
        raise HTTPException(400)
    max_prime_entry = get_max_prime_entry()
    max_prime_number = max_prime_entry['number']
    for idx, val in enumerate(num):
        assert val > 1 and val <= max_prime_number, "Invalid number entry. Number must be >1 and <= current max prime"
        cursor = app.numbers.find_one({"number":{"$eq":val}},{"_id": 0})
        num[idx] = {val: json.loads(dumps(cursor))}
    return num
