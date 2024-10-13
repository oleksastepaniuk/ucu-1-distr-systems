import subprocess
import json
import time


def kill_process_on_port(port):
    try:
        result = subprocess.run(
            ["lsof", "-t", f"-i:{port}"], capture_output=True, text=True
        )
        pid = result.stdout.strip()
        if pid:
            print(f"Killing process {pid} blocking port {port}...")
            subprocess.run(["kill", "-9", pid])
    except Exception as e:
        print(f"Error killing process on port {port}: {e}")


def main():
    ########## Start the main server
    main_port = 8010
    kill_process_on_port(main_port)
    main_server_command = [
        "python",
        "server/server.py",
        "main",
        "main_server_6",
        str(main_port),
    ]

    print("Starting the main server:")
    subprocess.Popen(main_server_command)
    time.sleep(3)

    ########## Start backup servers
    with open("backup_servers.json", "r") as f:
        backup_server_dict = json.load(f)

    for backup_name, port in backup_server_dict.items():
        kill_process_on_port(port)
        backup_server_command = [
            "python",
            "server/server.py",
            "backup",
            backup_name,
            str(port),
        ]
        subprocess.Popen(backup_server_command)
        time.sleep(1)

    print("Finished starting servers.")


if __name__ == "__main__":
    main()
