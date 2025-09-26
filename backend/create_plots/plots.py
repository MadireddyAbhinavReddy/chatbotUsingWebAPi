import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import aiofiles

# Static folder path
STATIC_PATH = 'static/plots/'
os.makedirs(STATIC_PATH, exist_ok=True)

async def create_csv_async(data):

    file_name = 'userId|chatId|questionHash.csv'
    filepath = os.path.join(STATIC_PATH, file_name)

    df = pd.DataFrame(data)
    
    # Write CSV asynchronously
    async with aiofiles.open(filepath, mode='w', encoding='utf-8') as f:
        # Write header
        await f.write(",".join(df.columns) + "\n")
        # Write each row
        for row in df.itertuples(index=False):
            await f.write(",".join(str(x) for x in row) + "\n")

    return filepath
