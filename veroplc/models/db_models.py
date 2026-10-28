import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from veroplc.models.database import Base

class VerificationAudit(Base):
    __tablename__ = "verification_audits"

    id = Column(Integer, primary_key=True, index=True)
    benchmark_name = Column(String(128), default="Custom")
    source_type = Column(String(32), default="ST")  # "ST" or "PLCOPEN_XML"
    k_bound = Column(Integer, nullable=False)
    status = Column(String(32), nullable=False)  # "SAT" (violation), "UNSAT" (safe), "ERROR", "TIMEOUT"
    violating_cycle = Column(Integer, nullable=True)
    solve_time_seconds = Column(Float, nullable=False)
    clauses_count = Column(Integer, default=0)
    variables_count = Column(Integer, default=0)
    invariant_expression = Column(Text, nullable=False)
    counterexample_json = Column(Text, nullable=True)
    source_code = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class InvariantTemplate(Base):
    __tablename__ = "invariant_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)
    category = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    expression_pattern = Column(Text, nullable=False)
    parameters_schema = Column(Text, nullable=False)

class BenchmarkModel(Base):
    __tablename__ = "benchmark_models"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    raw_code = Column(Text, nullable=False)
    patched_code = Column(Text, nullable=False)
    format = Column(String(16), default="ST")  # "ST" or "XML"
    default_invariant = Column(Text, nullable=False)
    expected_k = Column(Integer, default=10)
