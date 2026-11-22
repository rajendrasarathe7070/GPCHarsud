
from openai import OpenAI
import os
client = OpenAI(
    api_key= "gsk_03e4oesJAgyKcfsZUqpQWGdyb3FYpTNQOP3ep3qD1zyMeY",
    base_url="https://api.groq.com/openai/v1",
)

while True :
    x = input(">>>")
    response = client.responses.create(
    input=x,
    model="openai/gpt-oss-20b",
)
    print(response.output_text)
