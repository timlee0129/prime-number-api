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
async def startup():
    app.mongodb_client = client
    app.database = app.mongodb_client["numbers_db"]
    app.numbers = app.database["numbers"]

@app.on_event("shutdown")
async def shutdown():
    await app.mongodb_client.close()

@app.get("/")
async def get_about() -> dict:
    cursor = app.numbers.find().sort('number',-1).limit(1)
    largest_num_entry = cursor[0]
    return {
        "about": "Prime Number API: a self-updating API where you can get basic information about number's prime-ness.",
        "last_updated": largest_num_entry['_id'].generation_time.strftime('%Y-%m-%d'),
        "max_prime_number": largest_num_entry['number'],
        "max_prime_order": largest_num_entry['order']
    }

@app.get("/checkIfPrime")
async def check_prime(num: List[str] = Query(default=None)):
    try:
        num = [int(i) for i in num]
    except:
        raise HTTPException(400)
    for idx, val in enumerate(num):
        cursor = app.numbers.find_one({"number":{"$eq":val}},{"_id": 0})
        num[idx] = json.loads(dumps(cursor))
    return num
