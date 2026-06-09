import os 
from dotenv import load_dotenv 
from openai import OpenAI 
import json 
import gradio as gr 
import base64 
from io import BytesIO 
from PIL import Image
import sqlite3

load_dotenv(override= True) 

openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")


openai= OpenAI()

gemini_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

gemini = OpenAI(api_key= google_api_key , base_url= gemini_url)

system_message= "You are a helpful assistant for an Airline called FlightAI. Give short, courteous answers, no more than 1 sentence. Always be accurate. If you dont know the answer, so so." 


DB = "data.db"


with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS data")

    cursor.execute("""
    CREATE TABLE data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origin TEXT,
        destination TEXT,
        flight_date TEXT,
        price REAL
    )
    """)

    conn.commit()


flights = [
    ("istanbul", "london", "2026-06-10", 799),
    ("istanbul", "london", "2026-06-11", 720),
    ("istanbul", "paris", "2026-06-10", 499),
    ("istanbul", "berlin", "2026-06-10", 450),
    ("istanbul", "tokyo", "2026-06-15", 1400),
]

with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()

    cursor.executemany(
        "INSERT INTO data (origin, destination, flight_date, price) VALUES (?, ?, ?, ?)",
        [(o.lower(), d.lower(), date, price) for o, d, date, price in flights]
    )

    conn.commit()

def get_ticket_price(city): 
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT price FROM data WHERE destination = ?",
            (city.lower(),)
        )
        result = cursor.fetchone()

        if result:
            return f"The price of a ticket to {city} is {result[0]}"

        return "No price found"


def get_ticket_date(city):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()     
        cursor.execute("SELECT flight_date,price FROM data WHERE destination = ? ORDER BY flight_date ", (city.lower(),)) 
        result = cursor.fetchone() 

        if result:
            date,price= result
            return f"The date for flight to {city} available in {date} with price {price}"

        return "No date found for this city " 


price_function = {
    "name": "get_ticket_price",
    "description": "Return the price of the destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that customer wants to travel to."
            }
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}

date_function = {
    "name": "get_ticket_date",
    "description": "Return available flight date and price for a destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that customer wants to travel to."
            }
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}


def handle_tool_calls_and_return_cities(message): 
    responses = []
    cities = []

    for tool_call in message.tool_calls: 
        if tool_call.function.name == "get_ticket_price" :
            arguments = json.loads(tool_call.function.arguments)
            city = arguments.get("destination_city") 
            cities.append(city)
            price_details = get_ticket_price(city)

            responses.append({"role": "tool", "content": price_details, "tool_call_id": tool_call.id})

        if tool_call.function.name == "get_ticket_date" :
            arguments = json.loads(tool_call.function.arguments)
            city = arguments.get("destination_city") 
            cities.append(city)
            date_details = get_ticket_date(city)
            responses.append({"role": "tool", "content": date_details, "tool_call_id": tool_call.id})

    return responses, cities 

def artist(city): 
    image_response = openai.images.generate(
        model= "gpt-image-1", 
        prompt = f"An brochure representing a vacation in {city}, showing tourist spots and everything unique about {city}. Its local foods and famous places to visit. Create a informative brochure.",
        size = "1024x1024", 
    )
    image_base64 = image_response.data[0].b64_json

    image_bytes = base64.b64decode(image_base64)

    return Image.open(BytesIO(image_bytes))

     

def talker(message): 
    response = openai.audio.speech.create(
        model = "gpt-4o-mini-tts",
        voice = "coral", 
        input = message
    )
    return response.content


tools = [
    {"type": "function", "function": price_function},
    {"type": "function", "function": date_function}
]


def chat(history):

    history = [{"role": h["role"], "content": h["content"]} for h in history]

    messages = [{"role": "system", "content": system_message}] + history

    response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        tools=tools
    )

    cities = []
    image = None
    voice = b""
    reply = ""

    max_iter = 5

    while response.choices[0].finish_reason == "tool_calls" and max_iter > 0:
        max_iter -= 1

        message = response.choices[0].message
        responses, cities = handle_tool_calls_and_return_cities(message)

        messages.append(message)
        messages.extend(responses)

        response = openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            tools=tools
        )

    
    if response.choices[0].message.content:
        reply = response.choices[0].message.content
    else:
        reply = "I couldn't generate a response."

    history.append({"role": "assistant", "content": reply})

    voice = talker(reply)

    if cities:
        image = artist(cities[0])

    return history, voice, image


def put_message_in_chatbot(message,history): 
    return "", history + [{"role": "user", "content":message}]

with gr.Blocks() as ui: 
    with gr.Row():
        chatbot = gr.Chatbot(height= 500)
        image_output= gr.Image(height = 500, interactive = False) 
    with gr.Row():
        audio_output=  gr.Audio(autoplay = True) 

    with gr.Row(): 
        message= gr.Textbox(label = "Chat with AI assistant ")

    message.submit(put_message_in_chatbot, inputs = [message,chatbot], outputs = [message, chatbot]).then(
        chat, inputs = chatbot, outputs = [chatbot, audio_output, image_output]
    ) 
        
ui.launch(inbrowser = True)
