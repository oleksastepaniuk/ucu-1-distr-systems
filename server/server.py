import argparse
import aiohttp
import uvicorn
from fastapi import FastAPI, Request, HTTPException
import uuid
from datetime import datetime
import os
import csv
import json
import pandas as pd
import sys

sys.path.append("./")
from utils.log_func import init_logger

app = FastAPI()


async def backup_message(
    message: str,
    session: aiohttp.ClientSession,
    url: str = "http://127.0.0.1:8010/post_message",
) -> None:
    try:
        async with session.post(url, json={"message": message}) as response:
            if response.status == 200:
                return True
            else:
                print(
                    f"Failed to post message: {message}. Response status {response.status}"
                )
                return False
    except aiohttp.ClientError as e:
        print(f"Failed to connect. Message {message}, error - {e}")
        return False


@app.post("/post_message")
async def store_message(request: Request):
    json_data = await request.json()
    request_id = str(uuid.uuid4())

    logger.info(f"[{request_id}] - POST request: {json_data['message']}")

    log_entry = [request_id, datetime.now().isoformat(), json_data["message"]]
    with open(data_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(log_entry)

    if args.server_type == "main":
        for backup_name, port in backup_server_dict.items():
            print(f"Sending message to: http://127.0.0.1:{port}/post_message")

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
    parser.add_argument("server_type", type=str, help="Choose 'main' or 'backup'.")
    parser.add_argument("server_name", type=str, help="Name used for logging.")
    parser.add_argument("port", type=int, help="Which port to use")
    args = parser.parse_args()

    if args.server_type not in ["main", "backup"]:
        raise ValueError(
            f"Server type should be 'main' or 'backup'. Received: {args.server_type}"
        )

    data_file = os.path.join(
        "data", f"{args.server_name}_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.csv"
    )
    file_exists = os.path.isfile(data_file)
    if not file_exists:
        with open(data_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Request_ID", "Timestamp", "Message"])

    logger = init_logger(args.server_name, "loggs")

    if args.server_type == "main":
        with open("./server/backup_servers.json", "r") as f:
            backup_server_dict = json.load(f)
        print(f"Starting main server '{args.server_name}' at port {args.port}")
        print(
            f"{len(backup_server_dict)} backup servers will be used. Ports: {list(backup_server_dict.values())}\n"
        )

    uvicorn.run(app, host="0.0.0.0", port=args.port)
