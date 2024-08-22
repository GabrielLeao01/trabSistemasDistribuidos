import os
import requests
import time
import random

SINAL_FOLDER = "sinais"
PROCESS_FOLDER = "processos"
SERVER_URL = "http://localhost:5000"
TIPOS_ALGORITMOS = ["A", "B"]
TIPOS_SINAIS = ["sinal1", "sinal2", "sinal3"]
TAMANHO_CHUNK = 5

def ler_sinal(tipo_sinal):
    """Lê o sinal de um arquivo e retorna um array de números."""
    with open(f"{SINAL_FOLDER}/{tipo_sinal}.txt", "r") as f:
        sinal = [int(line.strip()) for line in f]
    return sinal

def enviar_sinal(id_processo, sinal, isLast=False):
    """Envia um sinal para o servidor."""
    url = f"{SERVER_URL}/processo/{id_processo}"
    data = {"sinal": sinal, "isLast": isLast}
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
        image_path = f"{PROCESS_FOLDER}/{id_processo}/imagem.jpg"
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

                # Divide o sinal em pedaços de até TAMANHO_CHUNK posições
                pedacos_sinal = [sinal[i:i + TAMANHO_CHUNK] for i in range(0, len(sinal), TAMANHO_CHUNK)]

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
                imagem_path = f"{PROCESS_FOLDER}/{processo}/imagem.jpg"
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