from typing import Optional, List, Union
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import requests
from pydantic import BaseModel
import numpy as np
import json

# Load the configuration
with open("./configs/urls.json", 'r+') as f:
    config = json.load(f)

# Get the review data
response = requests.get(config["DATA_URL"])
records = response.json()
df = pd.json_normalize(records)
df = df.rename({'gender of author': 'gender_of_author', 'gender of critic': 'gender_of_critic', 'same year': 'same_year'}, axis=1)

# Get the nearest neighbours index
index = np.memmap(config["KNN_INDEX_PATH"], dtype='int32', mode='r+', shape=(len(df), len(df)))
class Review(BaseModel):
    title: Union[str, None]
    author: Union[str, None]
    forum: Union[str, None]
    critic: Union[str, None]
    genre: Union[str, None]
    gender_of_author: Union[str, None]
    gender_of_critic: Union[str, None]
    year: Union[int, None]
    same_year: Union[str, None]
    tokens: Union[List[str], None]
    x: Union[float, None]
    y: Union[float,None]

    class Config:
        orm_mode = True

class Position(BaseModel):
    x: Union[float, None]
    y: Union[float, None]

middleware = [Middleware(CORSMiddleware, 
                        allow_origins=['*'], 
                        allow_credentials=True, 
                        allow_methods=['*'], 
                        allow_headers=['*'])]

app = FastAPI(middleware=middleware)

@app.get("/api/reviews/", response_model=List[Review])
async def get_reviews():
    
    return list(df.to_dict('records'))
    
@app.get("/api/reviews/{review_id}", response_model=Review)
async def get_review(review_id: int):
    return df.iloc[review_id]

@app.get("/api/reviews/nearest/", response_model=List[Review])
async def get_nearest_neighbors(review_id: int, nn: int = 10):
    review_idxs = index[review_id, :nn]

    return list(df.iloc[review_idxs].to_dict('records'))

@app.get("/api/reviews/{review_id}/position/", response_model=Position)
async def get_position_of_review(review_id: int):

    return {
        "x": df.iloc[review_id].x,
        "y": df.iloc[review_id].y
    }

@app.get("/api/positions/", response_model=List[Position])
async def get_positions_of_reviews(title: str):

    if title:
        results = df[df.title == title][['x', 'y']]

    return list(results.to_dict('records'))