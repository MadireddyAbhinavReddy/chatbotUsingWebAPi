from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
import pandas as pd


DB_URL = os.getenv('DB_URL')
engine = create_engine(DB_URL)


def retrieve_data_from_postgres(sql_query):
    with engine.connect() as conn:
        df = pd.read_sql(sql_query, conn)

        return df
