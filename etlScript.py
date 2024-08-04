import pandas as pd
import json
import xml.etree.ElementTree as ET
import mysql.connector
from mysql.connector import Error

def get_file_path():
    return input("Por favor, especifique o caminho do arquivo: ")

def identify_file_type(file_path):
    if file_path.endswith('.json'):
        return 'json'
    elif file_path.endswith('.csv'):
        return 'csv'
    elif file_path.endswith('.xml'):
        return 'xml'
    else:
        raise ValueError("Tipo de arquivo não suportado. Por favor, forneça um arquivo JSON, CSV ou XML.")

def get_columns(file_path, file_type):
    if file_type == 'json':
        with open(file_path, 'r') as f:
            data = json.load(f)
        df = pd.json_normalize(data)
    elif file_type == 'csv':
        df = pd.read_csv(file_path)
    elif file_type == 'xml':
        tree = ET.parse(file_path)
        root = tree.getroot()
        data = [{child.tag: child.text for child in element} for element in root]
        df = pd.DataFrame(data)
    return df.columns.tolist(), df

def transform_to_sql(df, columns):
    host = input("Especifique o host do MySQL: ")
    user = input("Especifique o usuário do MySQL: ")
    password = input("Especifique a senha do MySQL: ")
    database = input("Especifique o nome do banco de dados: ")
    table = input("Especifique o nome da tabela: ")

    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            # Limpar os NaNs substituindo por None (NULL no MySQL)
            df = df.where(pd.notnull(df), None)
            # Formar a query de inserção
            cols = ', '.join([f'`{col}`' for col in columns])
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO `{table}` ({cols}) VALUES ({placeholders})"

            # Inserir os dados
            for row in df.itertuples(index=False):
                cursor.execute(insert_query, tuple(row))
            connection.commit()
            print("Dados inseridos com sucesso no MySQL")
    
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def main():
    while True:
        file_path = get_file_path()
        try:
            file_type = identify_file_type(file_path)
            columns, df = get_columns(file_path, file_type)
            print("Nomes das prováveis colunas para armazenamento no banco de dados SQL:", columns)
            transform = input("Você deseja transformar os dados para SQL? (sim/não): ").strip().lower()
            if transform == 'sim':
                transform_to_sql(df, columns)
            else:
                print("Transformação não realizada.")
        except ValueError as ve:
            print(ve)
        
        again = input("Você deseja processar outro arquivo? (sim/não): ").strip().lower()
        if again != 'sim':
            print("Programa encerrado.")
            break

if __name__ == "__main__":
    main()

