import pandas as pd
import xml.etree.ElementTree as ET
import json

def fill_missing_values(df, columns_to_exclude):
    for column in df.columns:
        if column not in columns_to_exclude:
            if df[column].isnull().any():
                most_frequent_value = df[column].mode()[0]
                df[column].fillna(most_frequent_value, inplace=True)
        else:
            df[column].fillna('N/A', inplace=True)
    return df

def process_csv(input_file, output_file, columns_to_exclude):
    df = pd.read_csv(input_file)
    display_missing_info(df)
    columns_to_exclude = get_excluded_columns(df.columns, columns_to_exclude)
    df = fill_missing_values(df, columns_to_exclude)
    df.to_csv(output_file, index=False)

def process_json(input_file, output_file, columns_to_exclude):
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    df = pd.json_normalize(data)
    display_missing_info(df)
    columns_to_exclude = get_excluded_columns(df.columns, columns_to_exclude)
    df = fill_missing_values(df, columns_to_exclude)
    
    with open(output_file, 'w') as f:
        json.dump(df.to_dict(orient='records'), f, indent=4)

def process_xml(input_file, output_file, columns_to_exclude):
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    data = []
    for child in root:
        record = {}
        for elem in child:
            record[elem.tag] = elem.text
        data.append(record)
    
    df = pd.DataFrame(data)
    display_missing_info(df)
    columns_to_exclude = get_excluded_columns(df.columns, columns_to_exclude)
    df = fill_missing_values(df, columns_to_exclude)
    
    new_root = ET.Element("root")
    for _, row in df.iterrows():
        record_elem = ET.SubElement(new_root, "record")
        for col in df.columns:
            col_elem = ET.SubElement(record_elem, col)
            col_elem.text = str(row[col])
    
    new_tree = ET.ElementTree(new_root)
    new_tree.write(output_file)

def display_missing_info(df):
    missing_info = df.isnull().sum()
    if missing_info.any():
        print("Colunas com valores nulos:")
        for column, count in missing_info.items():
            if count > 0:
                print(f" - {column}: {count} valor(es) nulo(s)")
    else:
        print("Não há valores nulos nas colunas.")

def get_excluded_columns(columns, default_exclude):
    print("Colunas disponíveis:")
    for i, column in enumerate(columns):
        print(f"{i}: {column}")
    excluded = input("Digite o número das colunas que NÃO devem ser preenchidas, separados por vírgula (ex: 1,3): ").strip()
    
    if excluded:
        try:
            excluded_indices = list(map(int, excluded.split(',')))
            excluded_columns = [columns[i] for i in excluded_indices]
        except (ValueError, IndexError):
            print("Entrada inválida. Nenhuma coluna será excluída do preenchimento.")
            excluded_columns = default_exclude
    else:
        excluded_columns = default_exclude

    return excluded_columns

def ask_to_proceed():
    proceed = input("Deseja prosseguir com o tratamento dos valores nulos? (s/n): ").strip().lower()
    return proceed == 's'

def main():
    while True:
        input_file = input("Digite o nome do arquivo de entrada (CSV, JSON ou XML): ")
        output_file = input("Digite o nome do arquivo de saída: ")
        
        columns_to_exclude = []
        
        # Detectar o tipo de arquivo
        if input_file.endswith('.csv'):
            process_csv(input_file, output_file, columns_to_exclude)
        elif input_file.endswith('.json'):
            process_json(input_file, output_file, columns_to_exclude)
        elif input_file.endswith('.xml'):
            process_xml(input_file, output_file, columns_to_exclude)
        else:
            print("Formato de arquivo não suportado.")
            continue
        
        print(f"Arquivo tratado salvo como '{output_file}'.")

        # Perguntar se o usuário deseja continuar
        continue_program = input("Deseja tratar outro arquivo? (s/n): ").strip().lower()
        if continue_program != 's':
            print("Encerrando o programa.")
            break

if __name__ == "__main__":
    main()
