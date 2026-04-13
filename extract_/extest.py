import requests
import pandas as pd
import asyncio
import httpx
import time

# Replace with your actual API key
API_KEY = "N3PY7PG3SJG1+60mH6Li3w=="

url = 'https://datamall2.mytransport.sg/ltaodataservice/EVChargingPoints'

headers = {
    "AccountKey": API_KEY,
    "accept": "application/json"
}
start = time.time()
params = {
    'PostalCode': '238843' # need to google for charging point postal code....
}
ptcodes = ['238843','238855','238839','238857']
results = []
def get_poke(client):
    tasks = []
    for ptcode in ptcodes:
        params = {"PostalCode": ptcode}
        tasks.append(asyncio.create_task(client.get(url, headers=headers, params=params)))
    return tasks

async def get_data():
    async with httpx.AsyncClient() as client:
        tasks = get_poke(client)
        responses = await asyncio.gather(*tasks)
        for response in responses:
            if response.status_code == 200:
                results.append(await response.json())
            else:
                print("Error:", response.status_code, response.text)
    print(results)
asyncio.run(get_data())
# import nest_asyncio
# nest_asyncio.apply()
# loop = asyncio.get_event_loop()
# loop.run_until_complete(get_data())
end = time.time()
total_time = end - start
print(total_time)
# response = requests.get(url, headers=headers, params=params)
# if response.status_code == 200:
#     data = response.json()
# else:
#     print("Error:", response.status_code, response.text)
# data