import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from veroplc.models.database import engine, Base, get_db
from veroplc.models.db_models import VerificationAudit, BenchmarkModel, InvariantTemplate
from veroplc.models.api_schemas import (
    VerificationRequest, VerificationResponse, SimulationStepRequest,
    SimulationStepResponse, BenchmarkSummary
)
from veroplc.parser.st_parser import StructuredTextParser
from veroplc.parser.plcopen_parser import PLCOpenXMLParser
from veroplc.engine.solver import BoundedModelChecker
from veroplc.simulator.plant_simulator import ConcreteScanCycleSimulator
from veroplc.benchmarks.seeder import seed_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables and benchmarks
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    seed_database(db)
    yield

app = FastAPI(
    title="VeroPLC Automated Formal Verifier",
    description="Bounded SMT Model Checking & Scan-Cycle Invariant Verifier for IEC 61131-3 Industrial Systems",
    version="1.0.0",
    lifespan=lifespan
)

# Static assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def get_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "VeroPLC Verification Engine", "z3": "active"}

@app.get("/api/benchmarks", response_model=list[BenchmarkSummary])
def list_benchmarks(db: Session = Depends(get_db)):
    return db.query(BenchmarkModel).all()

@app.get("/api/benchmarks/{slug}", response_model=BenchmarkSummary)
def get_benchmark(slug: str, db: Session = Depends(get_db)):
    bm = db.query(BenchmarkModel).filter(BenchmarkModel.slug == slug).first()
    if not bm:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return bm

@app.post("/api/verify", response_model=VerificationResponse)
def verify_code(req: VerificationRequest, db: Session = Depends(get_db)):
    try:
        # Ingest ST or PLCopen XML
        if req.code_format == "XML" or "<project" in req.code:
            pous = PLCOpenXMLParser().parse_xml(req.code)
        else:
            pous = StructuredTextParser().parse(req.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Structured Text / XML Parse Error: {str(e)}")

    if not pous:
        raise HTTPException(status_code=400, detail="No valid Program Organization Units (POUs) found in source.")

    checker = BoundedModelChecker(pous)
    invariants_dicts = [inv.model_dump() for inv in req.invariants]

    res = checker.verify(
        invariants=invariants_dicts,
        k_max=req.k_max,
        timeout_ms=int(req.timeout_seconds * 1000)
    )

    # Persist audit record
    audit = VerificationAudit(
        source_type=req.code_format,
        k_bound=req.k_max,
        status=res.status,
        violating_cycle=res.violating_cycle,
        solve_time_seconds=res.time_seconds,
        clauses_count=res.clauses_count,
        variables_count=res.variables_count,
        invariant_expression=invariants_dicts[0]["expression"] if invariants_dicts else "",
        counterexample_json=res.counterexample.model_dump_json() if res.counterexample else None,
        source_code=req.code
    )
    db.add(audit)
    db.commit()
    res.audit_id = audit.id

    return res

@app.post("/api/simulate/step", response_model=SimulationStepResponse)
def simulate_cycle(req: SimulationStepRequest):
    try:
        pous = StructuredTextParser().parse(req.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Syntax Error: {str(e)}")

    sim = ConcreteScanCycleSimulator(pous[0])
    sim.state = req.current_state
    next_state = sim.execute_cycle(req.inputs)

    # Segregate outputs
    outputs = {k: v for k, v in next_state.items() if any(p.name == k and p.section == "VAR_OUTPUT" for p in pous[0].variables)}

    return SimulationStepResponse(
        next_state=next_state,
        outputs=outputs,
        execution_log=[f"Processed discrete scan cycle with inputs {req.inputs}"]
    )