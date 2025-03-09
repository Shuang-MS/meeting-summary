from openai import AzureOpenAI
from dotenv import load_dotenv
import base64
import os

load_dotenv()
GPT4o_API_KEY = os.getenv("GPT4o_API_KEY")
GPT4o_DEPLOYMENT_ENDPOINT = os.getenv("GPT4o_DEPLOYMENT_ENDPOINT")
GPT4o_DEPLOYMENT_NAME = os.getenv("GPT4o_DEPLOYMENT_NAME")


client = AzureOpenAI(
  azure_endpoint = GPT4o_DEPLOYMENT_ENDPOINT, 
  api_key=GPT4o_API_KEY,  
  api_version="2024-02-01"
)


def call_openAI(text):
    print(f"deploy is {GPT4o_DEPLOYMENT_NAME}")
    response = client.chat.completions.create(
        model=GPT4o_DEPLOYMENT_NAME,
        messages = text,
        temperature=0.0
    )
    return response.choices[0].message.content

def encode_image(image):
    
    return base64.b64encode(image).decode("utf-8")
    
def analysis_image(image):
    
    question = "Please provide a detailed explanation of the image."
    encoded_image = encode_image(image.getvalue())
    messages=[
        {"role": "system", "content": "You are a helpful assistant that responds in image. Help me with my meeting recording image!"},
        {"role": "user", "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{encoded_image}"}
            }
        ]}
    ]
    result = call_openAI(messages)
    
    print(f"Image analysis result: {result}")
    return result

def analysis_text(userPrompt,text):
    question = "请提供一份侧重于会议内容和待办事项的总结. 使用良好的中文格式输出"
    messages=[
        {"role": "system", "content": "You are a helpful assistant that responds in text. Help me with my meeting recording text!"},
        {"role": "user", "content": [
            {"type": "text", "text": question + userPrompt},
            {"type": "text", "text": text}
        ]}
    ]
    result = call_openAI(messages)
    
    print(f"Text analysis result: {result}")
    return result