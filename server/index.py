import base64
import os
import json
import time
import random
import threading
from datetime import datetime
from flask import Flask, request, send_from_directory, jsonify

app = Flask(__name__)
semaphore = threading.Semaphore()

PROCESS_FOLDER = 'processos'
MAX_THREADS = 2
CURRENT_THREADS = 0

def generate_random_id():
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz1234567890') for i in range(10))

def create_process_json(id_processo, tipo_algoritmo, nome_usuario):
    data = {
        "idProcesso": id_processo,
        "tipoAlgoritmo": tipo_algoritmo,
        "nomeUsuario": nome_usuario,
        "sinal": [],
        "dataCriacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataInicioProcessamento": None,
        "dataFimProcessamento": None
    }
    return data

def update_process_json(id_processo, sinal, isLast):
    process_folder_path = f"{PROCESS_FOLDER}/{id_processo}"
    with open(f"{process_folder_path}/processo.json", 'r+') as f:
        data = json.load(f)
        data["sinal"].extend(sinal)
        if isLast:
            with open(f"{PROCESS_FOLDER}/fila.txt", "a") as file:
                file.write(id_processo + "\n")
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

def increment_current_threads():
    semaphore.acquire()
    global CURRENT_THREADS
    CURRENT_THREADS += 1
    semaphore.release()
    
def decrement_current_threads():
    semaphore.acquire()
    global CURRENT_THREADS
    CURRENT_THREADS -= 1
    semaphore.release()
    
def process_image(id_processo):
    increment_current_threads()
    
    process_folder_path = f"{PROCESS_FOLDER}/{id_processo}"
    with open(f"{process_folder_path}/processo.json", 'r+') as f:
        data = json.load(f)
        data["dataInicioProcessamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    time.sleep(10)
    with open(f"{process_folder_path}/processo.json", 'r+') as f:
        data = json.load(f)
        data["dataFimProcessamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    imagem_base64 = "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAIAAADTED8xAAADMElEQVR4nOzVwQnAIBQFQYXff81RUkQCOyDj1YOPnbXWPmeTRef+/3O/OyBjzh3CD95BfqICMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMO0TAAD//2Anhf4QtqobAAAAAElFTkSuQmCC"
    imagem_decodificada = base64.b64decode(imagem_base64)
    with open(f"{process_folder_path}/imagem.jpg", "wb") as f:
        f.write(imagem_decodificada)
        
    decrement_current_threads()

def popular_fila():
    count = 0
    while True:
        print("salvando processo na fila")
        with open(f"{PROCESS_FOLDER}/fila.txt", "a") as f:
            f.write(f"processo-{count}\n")
        count += 1
        time.sleep(1)

def monitor_fila():
    while True:
        print("current threads", CURRENT_THREADS)
        if CURRENT_THREADS < MAX_THREADS:
            with open(f"{PROCESS_FOLDER}/fila.txt", "r+") as f:
                lines = f.readlines()
                
                if(len(lines) > 0):
                    idProcesso = lines[0].strip()
                    print(f"VAI PROCESSAR -{idProcesso}-")
                    thread = threading.Thread(target=process_image, args=(idProcesso,))
                    
                    thread.start()
                    del lines[0]
                    
                    f.seek(0)
                    f.writelines(lines)
                    f.truncate()
        else:
            print("Max threads reached")
        time.sleep(1)

@app.route('/processo', methods=['POST'])
def create_process():
    tipo_algoritmo = request.form.get('tipoAlgoritmo')
    nome_usuario = request.form.get('nomeUsuario')
    id_processo = generate_random_id()
    process_folder_path = f"{PROCESS_FOLDER}/{id_processo}"
    
    os.makedirs(process_folder_path, exist_ok=True)
    data = create_process_json(id_processo, tipo_algoritmo, nome_usuario)
    process_file_path = f"{process_folder_path}/processo.json"
    with open(process_file_path, 'w') as f:
        json.dump(data, f, indent=4)
    return jsonify({"idProcesso": id_processo}), 201

@app.route('/processo/<id_processo>', methods=['PATCH'])
def update_process(id_processo):
    sinal = request.json.get('sinal')
    isLast = request.json.get('isLast', False)
    update_process_json(id_processo, sinal, isLast)
    return jsonify({"message": "Sinal atualizado com sucesso"}), 200

@app.route('/processo/<id_processo>/imagem', methods=['GET'])
def get_imagem(id_processo):
    process_folder_path = f"{PROCESS_FOLDER}/{id_processo}"
    with open(f"{process_folder_path}/processo.json", 'r') as f:
        data = json.load(f)
        if data["dataFimProcessamento"]:
            return send_from_directory(f"{process_folder_path}", "imagem.jpg")
        else:
            return jsonify({"message": "O processo ainda está em andamento"}), 202

threading.Thread(target=monitor_fila).start()
app.run(debug=False)