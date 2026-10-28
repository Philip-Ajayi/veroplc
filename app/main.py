from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List
import os

from app.core.config import settings
from app.models.schemas import VerifyRequest, VerifyResponse, BenchmarkItem
from app.parser.st_parser import StructuredTextParser
from app.parser.plcopen_parser import PLCOpenXMLParser
from app.verifier.smt_engine import BoundedSMTVerifier
from app.benchmarks.benchmark_data import BENCHMARK_SUITE

app = FastAPI(
    title=settings.APP_NAME,
    description="Automated Bounded SMT Model Checking and Scan-Cycle Invariant Verifier for IEC 61131-3 Industrial Control Systems",
    version="1.0.0"
)

# FIXED: Standard FastAPI CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "VeroPLC verification engine running. Access /docs for Swagger API."}

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "solver": "Microsoft Z3 SMT Solver v4.13.0",
        "air_gapped_mode": True
    }

@app.get("/api/benchmarks", response_model=List[BenchmarkItem])
async def list_benchmarks():
    return BENCHMARK_SUITE

@app.post("/api/parse/xml")
async def parse_plcopen_xml(file: UploadFile = File(...)):
    """Upload PLCopen XML and receive extracted Structured Text."""
    try:
        content = await file.read()
        st_code = PLCOpenXMLParser.parse_xml_to_st(content.decode("utf-8"))
        return {"structured_text": st_code, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PLCopen XML: {str(e)}")

@app.post("/api/verify", response_model=VerifyResponse)
async def verify_logic(request: VerifyRequest):
    """Executes Bounded SMT Model Checking using Z3 over discrete cyclic scan transitions."""
    try:
        st_parser = StructuredTextParser()
        ast = st_parser.parse(request.structured_text)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Structured Text Syntax Error: {str(e)}")

    try:
        verifier = BoundedSMTVerifier(ast, cycle_time_ms=request.cycle_time_ms)
        response = verifier.verify(request.invariants, max_cycles=request.unroll_cycles)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification Engine Error: {str(e)}")
