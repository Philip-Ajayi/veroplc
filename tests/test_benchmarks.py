import pytest
from app.parser.st_parser import StructuredTextParser
from app.verifier.smt_engine import BoundedSMTVerifier
from app.benchmarks.benchmark_data import BENCHMARK_SUITE
from app.models.schemas import VerificationStatus

@pytest.mark.parametrize("benchmark", BENCHMARK_SUITE)
def test_industrial_benchmarks_fail_then_pass_when_patched(benchmark):
    parser = StructuredTextParser()

    # 1. Flawed version MUST trigger SAT (Violation detected)
    flawed_ast = parser.parse(benchmark.structured_text)
    verifier_flawed = BoundedSMTVerifier(flawed_ast, cycle_time_ms=20)
    res_flawed = verifier_flawed.verify(benchmark.recommended_invariants, max_cycles=benchmark.cycle_bound)
    assert res_flawed.status == VerificationStatus.SAT, f"Benchmark {benchmark.id} failed to catch injected bug"

    # 2. Patched version MUST return UNSAT (Proven mathematically safe)
    patched_ast = parser.parse(benchmark.patched_structured_text)
    verifier_patched = BoundedSMTVerifier(patched_ast, cycle_time_ms=20)
    res_patched = verifier_patched.verify(benchmark.recommended_invariants, max_cycles=benchmark.cycle_bound)
    assert res_patched.status == VerificationStatus.UNSAT, f"Benchmark {benchmark.id} patch failed verification"
    assert res_patched.certificate is not None
