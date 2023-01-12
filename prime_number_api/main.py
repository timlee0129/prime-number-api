import json
import datetime
from typing import List, Union

from bson.json_util import dumps
from decouple import config

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pymongo import MongoClient

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
)

client = MongoClient(config('DB_URI'))

@app.on_event("startup")
async def startup() -> None:
    app.mongodb_client = client
    app.database = app.mongodb_client["numbers_db"]
    app.numbers = app.database["numbers"]

@app.on_event("shutdown")
def shutdown() -> None:
    app.mongodb_client.close()

def get_max_prime_entry() -> dict:
    cursor = app.numbers.find().sort('number',-1).limit(1)
    return cursor[0]

def get_min_prime_entry() -> dict:
    cursor = app.numbers.find().sort('number',1).limit(1)
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
async def check_prime(num: List[str] = Query(default=...)):
    try:
        num = [int(i) for i in num]
    except:
        raise HTTPException(400)
    max_prime_entry = get_max_prime_entry()
    max_prime_number = max_prime_entry['number']
    invalid_entries = [val for val in num if val < 2 or val > max_prime_number]
    if len(invalid_entries) > 0:
        raise HTTPException(status_code=400,detail=f"Invalid number entries: {invalid_entries}. Numbers must be >1 and <={max_prime_number} (current max prime)")
    query_dict = {val['number']: val for val in list(app.numbers.find({"number":{"$in":num}},{"_id": 0}))}
    for idx, val in enumerate(num):
        num[idx] = {val: query_dict.get(val)}
    return num

@app.get("/primeNumbers")
async def get_prime_numbers(
    q_order: Union[int, None] = Query(
        default = 0,
        alias="order",
    ),
    q_type: Union[str, None] = Query(
        default = "number",
        alias="type",
    ),
    q_min: Union[int, None] = Query(
        default = None,
        alias="min",
    ),
    q_max: Union[int, None] = Query(
        default = None,
        alias="max",
    ),
    q_len: Union[int, None] = Query(
        default = 1,
        alias="len",
    ),
):
    # verify that inputs are valid
    valid_order = [-1,0,1]
    valid_type = ["number", "order"]
    max_prime = get_max_prime_entry().get(q_type)
    min_prime = get_min_prime_entry().get(q_type)
    if q_max is None:
        q_max = max_prime
    if q_min is None:
        q_min = min_prime
    max_len = 1000
    if q_order not in valid_order:
        raise HTTPException(status_code=400,detail=f"Invalid 'order' input: {q_order}. 'order' must be one of these: {valid_order}")
    if q_type not in ["number", "order"]:
        raise HTTPException(status_code=400,detail=f"Invalid 'type' input: {q_type}. 'type' must be one of these: {valid_type}")
    if q_min < min_prime:
        raise HTTPException(status_code=400,detail=f"Invalid 'min' input: {q_min}. 'min' must be >={min_prime} for type '{q_type}'")
    if q_max > max_prime:
        raise HTTPException(status_code=400,detail=f"Invalid 'max' input: {q_max}. 'max' must be <={max_prime} for type '{q_type}'")
    if q_len > 1000:
        raise HTTPException(status_code=400,detail=f"Invalid 'len' input: {q_len}. 'len' must be <={max_len}")

    # if order is random
    if q_order == 0:
        return list(app.numbers.aggregate([
                {
                    "$match": {
                        q_type: {
                            "$gte": q_min,
                            "$lte": q_max,
                        }
                    }
                },
                {
                    "$sample": {
                        "size": q_len
                    }
                },
                {
                    "$project": {
                        "_id": 0
                    }
                }
            ])
        )
    else:
        return list(app.numbers.find(
                {
                    q_type: {
                        "$gte": q_min,
                        "$lte": q_max,
                    }
                },
                {
                    "_id": 0
                }
            ).sort(q_type,q_order).limit(q_len)
        )
