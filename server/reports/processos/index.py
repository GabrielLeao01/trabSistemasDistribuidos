import json
import os
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.platypus import Table, TableStyle
from datetime import datetime

def gerar_grafico_sinal(sinal, caminho_grafico):
    plt.figure(figsize=(10, 4))
    plt.plot(sinal, marker='o')
    plt.title('Gráfico do Sinal')
    plt.xlabel('Índice')
    plt.ylabel('Valor do Sinal')
    plt.grid(True)
    plt.savefig(caminho_grafico)
    plt.close()

def criar_relatorio_pdf(dados_json, caminho_imagem, caminho_pdf):
    doc = SimpleDocTemplate(caminho_pdf, pagesize=letter)
    elementos = []
    styles = getSampleStyleSheet()

    titulo = f"Relatório do Processo: {dados_json['idProcesso']}"
    elementos.append(Paragraph(titulo, styles['Title']))
    elementos.append(Spacer(1, 0.2 * inch))


    dataCriacao = datetime.strptime(dados_json['dataCriacao'], "%Y-%m-%d %H:%M:%S")
    dataInicioProcessamento = datetime.strptime(dados_json['dataInicioProcessamento'], "%Y-%m-%d %H:%M:%S")
    dataFimProcessamento = datetime.strptime(dados_json['dataFimProcessamento'], "%Y-%m-%d %H:%M:%S")
    tipoAlgoritmo = dados_json['tipoAlgoritmo']  
    nomeUsuario = dados_json['nomeUsuario']
    
    tempoProcessamento = dataFimProcessamento - dataInicioProcessamento
    tempoSegundos = tempoProcessamento.total_seconds()
    
    elementos.append(Paragraph(f"<b>Data de criação:</b> {dataCriacao.strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
    elementos.append(Paragraph(f"<b>Data de início de processamento:</b> {dataInicioProcessamento.strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
    elementos.append(Paragraph(f"<b>Data de fim de processamento:</b> {dataFimProcessamento.strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
    elementos.append(Paragraph(f"<b>Tempo de Processamento:</b> {tempoSegundos} segundos", styles['Normal']))
    elementos.append(Paragraph(f"<b>Tipo de Algoritmo:</b> {tipoAlgoritmo}", styles['Normal']))
    elementos.append(Paragraph(f"<b>Nome do Usuário:</b> {nomeUsuario}", styles['Normal']))

    caminho_grafico = "grafico_sinal.png"
    gerar_grafico_sinal(dados_json["sinal"], caminho_grafico)
    elementos.append(Spacer(1, 0.2 * inch))
    elementos.append(Image(caminho_grafico, width=6*inch, height=3*inch))

    elementos.append(Spacer(1, 0.2 * inch))
    elementos.append(Image(caminho_imagem, width=6*inch, height=3*inch))

    doc.build(elementos)



PROCESS_FOLDER = "processos"
PDF_FOLDER = "reports/processos"

for processoId in os.listdir(PROCESS_FOLDER):
    print(f"Processando relatório: {processoId}")
    imagem_path = f"{PROCESS_FOLDER}/{processoId}/imagem.jpg"
    json_path = f"{PROCESS_FOLDER}/{processoId}/processo.json"
    pdf_path = f"{PDF_FOLDER}/report_{processoId}.pdf"

    with open(json_path, 'r') as file:
        dados_json = json.load(file)
        
        if(dados_json["dataFimProcessamento"] == None):
          continue

    criar_relatorio_pdf(dados_json, imagem_path, pdf_path)
    print(f"Relatório gerado com sucesso: {processoId}")

