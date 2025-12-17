'''

NEEDS a paid plan to work

'''



from openai import OpenAI
import os

client = OpenAI(api_key= os.getenv("OPENAI_API_KEY")) #I am not showing my key here
#client = OpenAI(api_key= "you-api-key-here")         #use yours here

response = client.responses.create(
    model= "gpt-3.5-turbo",  # or "gpt-4",
    input="Write a one-sentence bedtime story about a unicorn."
)

print(response.output_text)