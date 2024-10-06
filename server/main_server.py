import argparse
import uvicorn
from fastapi import FastAPI, Request, HTTPException
import uuid
from datetime import datetime
import os
import csv
import pandas as pd
import sys

sys.path.append("./")
from utils.log_func import init_logger

app = FastAPI()


@app.post("/post_message")
async def store_message(request: Request):
    json_data = await request.json()
    request_id = str(uuid.uuid4())

    logger.info(f"[{request_id}] - POST request: {json_data['message']}")

    log_entry = [request_id, datetime.now().isoformat(), json_data["message"]]
    with open(data_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(log_entry)

    return {"message": "Data received"}


@app.get("/get_messages")
async def reurn_messages():
    if os.path.isfile(data_file):
        messages_df = pd.read_csv(data_file)
        return {"messages": messages_df["Message"].to_list()}
    else:
        raise HTTPException(status_code=404, detail="Data file not found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Server for storing and retrieving messages."
    )
    parser.add_argument("server_name", type=str, help="Name used for logging.")
    parser.add_argument("port", type=int, help="Which port to use")
    args = parser.parse_args()

    data_file = os.path.join(
        "data", f"{args.server_name}_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.csv"
    )
    file_exists = os.path.isfile(data_file)
    if not file_exists:
        with open(data_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Request_ID", "Timestamp", "Message"])

    logger = init_logger(args.server_name, "loggs")

    uvicorn.run(app, host="0.0.0.0", port=args.port)
