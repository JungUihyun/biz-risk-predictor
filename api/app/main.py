"""상권 폐업 위험도 진단 API (FastAPI).

실행 (api/ 디렉터리에서):
    uvicorn app.main:app --reload --port 8000
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .advice import build_advice
from .model import RiskModel

state: dict[str, RiskModel] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["model"] = RiskModel()
    yield
    state.clear()


app = FastAPI(title="Biz Risk Predictor API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/options")
def options():
    return state["model"].options


@app.get("/map")
def map_scores(industry_code: str = Query(..., min_length=8, max_length=8)):
    return state["model"].map_scores(industry_code)


@app.get("/diagnose")
def diagnose(
    dong_code: str = Query(..., min_length=8, max_length=10),
    industry_code: str = Query(..., min_length=8, max_length=8),
):
    result = state["model"].diagnose(dong_code, industry_code)
    if result is None:
        raise HTTPException(404, "해당 지역·업종 조합의 데이터가 없거나 점포 수가 너무 적습니다.")
    result["advice"] = build_advice(result["contributions"])
    return result
