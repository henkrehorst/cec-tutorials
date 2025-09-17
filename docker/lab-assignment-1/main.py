import requests
import os

url = "http://notifications-service:3000/api/notify"

headers = {
    "accept": "text/plain; charset=utf-8",
    "Content-Type": "application/json; charset=utf-8",
}

data = {
    "notification_type": "OutOfRange",
    "researcher": "d.landau@uu.nl",
    "measurement_id": "1234",
    "experiment_id": "5678",
    "cipher_data": "D5qnEHeIrTYmLwYX.hSZNb3xxQ9MtGhRP7E52yv2seWo4tUxYe28ATJVHUi0J++SFyfq5LQc0sTmiS4ILiM0/YsPHgp5fQKuRuuHLSyLA1WR9YIRS6nYrokZ68u4OLC4j26JW/QpiGmAydGKPIvV2ImD8t1NOUrejbnp/cmbMDUKO1hbXGPfD7oTvvk6JQVBAxSPVB96jDv7C4sGTmuEDZPoIpojcTBFP2xA"
}

response = requests.post(url, headers=headers, json=data)

print("Status code:", response.status_code)
print("Response body:", response.text)

os.makedirs("./assignment", exist_ok=True)

with open("./assignment/log.txt", "a") as f:
    f.write(response.text + "\n")