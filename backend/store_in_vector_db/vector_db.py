import chromadb
from google import genai


from dotenv import load_dotenv
import os


load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY2')
# CHROMA_API_KEY = os.getenv('CHROMA_API_KEY')
# CHROMA_TENANT = os.getenv('CHROMA_TENANT')
# CHROMA_DB = os.getenv('CHROMA_DB')

# chroma_client = chromadb.CloudClient(
#     api_key=CHROMA_API_KEY,
#     tenant=CHROMA_TENANT,
#     database=CHROMA_DB
# )

chroma_client = chromadb.PersistentClient("/home/subhash/Desktop/float/subhash_chromadb")

collection = chroma_client.get_or_create_collection(name="documents")


def generate_embeddings(summary):

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=summary)

    return result.embeddings[0].values




def add_documents(documents, metadata, embeddings, float_id):
    collection.add(
        documents=[documents],
        metadatas=[metadata],
        embeddings=embeddings,
        ids=[float_id]
    )

    print(f"Data added successfully {float_id}", end="\n\n\n\n")


def query_documents(query, filters):
    if(filters == {}):
        results = collection.query(
        query_embeddings=generate_embeddings(query),
        )
    else:
        results = collection.query(
            query_embeddings=generate_embeddings(query),
            where=filters,
            n_results=100
        )
    # print("\n",results, end="\n\n")


    # need to add re-reranking here 


    return results


def all_docs():
    results = collection.get()

    print(results)


# print(all_docs())

# print("\n\n\n")

# query_documents("Retrieve ARGO float profiles and associated oceanographic data, specifically focusing on temperature (TEMP) parameter measurements to analyze trends, for floats operating or deployed within the Laccadive Sea region, with data recorded from March 1, 2019, onwards. Include details such as float IDs, WMO numbers, launch dates, mission durations, operating institutions, and specific CTD sensor types.")