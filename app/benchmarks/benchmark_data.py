from typing import List
from app.models.schemas import BenchmarkItem, InvariantDefinition, InvariantType

PRESS_STAMPING_FLAWED = """PROGRAM StampingPressCell
  VAR_INPUT
    Part_Present_Switch : BOOL;
    Sensor_Debounce_Glitch : BOOL;
    Emergency_Stop : BOOL;
  END_VAR
  VAR_OUTPUT
    Ram_Cylinder_Extend : BOOL;
    Ram_Cylinder_Retract : BOOL;
    Loader_In_Die_Envelope : BOOL;
  END_VAR
  VAR
    Loader_Moving_In : BOOL;
    Loader_Clear_Flag : BOOL;
    Cycle_Step : INT;
  END_VAR

  // Scan Logic
  IF Emergency_Stop THEN
    Ram_Cylinder_Extend := FALSE;
    Ram_Cylinder_Retract := TRUE;
    Loader_In_Die_Envelope := FALSE;
    Loader_Moving_In := FALSE;
  ELSE
    // Retooling sequence flaw: Debounce glitch asynchronously unlatches clear flag
    IF Sensor_Debounce_Glitch THEN
      Loader_Clear_Flag := TRUE;
    END_IF;

    IF Part_Present_Switch THEN
      Loader_Moving_In := TRUE;
      Loader_In_Die_Envelope := TRUE;
    END_IF;

    // VULNERABILITY: Ram extend check relies on Loader_Clear_Flag without verifying Loader_In_Die_Envelope
    IF Loader_Clear_Flag AND NOT Emergency_Stop THEN
      Ram_Cylinder_Extend := TRUE;
    ELSE
      Ram_Cylinder_Extend := FALSE;
    END_IF;
  END_IF;
END_PROGRAM"""

PRESS_STAMPING_PATCHED = """PROGRAM StampingPressCell
  VAR_INPUT
    Part_Present_Switch : BOOL;
    Sensor_Debounce_Glitch : BOOL;
    Emergency_Stop : BOOL;
  END_VAR
  VAR_OUTPUT
    Ram_Cylinder_Extend : BOOL;
    Ram_Cylinder_Retract : BOOL;
    Loader_In_Die_Envelope : BOOL;
  END_VAR
  VAR
    Loader_Moving_In : BOOL;
    Loader_Clear_Flag : BOOL;
    Cycle_Step : INT;
  END_VAR

  // Scan Logic
  IF Emergency_Stop THEN
    Ram_Cylinder_Extend := FALSE;
    Ram_Cylinder_Retract := TRUE;
    Loader_In_Die_Envelope := FALSE;
    Loader_Moving_In := FALSE;
    Loader_Clear_Flag := FALSE;
  ELSE
    IF Sensor_Debounce_Glitch THEN
      Loader_Clear_Flag := TRUE;
    END_IF;

    IF Part_Present_Switch THEN
      Loader_Moving_In := TRUE;
      Loader_In_Die_Envelope := TRUE;
      Loader_Clear_Flag := FALSE;
    END_IF;

    // REMEDIATED: Formal temporal interlock guarantees mutual exclusion
    IF Loader_Clear_Flag AND NOT Loader_In_Die_Envelope AND NOT Loader_Moving_In AND NOT Emergency_Stop THEN
      Ram_Cylinder_Extend := TRUE;
    ELSE
      Ram_Cylinder_Extend := FALSE;
    END_IF;
  END_IF;
END_PROGRAM"""

CHEMICAL_REACTOR_FLAWED = """PROGRAM ChemicalMixingTank
  VAR_INPUT
    Low_Level_Sensor : BOOL;
    High_Level_Sensor : BOOL;
    EStop_Reset_Pulse : BOOL;
    System_Halt : BOOL;
  END_VAR
  VAR_OUTPUT
    Acid_Feed_Pump : BOOL;
    Caustic_Feed_Pump : BOOL;
    Drain_Valve : BOOL;
  END_VAR
  VAR
    Reactivity_Lockout : BOOL;
  END_VAR

  // Migration logic flaw: Inverted rung priority permits dual acid-caustic feed
  IF System_Halt THEN
    Acid_Feed_Pump := FALSE;
    Caustic_Feed_Pump := FALSE;
    Drain_Valve := TRUE;
  ELSE
    IF EStop_Reset_Pulse THEN
      Reactivity_Lockout := FALSE;
    END_IF;

    IF Low_Level_Sensor THEN
      Acid_Feed_Pump := TRUE;
    END_IF;

    // VULNERABILITY: Rung allows simultaneous feed during unlatched lockout
    IF NOT Reactivity_Lockout AND NOT High_Level_Sensor THEN
      Caustic_Feed_Pump := TRUE;
    ELSE
      Caustic_Feed_Pump := FALSE;
    END_IF;
  END_IF;
END_PROGRAM"""

CHEMICAL_REACTOR_PATCHED = """PROGRAM ChemicalMixingTank
  VAR_INPUT
    Low_Level_Sensor : BOOL;
    High_Level_Sensor : BOOL;
    EStop_Reset_Pulse : BOOL;
    System_Halt : BOOL;
  END_VAR
  VAR_OUTPUT
    Acid_Feed_Pump : BOOL;
    Caustic_Feed_Pump : BOOL;
    Drain_Valve : BOOL;
  END_VAR
  VAR
    Reactivity_Lockout : BOOL;
  END_VAR

  IF System_Halt THEN
    Acid_Feed_Pump := FALSE;
    Caustic_Feed_Pump := FALSE;
    Drain_Valve := TRUE;
  ELSE
    IF EStop_Reset_Pulse THEN
      Reactivity_Lockout := TRUE;
    END_IF;

    IF Low_Level_Sensor AND NOT Caustic_Feed_Pump THEN
      Acid_Feed_Pump := TRUE;
      Reactivity_Lockout := TRUE;
    ELSE
      Acid_Feed_Pump := FALSE;
    END_IF;

    // REMEDIATED: Rigorous mutual exclusion interlock
    IF NOT Reactivity_Lockout AND NOT High_Level_Sensor AND NOT Acid_Feed_Pump THEN
      Caustic_Feed_Pump := TRUE;
    ELSE
      Caustic_Feed_Pump := FALSE;
    END_IF;
  END_IF;
END_PROGRAM"""

BAGGAGE_SORTER_FLAWED = """PROGRAM BaggageHandlingSorter
  VAR_INPUT
    PhotoEye_1 : BOOL;
    PhotoEye_2 : BOOL;
    Jam_Reset_Pulse : BOOL;
  END_VAR
  VAR_OUTPUT
    Diverter_Arm_1 : BOOL;
    Diverter_Arm_2 : BOOL;
  END_VAR
  VAR
    Diverter_1_Active : BOOL;
    Diverter_2_Active : BOOL;
  END_VAR

  // Sorter clash race condition
  IF Jam_Reset_Pulse THEN
    Diverter_1_Active := FALSE;
    Diverter_2_Active := TRUE;
  END_IF;

  IF PhotoEye_1 THEN
    Diverter_1_Active := TRUE;
  END_IF;

  IF PhotoEye_2 AND NOT Jam_Reset_Pulse THEN
    Diverter_2_Active := TRUE;
  END_IF;

  Diverter_Arm_1 := Diverter_1_Active;
  Diverter_Arm_2 := Diverter_2_Active;
END_PROGRAM"""

BAGGAGE_SORTER_PATCHED = """PROGRAM BaggageHandlingSorter
  VAR_INPUT
    PhotoEye_1 : BOOL;
    PhotoEye_2 : BOOL;
    Jam_Reset_Pulse : BOOL;
  END_VAR
  VAR_OUTPUT
    Diverter_Arm_1 : BOOL;
    Diverter_Arm_2 : BOOL;
  END_VAR
  VAR
    Diverter_1_Active : BOOL;
    Diverter_2_Active : BOOL;
  END_VAR

  IF Jam_Reset_Pulse THEN
    Diverter_1_Active := FALSE;
    Diverter_2_Active := FALSE;
  ELSE
    IF PhotoEye_1 AND NOT Diverter_2_Active THEN
      Diverter_1_Active := TRUE;
    ELSE
      Diverter_1_Active := FALSE;
    END_IF;

    IF PhotoEye_2 AND NOT Diverter_1_Active THEN
      Diverter_2_Active := TRUE;
    ELSE
      Diverter_2_Active := FALSE;
    END_IF;
  END_IF;

  Diverter_Arm_1 := Diverter_1_Active;
  Diverter_Arm_2 := Diverter_2_Active;
END_PROGRAM"""

BENCHMARK_SUITE: List[BenchmarkItem] = [
    BenchmarkItem(
        id="hydraulic_press",
        title="500-Ton Hydraulic Stamping Press",
        industry="Automotive Stamping Cell",
        description="Asynchronous sensor debounce overlap triggers ram cylinder extension while transfer carriage is inside die envelope.",
        structured_text=PRESS_STAMPING_FLAWED,
        patched_structured_text=PRESS_STAMPING_PATCHED,
        recommended_invariants=[
            InvariantDefinition(
                name="Actuator Mutual Exclusion",
                invariant_type=InvariantType.MUTUAL_EXCLUSION,
                expression="NEVER: Ram_Cylinder_Extend == TRUE AND Loader_In_Die_Envelope == TRUE",
                description="The hydraulic ram solenoid and loader transfer arm must never occupy the die cavity simultaneously."
            )
        ],
        cycle_bound=10
    ),
    BenchmarkItem(
        id="chemical_reactor",
        title="Chemical Exotherm Reactor Dual-Feed",
        industry="Chemical Processing",
        description="Brownfield migration bug: inverted IF execution priority energizes acid and caustic pumps concurrently following E-Stop reset.",
        structured_text=CHEMICAL_REACTOR_FLAWED,
        patched_structured_text=CHEMICAL_REACTOR_PATCHED,
        recommended_invariants=[
            InvariantDefinition(
                name="Dual-Feed Isolation",
                invariant_type=InvariantType.MUTUAL_EXCLUSION,
                expression="NEVER: Acid_Feed_Pump == TRUE AND Caustic_Feed_Pump == TRUE",
                description="Acid and caustic feed pumps must never be energized together under any condition to prevent runaway exotherm."
            )
        ],
        cycle_bound=12
    ),
    BenchmarkItem(
        id="baggage_sorter",
        title="High-Speed Baggage Diverter Line",
        industry="Airport Logistics",
        description="Asynchronous jam timer reset pulse collides with photo-eye flag, forcing twin diverters to extend into each other.",
        structured_text=BAGGAGE_SORTER_FLAWED,
        patched_structured_text=BAGGAGE_SORTER_PATCHED,
        recommended_invariants=[
            InvariantDefinition(
                name="Diverter Arm Clash Precedence",
                invariant_type=InvariantType.MUTUAL_EXCLUSION,
                expression="NEVER: Diverter_Arm_1 == TRUE AND Diverter_Arm_2 == TRUE",
                description="Both high-speed pneumatic diverter paddles must never cross paths concurrently."
            )
        ],
        cycle_bound=10
    )
]
