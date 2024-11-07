import argparse
import aiohttp
import asyncio
import uvicorn
from fastapi import FastAPI, Request, HTTPException

from typing import Tuple, Dict, List
import os
import sys

import csv
import json
import pandas as pd

from datetime import datetime
from time import time
import random
import uuid

sys.path.append("./")
from utils.log_func import init_logger

app = FastAPI()


async def backup_message(
    message: str,
    url: str = "http://127.0.0.1:8010/post_message",
    backup_name: str = "backup_server_1",
    port: int = 8011,
    request_id: str = "default_id",
) -> Tuple[bool, float, str, int, str]:
    try:
        start_time = time()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json={"message": message, "request_id": request_id}
            ) as response:
                elapsed_time = time() - start_time
                if response.status == 200:
                    return True, elapsed_time, backup_name, port, request_id
                else:
                    return False, elapsed_time, backup_name, port, request_id
    except Exception as e:
        elapsed_time = time() - start_time
        logger.error(
            f"{request_id}] - Exception during backup to {backup_name}:{port}. Error: {e}."
        )
        return False, elapsed_time, backup_name, port, request_id


def on_task_done(task: asyncio.Task) -> None:
    success, elapsed_time, backup_name, port, request_id = task.result()
    if success:
        logger.info(
            f"[{request_id}] - Backed up message to {backup_name}:{port}. Time taken: {elapsed_time:.2f} sec"
        )
    else:
        logger.error(
            f"[{request_id}] - Failed to back up message to {backup_name}:{port}. Time taken: {elapsed_time:.2f} sec"
        )


def validate_write_concern(write_concern: int, backups_available: int) -> None:
    if write_concern < 1:
        raise HTTPException(status_code=400, detail="write_concern must be at least 1.")
    if write_concern - 1 > backups_available:
        raise HTTPException(
            status_code=400,
            detail=f"Too many backups required. Requested {write_concern}, available: {backups_available + 1}",
        )


def prevent_request_duplicates(request_id: str):
    global processed_requests_ids

    if request_id in processed_requests_ids:
        return True

    processed_requests_ids.add(request_id)
    return False


@app.post("/post_message")
async def store_message(request: Request) -> Dict[str, str]:
    json_data = await request.json()
    request_id = json_data.get("request_id", str(uuid.uuid4()))
    message = json_data["message"]
    write_concern = int(json_data.get("write_concern", 1))

    log_message = (
        f"[{request_id}] - POST request: {message}; Write concern: {write_concern}"
    )
    logger.info(log_message)

    if prevent_request_duplicates(request_id):
        logger.info(f"[{request_id}] - Duplicate request received. Ignoring.")
        return {"message": "Duplicate message ignored."}
    else:
        data_entry = [request_id, datetime.now().isoformat(), message]
        with open(data_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(data_entry)

    if args.server_type == "main":
        validate_write_concern(write_concern, len(backup_server_dict))

        num_successes_needed = write_concern - 1
        num_successes = 0
        backup_tasks = []

        for backup_name, port in backup_server_dict.items():
            url = f"http://{backup_name}:{port}/post_message"
            print(f"Sending message to: {url}")
            task = asyncio.create_task(
                backup_message(message, url, backup_name, port, request_id)
            )
            backup_tasks.append(task)
            task.add_done_callback(on_task_done)

        if write_concern == 1:
            logger.info(f"[{request_id}] - Write concern fulfilled. Returning 200")
            return {"message": "Data received"}

        # process tasks as they complete
        for task in asyncio.as_completed(backup_tasks):
            success, _, _, _, _ = await task
            if success:
                num_successes += 1
            if num_successes >= num_successes_needed:
                logger.info(f"[{request_id}] - Write concern fulfilled. Returning 200")
                return {"message": "Data received"}

        logger.error(
            f"[{request_id}] - Write concern failed: requested {write_concern}, managed {num_successes + 1}. Returning 500"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to meet write concern: requested {write_concern}, managed {num_successes + 1}",
        )

    elif args.server_type == "backup":
        sleep_time = random.uniform(0, 10)
        await asyncio.sleep(sleep_time)
        return {"message": "Data received"}


@app.get("/get_messages")
async def reurn_messages() -> Dict[str, List[str]]:
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
    processed_requests_ids = set()

    if args.server_type == "main":
        with open("backup_servers.json", "r") as f:
            backup_server_dict = json.load(f)
        print(f"Starting main server '{args.server_name}' at port {args.port}")
        print(
            f"{len(backup_server_dict)} backup servers will be used. Ports: {list(backup_server_dict.values())}\n"
        )
    elif args.server_type == "backup":
        print(f"Starting backup server '{args.server_name}' at port {args.port}\n")

    uvicorn.run(app, host="0.0.0.0", port=args.port)
