from fastapi import APIRouter
from app.api.v1.routes import nlp, links, classify, attachment, aggregate, model_ops, pipeline

api_router = APIRouter()

api_router.include_router(nlp.router, tags=["NLP Analysis"])
api_router.include_router(links.router, tags=["Link Analysis"])
api_router.include_router(classify.router, tags=["Core Classifier"])
api_router.include_router(attachment.router, tags=["Attachment Scanner"])
api_router.include_router(aggregate.router, tags=["Score Aggregator"])
api_router.include_router(model_ops.router, tags=["Model Ops"])
api_router.include_router(pipeline.router, tags=["Pipeline Orchestrator"])

