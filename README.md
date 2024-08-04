# Dashboard Vendas de Carros
Olá pessoal tudo bem? Construí esse dashboard de vendas de carros para obter insights para alavancar as vendas. Os dados foram obtidos no formato csv no site **wwww.kaggle.com**, posteriormente foi realizado o processo de ETL (Extract, Transform, Load) para tratar de espaços em brancos ou com valores null, para isso criei um script em **python** que tratasse desses espaços:

```python
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

```
O script tem como entrada o arquivo csv para tratar e tem como saída outro arquivo csv ja tratado. O próximo passo foi transfomar o banco de dados csv em sql, para a realização da transformação foi criado um script em **python** que tem como entrada um arquivo csv e como saída uma mensagem de confirmação da transformação. É importante salientar que, para que a transformação seja bem-sucedida, foi preciso criar uma tabela sql contendo os mesmos nomes das colunas do arquivo csv - Segue abaixo o script para transformar csv em sql:

```python
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

```
Deixarei o arquivo csv do banco de dados em anexo.
Com os dados tratados e devidamente transformados em sql, é hora de criar nosso dashboard. Para a criação do dashboard eu utilizei o **Grafana** uma ferramenta de construção de dashboard completa e gratuita. Segue abaixo como ficou o dashboard

[Gravação de tela de 04-08-2024 13:58:21.webm](https://github.com/user-attachments/assets/826b6576-edc2-4175-86f9-1583f76a556b)

Segue tambem o Dashboard em formato JSON:
```json
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": {
          "type": "grafana",
          "uid": "-- Grafana --"
        },
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": 5,
  "links": [],
  "panels": [
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "custom": {
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 13,
        "w": 24,
        "x": 0,
        "y": 0
      },
      "id": 6,
      "options": {
        "basemap": {
          "config": {},
          "name": "Layer 0",
          "type": "default"
        },
        "controls": {
          "mouseWheelZoom": true,
          "showAttribution": true,
          "showDebug": false,
          "showMeasure": false,
          "showScale": false,
          "showZoom": true
        },
        "layers": [
          {
            "config": {
              "showLegend": true,
              "style": {
                "color": {
                  "fixed": "dark-green"
                },
                "opacity": 0.4,
                "rotation": {
                  "fixed": 0,
                  "max": 360,
                  "min": -360,
                  "mode": "mod"
                },
                "size": {
                  "field": "number_of_sales",
                  "fixed": 5,
                  "max": 35,
                  "min": 5
                },
                "symbol": {
                  "fixed": "img/icons/marker/circle.svg",
                  "mode": "fixed"
                },
                "symbolAlign": {
                  "horizontal": "center",
                  "vertical": "center"
                },
                "text": {
                  "field": "state",
                  "fixed": "",
                  "mode": "field"
                },
                "textConfig": {
                  "fontSize": 15,
                  "offsetX": 0,
                  "offsetY": 0,
                  "textAlign": "center",
                  "textBaseline": "middle"
                }
              }
            },
            "filterData": {
              "id": "byRefId",
              "options": "A"
            },
            "location": {
              "latitude": "latitude",
              "longitude": "longitude",
              "mode": "coords"
            },
            "name": "Estados",
            "tooltip": true,
            "type": "markers"
          }
        ],
        "tooltip": {
          "mode": "details"
        },
        "view": {
          "allLayers": true,
          "id": "north-america",
          "lat": 40,
          "lon": -100,
          "zoom": 4
        }
      },
      "pluginVersion": "11.1.3",
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    sc.state,\n    sc.latitude,\n    sc.longitude,\n    COUNT(v.vin) AS number_of_sales\nFROM\n    car_prices v\nJOIN\n    state_coordinates sc\nON\n    v.state = sc.state\nWHERE\n    LENGTH(v.state) = 2\n    AND LENGTH(sc.state) = 2\nGROUP BY\n    sc.state, sc.latitude, sc.longitude\nORDER BY\n    number_of_sales DESC;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Vendas Por Estados",
      "type": "geomap"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 0,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "insertNulls": false,
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "auto",
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 9,
        "w": 24,
        "x": 0,
        "y": 13
      },
      "id": 9,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    saledate AS days,\n    COUNT(*) AS 'Número de Vendas'\nFROM\n    car_prices\nGROUP BY\n    days\nORDER BY\n    days;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Vendas",
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 10,
        "w": 8,
        "x": 0,
        "y": 22
      },
      "id": 10,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "horizontal",
        "showValue": "always",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 100
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    DATE_FORMAT(saledate, '%M') AS month_name, -- Nome completo do mês\n    COUNT(*) AS number_of_sales\nFROM\n    car_prices\nGROUP BY\n    month_name\nORDER BY\n    number_of_sales DESC;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Número de Veículos Vendidos por Mês",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 10,
        "w": 8,
        "x": 8,
        "y": 22
      },
      "id": 11,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "horizontal",
        "showValue": "always",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 100
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    DATE_FORMAT(saledate, '%M') AS month,\n    AVG(sellingprice) AS preco_medio\nFROM\n    car_prices\nGROUP BY\n    month\nORDER BY\n\tpreco_medio DESC;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Preço Médio de Venda por Mês",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byName",
              "options": "average_price"
            },
            "properties": [
              {
                "id": "unit",
                "value": "short"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 10,
        "w": 4,
        "x": 16,
        "y": 22
      },
      "id": 13,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "vertical",
        "showValue": "never",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 100
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    DATE_FORMAT(saledate, '%Y') AS years,\n    AVG(sellingprice) AS average_price\nFROM\n    car_prices\nGROUP BY\n    years\nORDER BY\n    years DESC;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Preço Médio de Venda por Ano",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byName",
              "options": "number_of_sales"
            },
            "properties": [
              {
                "id": "unit",
                "value": "short"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 10,
        "w": 4,
        "x": 20,
        "y": 22
      },
      "id": 12,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "vertical",
        "showValue": "never",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 0
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    DATE_FORMAT(saledate, '%Y') AS years,\n    COUNT(*) AS 'Número de Vendas'\nFROM\n    car_prices\nGROUP BY\n    years\nORDER BY\n    years DESC;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Número de Veículos Vendidos por Ano",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 10,
        "w": 12,
        "x": 0,
        "y": 32
      },
      "id": 8,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "horizontal",
        "showValue": "auto",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 0
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    make as 'Marca',\n    COUNT(vin) AS numero_de_vendas\nFROM\n    car_prices\nWHERE\n    make IS NOT NULL\nGROUP BY\n    make\nORDER BY\n    numero_de_vendas DESC\nLIMIT 20;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "20 Marcas Mais Vendidas",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 10,
        "w": 12,
        "x": 12,
        "y": 32
      },
      "id": 3,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "horizontal",
        "showValue": "always",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xField": "Modelo",
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 100
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    make as 'Marca',\n    model as 'Modelo',\n    COUNT(*) AS numero_de_vendas\nFROM\n    car_prices\nGROUP BY\n    make,\n    model\nORDER BY\n    numero_de_vendas DESC\nLIMIT 20;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "20 Veículos Mais Vendidos",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "fieldConfig": {
        "defaults": {
          "custom": {
            "align": "auto",
            "cellOptions": {
              "type": "auto"
            },
            "inspect": false
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 9,
        "w": 6,
        "x": 0,
        "y": 42
      },
      "id": 4,
      "options": {
        "cellHeight": "sm",
        "footer": {
          "countRows": false,
          "fields": "",
          "reducer": [
            "sum"
          ],
          "show": false
        },
        "showHeader": true
      },
      "pluginVersion": "11.1.3",
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    make AS 'Marca',\n    model AS 'Modelo',\n    AVG(sellingprice) AS Média\nFROM\n    car_prices\nWHERE\n    sellingprice IS NOT NULL\nGROUP BY\n    make,\n    model\nORDER BY\n    Média DESC;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Preço Médio por Marca e Modelo",
      "type": "table"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "fieldConfig": {
        "defaults": {
          "custom": {
            "align": "auto",
            "cellOptions": {
              "type": "auto"
            },
            "inspect": false
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 9,
        "w": 6,
        "x": 6,
        "y": 42
      },
      "id": 5,
      "options": {
        "cellHeight": "sm",
        "footer": {
          "countRows": false,
          "fields": "",
          "reducer": [
            "sum"
          ],
          "show": false
        },
        "showHeader": true
      },
      "pluginVersion": "11.1.3",
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "WITH RankedPrices AS (\n    SELECT\n        make,\n        model,\n        sellingprice,\n        ROW_NUMBER() OVER (PARTITION BY make, model ORDER BY sellingprice) AS RowAsc,\n        ROW_NUMBER() OVER (PARTITION BY make, model ORDER BY sellingprice DESC) AS RowDesc\n    FROM\n        car_prices\n    WHERE\n        sellingprice IS NOT NULL\n),\nMedianPrices AS (\n    SELECT\n        make,\n        model,\n        AVG(sellingprice) AS median_price\n    FROM\n        RankedPrices\n    WHERE\n        RowAsc = RowDesc\n        OR RowAsc + 1 = RowDesc\n        OR RowAsc = RowDesc + 1\n    GROUP BY\n        make,\n        model\n)\nSELECT\n    make as 'Marca',\n    model as 'Modelo',\n    median_price as 'Mediana'\nFROM\n    MedianPrices\nORDER BY\n    median_price DESC;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Preço Mediano por Marca e Modelo",
      "type": "table"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "description": "10 veículos com as maiores diferenças entre o valor estimado pelo Manheim Market Report (mmr) e o preço de venda (sellingprice)",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 9,
        "w": 12,
        "x": 12,
        "y": 42
      },
      "id": 1,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "right",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "never",
        "stacking": "normal",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xField": "Modelo",
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 100
      },
      "pluginVersion": "11.1.3",
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    vin,\n    make as 'Marca',\n    model as 'Modelo',\n    sellingprice as 'Preço de Venda',\n    mmr as 'Preço MMR',\n    (sellingprice - mmr) AS diferenca_de_precos\nFROM\n    car_prices\nWHERE\n    mmr IS NOT NULL\n    AND sellingprice IS NOT NULL\nORDER BY\n    diferenca_de_precos DESC\nLIMIT 20;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "MMR x SELLINGPRICE",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "description": "Analisa a relação entre a quilometragem e o preço de venda",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "pointSize": {
              "fixed": 5
            },
            "scaleDistribution": {
              "type": "linear"
            },
            "show": "points"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byName",
              "options": "sellingprice"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Preço de Vendas"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 51
      },
      "id": 14,
      "options": {
        "dims": {
          "frame": 0
        },
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "series": [],
        "seriesMapping": "auto",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    odometer,\n    sellingprice\nFROM\n    car_prices\nWHERE\n    odometer IS NOT NULL\n    AND sellingprice IS NOT NULL\nORDER BY\n    odometer;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Odometer vs Preço",
      "type": "xychart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 51
      },
      "id": 15,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "always",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 0
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    CASE\n        WHEN odometer < 10000 THEN '0-10,000 km'\n        WHEN odometer BETWEEN 10000 AND 29999 THEN '10,000-30,000 km'\n        WHEN odometer BETWEEN 30000 AND 49999 THEN '30,000-50,000 km'\n        WHEN odometer BETWEEN 50000 AND 99999 THEN '50,000-100,000 km'\n        WHEN odometer >= 100000 THEN '100,000+ km'\n        ELSE 'Unknown'\n    END AS odometer_range,\n    COUNT(*) AS 'Número de Vendas'\nFROM\n    car_prices\nGROUP BY\n    odometer_range\nORDER BY\n    FIELD(odometer_range, '0-10,000 km', '10,000-30,000 km', '30,000-50,000 km', '50,000-100,000 km', '100,000+ km');\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Distribuição de Odometer",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "description": "Comparar o número de vendas e os preços médios para diferentes tipos de corpo",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "short"
        },
        "overrides": [
          {
            "matcher": {
              "id": "byName",
              "options": "numero_de_vendas"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Número de Vendas"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 59
      },
      "id": 16,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "never",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 100
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    LOWER(body) AS body_type, -- Converte o tipo de corpo para minúsculas\n    COUNT(*) AS numero_de_vendas,\n    AVG(sellingprice) AS 'Média de Preços'\nFROM\n    car_prices\nGROUP BY\n    LOWER(body) -- Agrupa por tipo de corpo convertido para minúsculas\nORDER BY\n    numero_de_vendas DESC; -- Ordena por número de vendas\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Comparação de Tipos de Corpo: Número de Vendas e Preços Médios",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "description": "Analisar a tendência de popularidade dos tipos de corpo ao longo do ano.",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "fieldMinMax": false,
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byName",
              "options": "body_type"
            },
            "properties": [
              {
                "id": "custom.axisPlacement",
                "value": "auto"
              },
              {
                "id": "custom.axisLabel",
                "value": "Tipo de Carroceria"
              }
            ]
          },
          {
            "matcher": {
              "id": "byName",
              "options": "body_type"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Carroceria"
              }
            ]
          },
          {
            "matcher": {
              "id": "byName",
              "options": "year"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Ano"
              }
            ]
          },
          {
            "matcher": {
              "id": "byName",
              "options": "number_of_sales"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Número de Vendas"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 59
      },
      "id": 17,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "auto",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 200
      },
      "pluginVersion": "11.1.3",
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    LOWER(body) AS body_type, -- Converte o tipo de corpo para minúsculas\n    DATE_FORMAT(saledate, '%Y') AS year, -- Formata a data para ano\n    COUNT(*) AS number_of_sales\nFROM\n    car_prices\nGROUP BY\n    LOWER(body), -- Agrupa por tipo de corpo convertido para minúsculas\n    DATE_FORMAT(saledate, '%Y') -- Agrupa por ano\nORDER BY\n    year;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Tendência de Tipos de Carroceria ao Longo do Ano",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "description": "Comparação de Vendas: Compare o número de vendas e os preços médios para veículos com diferentes tipos de transmissão (manual vs automático).",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "short"
        },
        "overrides": [
          {
            "matcher": {
              "id": "byName",
              "options": "number_of_sales"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Número de Vendas"
              }
            ]
          },
          {
            "matcher": {
              "id": "byName",
              "options": "average_price"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Média de Preços"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 9,
        "w": 5,
        "x": 0,
        "y": 67
      },
      "id": 18,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "never",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 0
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    LOWER(transmission) AS transmission_type, -- Converte o tipo de transmissão para minúsculas\n    COUNT(*) AS number_of_sales, -- Conta o número de vendas\n    AVG(sellingprice) AS average_price -- Calcula o preço médio\nFROM\n    car_prices\nGROUP BY\n    LOWER(transmission) -- Agrupa por tipo de transmissão convertido para minúsculas\nORDER BY\n    number_of_sales DESC; -- Ordena por número de vendas\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Análise de Vendas por Tipo de Transmissão",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "description": "Variações sazonais na popularidade das cores durante os anos.",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "short"
        },
        "overrides": [
          {
            "matcher": {
              "id": "byName",
              "options": "year"
            },
            "properties": [
              {
                "id": "unit",
                "value": "none"
              }
            ]
          },
          {
            "matcher": {
              "id": "byName",
              "options": "number_of_sales"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Número de Vendas"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 9,
        "w": 10,
        "x": 5,
        "y": 67
      },
      "id": 20,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "never",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 100
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    LOWER(color) AS vehicle_color, -- Converte a cor para minúsculas\n    DATE_FORMAT(saledate, '%Y') AS year, -- Formata a data para ano\n    COUNT(*) AS number_of_sales\nFROM\n    car_prices\nGROUP BY\n    LOWER(color), -- Agrupa por cor convertida para minúsculas\n    DATE_FORMAT(saledate, '%Y') -- Agrupa por ano\nORDER BY\n    year;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Tendência de Cores (Ano)",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "description": "Distribuição de Vendas por Cor: Analise qual cor de veículo é mais popular e qual tem o preço médio mais alto.",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "short"
        },
        "overrides": [
          {
            "matcher": {
              "id": "byName",
              "options": "number_of_sales"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Número de Vendas"
              }
            ]
          },
          {
            "matcher": {
              "id": "byName",
              "options": "average_price"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Média de Preços"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 9,
        "w": 9,
        "x": 15,
        "y": 67
      },
      "id": 19,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "never",
        "stacking": "normal",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 0
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    LOWER(color) AS vehicle_color, -- Converte a cor para minúsculas\n    COUNT(*) AS number_of_sales, -- Conta o número de vendas\n    AVG(sellingprice) AS average_price -- Calcula o preço médio\nFROM\n    car_prices\nGROUP BY\n    LOWER(color) -- Agrupa por cor convertida para minúsculas\nORDER BY\n    number_of_sales DESC; -- Ordena por número de vendas\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Análise de Vendas por Cor",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "short"
        },
        "overrides": [
          {
            "matcher": {
              "id": "byName",
              "options": "number_of_sales"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Número de Vendas"
              }
            ]
          },
          {
            "matcher": {
              "id": "byName",
              "options": "average_price"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Média de Preços"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 76
      },
      "id": 21,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "never",
        "stacking": "normal",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 0
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    LOWER(interior) AS interior_color, -- Converte a cor para minúsculas\n    COUNT(*) AS number_of_sales, -- Conta o número de vendas\n    AVG(sellingprice) AS average_price -- Calcula o preço médio\nFROM\n    car_prices\nGROUP BY\n    LOWER(interior) -- Agrupa por cor convertida para minúsculas\nORDER BY\n    number_of_sales DESC; -- Ordena por número de vendas\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Distribuição de Vendas por Cor do Interior",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "mysql",
        "uid": "edtbek6ufinswb"
      },
      "description": "",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "short"
        },
        "overrides": [
          {
            "matcher": {
              "id": "byName",
              "options": "year"
            },
            "properties": [
              {
                "id": "unit",
                "value": "none"
              }
            ]
          },
          {
            "matcher": {
              "id": "byName",
              "options": "number_of_sales"
            },
            "properties": [
              {
                "id": "displayName",
                "value": "Número de Vendas"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 76
      },
      "id": 22,
      "options": {
        "barRadius": 0,
        "barWidth": 0.97,
        "fullHighlight": false,
        "groupWidth": 0.7,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "never",
        "stacking": "none",
        "tooltip": {
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 100
      },
      "targets": [
        {
          "dataset": "cars_sales",
          "datasource": {
            "type": "mysql",
            "uid": "edtbek6ufinswb"
          },
          "editorMode": "code",
          "format": "table",
          "rawQuery": true,
          "rawSql": "SELECT\n    LOWER(interior) AS interior_color, -- Converte a cor para minúsculas\n    DATE_FORMAT(saledate, '%Y') AS year, -- Formata a data para ano\n    COUNT(*) AS number_of_sales\nFROM\n    car_prices\nGROUP BY\n    LOWER(interior), -- Agrupa por cor convertida para minúsculas\n    DATE_FORMAT(saledate, '%Y') -- Agrupa por ano\nORDER BY\n year;\n",
          "refId": "A",
          "sql": {
            "columns": [
              {
                "parameters": [],
                "type": "function"
              }
            ],
            "groupBy": [
              {
                "property": {
                  "type": "string"
                },
                "type": "groupBy"
              }
            ],
            "limit": 50
          }
        }
      ],
      "title": "Tendência de Cores do Interior",
      "type": "barchart"
    }
  ],
  "refresh": "",
  "schemaVersion": 39,
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "2014-10-26T20:54:40.882Z",
    "to": "2015-06-22T17:17:51.411Z"
  },
  "timepicker": {},
  "timezone": "browser",
  "title": "Cars Prices",
  "uid": "bdtm1xgay6vpca",
  "version": 11,
  "weekStart": ""
}
```
## Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

---

Feito por Derek Willyan
