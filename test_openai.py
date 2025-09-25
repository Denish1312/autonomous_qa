from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
print(f'API Key found: {api_key is not None}')

client = OpenAI(api_key=api_key)

try:
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': 'Say hello!'}],
        max_tokens=10
    )
    print('OpenAI API test successful!')
    print('Response:', response.choices[0].message.content)
except Exception as e:
    print('Error testing OpenAI API:', str(e))
