import asyncio
import websockets
import pymongo
import json

# Configuración de la conexión a MongoDB Atlas
mongo_url = 'mongodb://localhost:27017/'
client = pymongo.MongoClient(mongo_url)
db = client["Arduino"]
collection = db["datos"]

async def handle_client(websocket, path):
    while True:
        # Recibir datos desde el cliente WebSocket (Arduino)
        data = await websocket.recv()
        print(f"Datos recibidos desde Arduino: {data}")

        try:
            # Parsear el JSON recibido
            json_data = json.loads(data)
            print(f"JSON analizado: {json_data}")

            # Guardar los datos en la colección de MongoDB
            collection.insert_one(json_data)
            print("Datos guardados en MongoDB Atlas")

            # Enviar una respuesta a Arduino
            response = "Datos recibidos y guardados correctamente"
            await websocket.send(response)
            print(f"Respuesta enviada a Arduino: {response}")
        except json.JSONDecodeError as e:
            print(f"Error al analizar JSON: {e}")

async def start_server():
    server = await websockets.serve(handle_client, "0.0.0.0", 5000)
    print("Servidor WebSocket iniciado")

    await server.wait_closed()

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server())
