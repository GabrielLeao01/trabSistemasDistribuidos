import base64
import os
import json
import time
import random
import threading
from datetime import datetime
from flask import Flask, request, send_from_directory, jsonify
import psutil
import numpy as np
import matplotlib.pyplot as plt

app = Flask(__name__)
semaphore = threading.Semaphore()

MATRIZ_FOLDER = 'matriz'
PROCESS_FOLDER = 'processos'
SERVER_STATUS_PATH = 'reports/serverStatus/serverStatus.csv'
MAX_THREADS = 2
CURRENT_THREADS = 0
FILA_PATH = "fila.txt"
LENGTH_SINAL_30X30 = 27904
LENGTH_SINAL_60X60 = 50816
ALGORITMO_CGNR = "CGNR"
ALGORITMO_CGNE = "CGNE"

erro = 1e-4

def lerArquivoCSV(caminho_arquivo):
    with open(caminho_arquivo, 'r') as file:
        lines = file.readlines()
        data = []
        for line in lines:
            data.append([float(x) for x in line.strip().split(',')])
        return np.array(data)

Matriz_h_60x60 = lerArquivoCSV(f"{MATRIZ_FOLDER}/H_60x60.csv")
Matriz_h_30x30 = lerArquivoCSV(f"{MATRIZ_FOLDER}/H_30x30.csv")

def getMatrizH(tamanho):
    if tamanho == 60:
        return Matriz_h_60x60
    elif tamanho == 30:
        return Matriz_h_30x30

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
            with open(f"{FILA_PATH}", "a") as file:
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
    
def saveImage(path, image, metadata):
    plt.imsave(path, image, cmap='gray', metadata=metadata)
    
def binary_to_base64(binary):
    return base64.b64encode(binary).decode('utf-8')
    
def process_image(id_processo):
    increment_current_threads()
    
    process_folder_path = f"{PROCESS_FOLDER}/{id_processo}"

    tipoAlgoritmo = None
    usuario = None
    sinal = None
    dataInicioProcessamento = None
    dataFimProcessamento = None
    
    with open(f"{process_folder_path}/processo.json", 'r+') as f:
        data = json.load(f)
        data["dataInicioProcessamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        tipoAlgoritmo = data["tipoAlgoritmo"]
        sinal = np.array(data["sinal"])
        usuario = data["nomeUsuario"]
        dataInicioProcessamento = data["dataInicioProcessamento"]

    tamanhoImagem = None
    if sinal.shape[0] == LENGTH_SINAL_30X30:
        tamanhoImagem = 30
    elif sinal.shape[0] == LENGTH_SINAL_60X60:
        tamanhoImagem = 60
        
    matriz_h = getMatrizH(tamanhoImagem)
    
    imagem = None
    iteracoes = None
    
    if tipoAlgoritmo == ALGORITMO_CGNE:
        imagem, iteracoes = cgne(matriz_h, sinal, tamanhoImagem)
    elif tipoAlgoritmo == ALGORITMO_CGNR:
        imagem, iteracoes = cgnr(matriz_h, sinal, tamanhoImagem)
    
    
    with open(f"teste.txt", "w") as f:
        f.write(str(imagem))

    dataFimProcessamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(f"{process_folder_path}/processo.json", 'r+') as f:
        data = json.load(f)
        data["dataFimProcessamento"] = dataFimProcessamento
        data["iteracoes"] = iteracoes
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    
    saveImage(f"{process_folder_path}/imagem.png", imagem, {
        'Algoritmo': tipoAlgoritmo,
        'Usuario': usuario,
        'Iteracoes': str(iteracoes),
        'dataInicioProcessamento': dataInicioProcessamento,
        'dataFimProcessamento': dataFimProcessamento
    })
    
    
    decrement_current_threads()

def popular_fila():
    count = 0
    while True:
        print("salvando processo na fila")
        with open(f"{FILA_PATH}", "a") as f:
            f.write(f"processo-{count}\n")
        count += 1
        time.sleep(1)


def cgnr(h,g,tam_image):
    f = np.zeros((tam_image**2)) 
    r = g - np.dot(h, f)
    z = np.dot(np.transpose(h), r)
    p = z
    i = 0
    while True:
    # for i in range(0,30):
        w = np.dot(h, p)
        a = np.linalg.norm(z,ord=2) ** 2 / np.linalg.norm(w,ord=2) ** 2
        f = f + np.dot(a, p)
        r_ant = r
        r = r - np.dot(a, w)
        z_ant = z
        z = np.dot(np.transpose(h), r)
        beta = np.linalg.norm(z,ord=2) ** 2 / np.linalg.norm(z_ant,ord=2) ** 2
        p = z + np.dot(beta, p)
        if(calcula_erro(r,r_ant) < erro):
            break
        i += 1
    return f.reshape(tam_image,tam_image),i

def cgne(h,g,tam_image):
    f = np.zeros((tam_image**2))
    r = g - np.dot(h, f)
    p = np.dot(np.transpose(h), r)
    i = 0
    while True:
    # for i in range(0,30):
        r_ant = r
        a = np.dot(np.transpose(r), r)/np.dot(np.transpose(p), p)
        f = f + a*p
        r = r - np.dot(a,np.dot(h, p))  
        Beta = np.dot(np.transpose(r), r)/np.dot(np.transpose(r_ant), r_ant)
        p = np.dot(np.transpose(h), r) + np.dot(Beta, p)
        if(calcula_erro(r,r_ant)< erro):
            break
        i += 1
    return f.reshape(tam_image,tam_image),i


def calcula_erro(r,r_ant):
    return abs(np.linalg.norm(r, ord=2) - np.linalg.norm(r_ant, ord=2))

def monitor_fila():
    while True:
        print("current threads", CURRENT_THREADS)
        if CURRENT_THREADS < MAX_THREADS:
            with open(f"{FILA_PATH}", "r+") as f:
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
    print("OLA")
    process_folder_path = f"{PROCESS_FOLDER}/{id_processo}"
    with open(f"{process_folder_path}/processo.json", 'r') as f:
        data = json.load(f)
        if data["dataFimProcessamento"]:
            return send_from_directory(f"{process_folder_path}", "imagem.png")
        else:
            return jsonify({"message": "O processo ainda está em andamento"}), 202


def monit_server():
    with open(SERVER_STATUS_PATH, 'w') as f:
        f.seek(0)
        f.write("created_at;cpu_porcentagem;ram_porcentage;ram_gb\n")
        f.truncate()
    
    while True:
        with open(SERVER_STATUS_PATH, 'a') as f:
            cpu = psutil.cpu_percent()
            ram_porcentage = psutil.virtual_memory()[2]
            ram_gb = psutil.virtual_memory()[3]/1000000000
            createdAt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{createdAt};{"{:.2f}".format(cpu)};{"{:.2f}".format(ram_porcentage)};{"{:.2f}".format(ram_gb)}\n")
            
        time.sleep(1)
        
        
threading.Thread(target=monit_server).start()
threading.Thread(target=monitor_fila).start()
app.run(debug=False)