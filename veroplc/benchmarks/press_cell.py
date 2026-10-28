PRESS_CELL_VULNERABLE_ST = """PROGRAM Press_Cell_Line3
VAR_INPUT
    Part_Present_Switch : BOOL;
    Loader_In_Die_Envelope : BOOL;
    Sensor_Debounce_Glitch : BOOL;
    Safety_Curtain_Clear : BOOL;
END_VAR
VAR_OUTPUT
    Ram_Cylinder_Extend : BOOL;
    Loader_Motor_Advance : BOOL;
    Press_Safe_To_Fire : BOOL;
END_VAR
VAR
    Interlock_Latch : BOOL;
    Cycle_Step : INT;
END_VAR

(* Actuator Sequence Logic *)
IF Sensor_Debounce_Glitch THEN
    Interlock_Latch := FALSE;
END_IF;

IF Part_Present_Switch AND Safety_Curtain_Clear THEN
    Loader_Motor_Advance := TRUE;
ELSE
    Loader_Motor_Advance := FALSE;
END_IF;

(* VULNERABILITY: Missing temporal lock; debounce resets safety flag early *)
IF NOT Interlock_Latch AND Part_Present_Switch THEN
    Press_Safe_To_Fire := TRUE;
ELSE
    Press_Safe_To_Fire := FALSE;
END_IF;

IF Press_Safe_To_Fire AND NOT Sensor_Debounce_Glitch THEN
    Ram_Cylinder_Extend := TRUE;
ELSE
    Ram_Cylinder_Extend := FALSE;
END_IF;
END_PROGRAM"""

PRESS_CELL_PATCHED_ST = """PROGRAM Press_Cell_Line3
VAR_INPUT
    Part_Present_Switch : BOOL;
    Loader_In_Die_Envelope : BOOL;
    Sensor_Debounce_Glitch : BOOL;
    Safety_Curtain_Clear : BOOL;
END_VAR
VAR_OUTPUT
    Ram_Cylinder_Extend : BOOL;
    Loader_Motor_Advance : BOOL;
    Press_Safe_To_Fire : BOOL;
END_VAR
VAR
    Interlock_Latch : BOOL;
    Cycle_Step : INT;
END_VAR

(* Actuator Sequence Logic with strict physical mutual exclusion *)
IF Loader_In_Die_Envelope THEN
    Interlock_Latch := TRUE;
END_IF;

IF Safety_Curtain_Clear AND NOT Loader_In_Die_Envelope THEN
    Interlock_Latch := FALSE;
END_IF;

IF Part_Present_Switch AND Safety_Curtain_Clear AND NOT Loader_In_Die_Envelope THEN
    Loader_Motor_Advance := TRUE;
ELSE
    Loader_Motor_Advance := FALSE;
END_IF;

(* PATCHED: Ram can strictly NEVER fire while Loader is within die envelope *)
IF Part_Present_Switch AND Safety_Curtain_Clear AND NOT Loader_In_Die_Envelope AND NOT Interlock_Latch THEN
    Press_Safe_To_Fire := TRUE;
ELSE
    Press_Safe_To_Fire := FALSE;
END_IF;

IF Press_Safe_To_Fire AND NOT Loader_In_Die_Envelope THEN
    Ram_Cylinder_Extend := TRUE;
ELSE
    Ram_Cylinder_Extend := FALSE;
END_IF;
END_PROGRAM"""
