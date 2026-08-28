from fastapi import APIRouter, status
from app.schemas.links import LinkExtractRequest, LinkExtractResponse
from app.ml.link_engine import link_engine

router = APIRouter()

@router.post("/links/extract-and-score", response_model=LinkExtractResponse, status_code=status.HTTP_200_OK)
async def extract_and_score_links(payload: LinkExtractRequest):
    """
    Extracts all links from HTML body, analyzes obfuscation, IP literal hosts,
    shorteners, mismatched text/href, and assigns risk scores.
    """
    links = link_engine.extract_and_score(body_html=payload.body_html)
    return LinkExtractResponse(links=links)

