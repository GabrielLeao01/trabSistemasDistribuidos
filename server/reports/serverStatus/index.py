import pandas as pd
import matplotlib.pyplot as plt

def ler_arquivo(caminho_arquivo):
    df = pd.read_csv(caminho_arquivo, sep=';', parse_dates=['created_at'])
    return df

def plotar_graficos(df):
    plt.figure(figsize=(15, 10))

    plt.subplot(3, 1, 1)
    plt.plot(df['created_at'], df['cpu_porcentagem'], marker='o')
    plt.title('Uso de CPU (%)')
    plt.xlabel('Horário')
    plt.ylabel('CPU (%)')
    plt.grid(True)

    plt.subplot(3, 1, 2)
    plt.plot(df['created_at'], df['ram_porcentage'], marker='o', color='orange')
    plt.title('Uso de Memória (%)')
    plt.xlabel('Horário')
    plt.ylabel('Memória (%)')
    plt.grid(True)

    plt.subplot(3, 1, 3)
    plt.plot(df['created_at'], df['ram_gb'], marker='o', color='green')
    plt.title('Uso de Memória (GB)')
    plt.xlabel('Horário')
    plt.ylabel('Memória (GB)')
    plt.grid(True)

    plt.tight_layout()
    
    dataInicio = df['created_at'][0]
    dataFim = df['created_at'][len(df)-1]
    filename = f"reports/serverStatus/serverStatus_{dataInicio.strftime('%Y-%m-%d_%H-%M-%S')}_{dataFim.strftime('%Y-%m-%d_%H-%M-%S')}.png"
    plt.savefig(filename)
    plt.show()
    
    
    plt.close()

caminho_arquivo = 'reports/serverStatus/serverStatus.csv'

df = ler_arquivo(caminho_arquivo)

plotar_graficos(df)
