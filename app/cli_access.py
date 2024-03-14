import requests

# get the input arguments, first the hostname, then the command then the key and finally the argument

# get the hostname
hostname = input("Enter the hostname: ")

# get the command
command = input("Enter the command (setprompt, apikey or llmkey): ")

# get the key
key = input("Enter the Admin key: ")

# get the argument
argument = input("Enter the argument: ")

# depending on the command, we will define the URL
if command == "llmkey":
    url = f"http://{hostname}/admin/setllmkey"
    data = {"key": argument}
elif command == "apikey":
    url = f"http://{hostname}/admin/addapikey"
    data = {"key": argument, "user": "default", "name": "test"}
elif command == "setprompt":
    url = f"http://{hostname}/admin/setprompt"
    data = {"prompt": argument}

# Send the request to the API. All commands are post requests and need the "AdminKey" header
print(f"Sending request to {url} with data {data} and key {key}")
response = requests.post(url, headers={"AdminKey": key}, json=data)
response.raise_for_status()
print("Done")
