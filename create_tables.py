import os

from dotenv import load_dotenv

from db_connector import DbConnector, DB
from tables import TABLES


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


if __name__ == '__main__':
    conn = DbConnector(**DB)
    conn.open_connection()
    conn.create_database(os.environ.get('DB_NAME'))
    conn.create_tables(**TABLES)
    conn.close_connection()