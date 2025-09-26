from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
import pandas as pd

# Load .env
load_dotenv()  # <-- this is needed here
DB_URL = os.getenv('DB_URL')

if not DB_URL:
    raise ValueError("DB_URL is not set. Please check your .env file.")

engine = create_engine(DB_URL)


def retrieve_data_from_postgres(sql_query: str) -> pd.DataFrame:
    with engine.connect() as conn:
        df = pd.read_sql(sql_query, conn)
    return df
