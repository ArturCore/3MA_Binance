from azure.data.tables import TableServiceClient
import os
import datetime
from datetime import datetime, timedelta, timezone

# Запускаємо стратегію
def handle(data):
    data = main(data)
    return data

def get_depth_data(service_client, table_name, minutes_ago):
  table_client = service_client.get_table_client(table_name)

  # Query data for date
  now_utc = datetime.now(timezone.utc)
  rounded = now_utc.replace(second=0, microsecond=0)
  start_time = rounded - timedelta(minutes=minutes_ago)
  start_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
  query_filter = f"Timestamp ge datetime'{start_time}' "

  entities = table_client.query_entities(query_filter)
  data = list(entities)
  return data

def get_data(conn_string, table_name1, table_name2, minutes_ago):
  service_client = TableServiceClient.from_connection_string(conn_string)
  table1 = get_depth_data(service_client, table_name1, minutes_ago)
  table2 = get_depth_data(service_client, table_name2, minutes_ago)
  return table1, table2 


# Головна функція для стратегії
def main(data):
    try:
        result = {}

        table1, table2 = get_data(data['conn_string'], data['table_name1'], data['table_name2'], data['minutes_ago'])

        result['table1'] = table1
        result['table2'] = table2

        data['result'] = result
        return data

    except Exception as e:
        data['result'] = str(e)
        return data


