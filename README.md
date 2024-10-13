# ucu-1-distr-systems
Assignments from the 1st Distributed Systems course, part of UCU Data Engineering program

Build images and start containers:
```
docker compose up --build --force-recreate
```

Send X messages to the main server, Y of them at a time
```
python client/client_post.py X Y
```
Example: `python client/client_post.py 50 12` - send 50 messages, 12 messages at a time

Retrieve all the messages stored by the main server:
```
python client/client_get.py 
```


### Black code style

- Install dev-requirements
```
pip install -r dev-requirements.txt
```
- Create a file named .pre-commit-config.yaml
```
repos:
- repo: https://github.com/psf/black-pre-commit-mirror
  rev: 23.11.0
  hooks:
    - id: black
      args: [--line-length, "88"]
      language_version: python3.11
```
- Install the git hook scripts
```
pre-commit install
```
- After completing this process, a code style check hook will automatically run before each commit

Example
```
black....................................................................Failed
- hook id: black
- files were modified by this hook
reformatted black_test.py
All done! \u2728 \U0001f370 \u2728
1 file reformatted.
```
