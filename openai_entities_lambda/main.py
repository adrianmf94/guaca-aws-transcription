import json
import openai
import re
import os
from dynamodb_helper import DynamoDBHelper

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")

def handler(event, context):
    dynamodb_helper = DynamoDBHelper(DYNAMODB_TABLE)
    transcript = event.get("transcript")
    audio_key = event.get("audio_key")
    final_response = []
    openai_json1 = None
    openai_json2 = None

    cars_identified = f"Despliega en formato lista de JSONs (campos: modelo, marca, año) (en español, remover tildes o caracteres especiales) una lista de los vehículos que encuentres en el siguiente texto: {transcript}."

    ask_openai = openai.Completion.create(
        engine="text-davinci-003",
        prompt=cars_identified,
        max_tokens=1000,
    )

    #print(f"ask_openai {ask_openai}")
    try:
        openai_response = ask_openai.choices[0].text.strip()
        print(f"openai_response {openai_response}")
        cleaned_input = re.sub(r'^.*?\[', '[', openai_response)
        print(f"cleaned_input {cleaned_input}")
        openai_json1 = json.loads(cleaned_input)
        print(f"openai_json1 {openai_json1}")
        final_response.append(openai_json1)
    except Exception as e:
        print("Error", e)

    availability = f"Despliega en formato lista de JSONs (campos: Nombre del repuesto, sucursal, disponibilidad (si o no)) (en español, remover tildes o caracteres especiales) el/los repuestos de vehículo que el cliente solicitó y si había en inventario o no y en cuál sucursal de la empresa: {transcript}."

    ask_openai = openai.Completion.create(
        engine="text-davinci-003",
        prompt=availability,
        max_tokens=1000,
    )

    #print(f"ask_openai {ask_openai}")
    try:
        openai_response2 = ask_openai.choices[0].text.strip()
        print(f"openai_response 2 {openai_response2}")
        cleaned_input2 = re.sub(r'^.*?\[', '[', openai_response2)
        print(f"cleaned_input2 {cleaned_input2}")
        openai_json2 = json.loads(cleaned_input2)
        print(f"openai_json2 {openai_json2}")
        final_response.append(openai_json2)
    except Exception as e:
        print("Error", e)
    

    
    if openai_json1 is not None and openai_json2 is not None:
        item = {
            "Audio_key": audio_key,
            "Transcript": transcript,
            "Vehiculos": openai_json1,
            "Disponibilidad": openai_json2,
        }
        dynamodb_helper.insert_item(item)

    return {
        "statusCode": 200,
        "body": final_response,
    }

