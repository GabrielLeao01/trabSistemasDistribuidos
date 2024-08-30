import os
import requests
import time
import random
import numpy as np

SINAL_FOLDER = "sinais"
PROCESS_FOLDER = "processos"
SERVER_URL = "http://localhost:5000"
TIPOS_ALGORITMOS = ["CGNR", "CGNE"]
TIPOS_SINAIS = ["A_30x30.csv", "B_30x30.csv", "C_30x30.csv", "A_60x60.csv", "B_60x60.csv", "C_60x60.csv"]

def lerArquivoCSV(caminho_arquivo):
    with open(caminho_arquivo, 'r') as file:
        lines = file.readlines()
        data = []
        for line in lines:
            data.append([float(x) for x in line.strip().split(',')])
        return np.array(data)

def calculate_signal(g):
    n = 64
    s = 794 if len(g) > 50000 else 436
    for c in range(n):
        for l in range(s):
            y = 100 + (1/20) * l * np.sqrt(l)
            g[l + c * s] = g[l + c * s] * y
            
    return g

def ler_sinal(tipo_sinal):
    """Lê o sinal de um arquivo e retorna um array de números."""
    sinal = lerArquivoCSV(f"{SINAL_FOLDER}/{tipo_sinal}")[:,0]
    sinalGanho = calculate_signal(sinal)
    return sinalGanho

def enviar_sinal(id_processo, sinal: np.ndarray, isLast=False):
    """Envia um sinal para o servidor."""
    url = f"{SERVER_URL}/processo/{id_processo}"
    data = {"sinal": sinal.tolist(), "isLast": isLast}
    response = requests.patch(url, json=data)
    if response.status_code == 200:
        print("Sinal enviado com sucesso.")
    else:
        print(f"Erro ao enviar sinal: {response.status_code}")

def capturar_imagem(id_processo):
    """Captura a imagem do processo."""
    url = f"{SERVER_URL}/processo/{id_processo}/imagem"
    response = requests.get(url)
    if response.status_code == 200:
        # Salva a imagem na pasta do processo
        image_path = f"{PROCESS_FOLDER}/{id_processo}/imagem.png"
        with open(image_path, "wb") as f:
            f.write(response.content)
        print(f"Imagem capturada e salva em {image_path}")
    elif response.status_code == 202:
        print("O processo ainda está em andamento.")
    else:
        print(f"Erro ao capturar imagem: {response.status_code}")

def main():
    """Função principal do cliente."""
    nome_cliente = input("Digite o nome do cliente: ")
    while True:
        print("\nEscolha uma opção:")
        print("1: Enviar sinal")
        print("2: Capturar imagem")
        opcao = input("Opção: ")

        if opcao == "1":
            # Cria um processo
            tipo_algoritmo = random.choice(TIPOS_ALGORITMOS)
            url = f"{SERVER_URL}/processo"
            data = {"tipoAlgoritmo": tipo_algoritmo, "nomeUsuario": nome_cliente}
            response = requests.post(url, data=data)
            if response.status_code == 201:
                id_processo = response.json()["idProcesso"]
                print(f"Processo criado com ID: {id_processo}")
                os.makedirs(f"{PROCESS_FOLDER}/{id_processo}", exist_ok=True)

                # Lê o sinal
                tipo_sinal = random.choice(TIPOS_SINAIS)
                sinal = ler_sinal(tipo_sinal)
                
                porcentagem = random.randint(10, 20)
                tamanho_chunk = int(len(sinal) * porcentagem / 100)
                pedacos_sinal = [sinal[i:i + tamanho_chunk] for i in range(0, len(sinal), tamanho_chunk)]
                
                # Envia os pedaços de sinal
                for i, pedaço in enumerate(pedacos_sinal):
                    print(f"Enviando pedaço {i+1}/{len(pedacos_sinal)}")
                    enviar_sinal(id_processo, pedaço, isLast=(i == len(pedacos_sinal) - 1))
                    time.sleep(random.randint(1, 2))
            else:
                print(f"Erro ao criar processo: {response.status_code}")

        elif opcao == "2":
            # Mostra os processos sem imagem
            processos_sem_imagem = []
            for processo in os.listdir("processos"):
                imagem_path = f"{PROCESS_FOLDER}/{processo}/imagem.png"
                if not os.path.exists(imagem_path):
                    processos_sem_imagem.append(processo)

            if processos_sem_imagem:
                print("\nProcessos sem imagem:")
                for i, processo in enumerate(processos_sem_imagem):
                    print(f"{i+1}: {processo}")
                escolha = input("Escolha um processo: ")
                if escolha.isdigit() and 1 <= int(escolha) <= len(processos_sem_imagem):
                    id_processo = processos_sem_imagem[int(escolha) - 1]
                    capturar_imagem(id_processo)
                else:
                    print("Opção inválida.")
            else:
                print("Não há processos sem imagem.")

        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()