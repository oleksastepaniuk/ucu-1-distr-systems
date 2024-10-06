import argparse
from time import sleep
import aiohttp
import asyncio
from typing import List


async def post_message(
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


async def send_messages_concurrently(messages: List, url: str, concurrency: int) -> int:
    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [post_message(m, session, url) for m in messages]
        results = await asyncio.gather(*tasks)

    success_count = sum(results)
    return success_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script for testing message logging server."
    )
    parser.add_argument(
        "message_number", type=int, help="Number of of messages to send"
    )
    parser.add_argument("concurrency", type=int, help="Number of simultaneous requests")
    args = parser.parse_args()

    url = "http://127.0.0.1:8010/post_message"
    messages = [
        f"Message {i}/{args.message_number};" for i in range(1, args.message_number + 1)
    ]

    success_count = asyncio.run(
        send_messages_concurrently(messages, url, args.concurrency)
    )

    print(
        f"Sent {args.message_number} messages with {success_count} successes.\n{args.concurrency} simultaneous messages at a time."
    )
