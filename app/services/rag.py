from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from app.config import settings
from structlog import get_logger
import json
import pandas as pd
from typing import List

logger = get_logger()
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

async def setup_vector_store(properties: List[dict]):
    with open("transport_price_data.json", "r") as f:
        transport_data = json.load(f)
    documents = [f"{p['title']}: {p['location']}, {p['price']} ETB, {p['house_type']}, {p['bedrooms']} bedrooms, amenities: {', '.join(p['amenities'])}" for p in properties]
    transport_docs = [f"{t['source']} to {t['destination']}: {t['price']} ETB, {t['kilometer']} km" for t in transport_data]
    documents.extend(transport_docs)
    vectorstore = Chroma.from_texts(documents, embeddings, persist_directory="/persistent-storage/chroma_db")
    return vectorstore

async def retrieve_relevant_properties(vectorstore, query: str, k: int = 5):
    results = vectorstore.similarity_search(query, k=k)
    return [doc.metadata for doc in results]

async def save_tenant_profile(user_id: int, request: dict) -> int:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from app.models.tenant_profile import TenantProfile
    engine = create_async_engine(settings.DATABASE_URL)
    async with AsyncSession(engine) as db:
        profile = TenantProfile(
            user_id=user_id,
            job_school_location=request.job_school_location,
            salary=request.salary,
            house_type=request.house_type,
            family_size=request.family_size,
            preferred_amenities=request.preferred_amenities
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile.id
