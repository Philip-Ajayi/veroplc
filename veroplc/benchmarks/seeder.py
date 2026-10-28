import json
from sqlalchemy.orm import Session
from veroplc.models.db_models import BenchmarkModel, InvariantTemplate
from veroplc.benchmarks.press_cell import PRESS_CELL_VULNERABLE_ST, PRESS_CELL_PATCHED_ST
from veroplc.benchmarks.chemical_reactor import CHEMICAL_REACTOR_LEGACY_ST, CHEMICAL_REACTOR_MIGRATED_FLAWED_ST
from veroplc.benchmarks.baggage_sorter import BAGGAGE_SORTER_FLAWED_ST

def seed_database(db: Session):
    # 1. Seed Templates
    if db.query(InvariantTemplate).count() == 0:
        templates = [
            InvariantTemplate(
                name="Actuator Mutual Exclusion",
                category="Safety",
                description="Guarantees two opposing physical actuators never energize at the same time.",
                expression_pattern="NOT ({var_a} AND {var_b})",
                parameters_schema=json.dumps(["var_a", "var_b"])
            ),
            InvariantTemplate(
                name="Emergency Stop Precedence",
                category="Safety",
                description="Guarantees actuators are immediately killed when E-Stop is active.",
                expression_pattern="NOT ({estop} AND {actuator})",
                parameters_schema=json.dumps(["estop", "actuator"])
            ),
            InvariantTemplate(
                name="Safe Door Interlock",
                category="Interlock",
                description="Hazardous motion requires guard safety circuit to be active.",
                expression_pattern="NOT ({motion} AND NOT {guard_switch})",
                parameters_schema=json.dumps(["motion", "guard_switch"])
            )
        ]
        db.add_all(templates)
        db.commit()

    # 2. Seed Benchmark Models
    if db.query(BenchmarkModel).count() == 0:
        b1 = BenchmarkModel(
            slug="stamping-press",
            name="500-Ton Hydraulic Stamping Press",
            description="High-speed automotive stamping press with unhandled limit-switch debounce race condition.",
            raw_code=PRESS_CELL_VULNERABLE_ST,
            patched_code=PRESS_CELL_PATCHED_ST,
            format="ST",
            default_invariant="NOT (Ram_Cylinder_Extend AND Loader_In_Die_Envelope)",
            expected_k=10
        )
        b2 = BenchmarkModel(
            slug="chemical-reactor",
            name="Chemical Exotherm Mixing Tank",
            description="Acid/Caustic reactor migration with priority inversion flaw causing dual chemical feeding.",
            raw_code=CHEMICAL_REACTOR_MIGRATED_FLAWED_ST,
            patched_code=CHEMICAL_REACTOR_LEGACY_ST,
            format="ST",
            default_invariant="NOT (Acid_Feed_Pump AND Caustic_Feed_Pump)",
            expected_k=10
        )
        b3 = BenchmarkModel(
            slug="baggage-sorter",
            name="Baggage Sorter Diverter Cell",
            description="Airport logistics sorting cell with an 8-cycle deep asynchronous race condition.",
            raw_code=BAGGAGE_SORTER_FLAWED_ST,
            patched_code=BAGGAGE_SORTER_FLAWED_ST,
            format="ST",
            default_invariant="NOT (Diverter_Arm_1 AND Diverter_Arm_2)",
            expected_k=12
        )
        db.add_all([b1, b2, b3])
        db.commit()
