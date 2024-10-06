import requests
from requests.exceptions import ConnectionError
import json


def get_messages(url: str = "http://127.0.0.1:8010/get_messages") -> bool:
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return json.loads(response.content.decode("utf-8"))["messages"]
        else:
            return False
    except ConnectionError:
        return False


if __name__ == "__main__":
    url = "http://127.0.0.1:8010/get_messages"
    message_list = get_messages(url)
    if message_list != False:
        print(f"Stored messages:\n{', '.join(message_list)}")
    else:
        print("Failed to retrieve messages")
