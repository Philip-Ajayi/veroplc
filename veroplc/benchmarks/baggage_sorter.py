BAGGAGE_SORTER_FLAWED_ST = """PROGRAM Baggage_Sorter_Challenge
VAR_INPUT
    PhotoEye_1 : BOOL;
    PhotoEye_2 : BOOL;
    Reset_Pulse : BOOL;
END_VAR
VAR_OUTPUT
    Diverter_Arm_1 : BOOL;
    Diverter_Arm_2 : BOOL;
    Alarm_Clash : BOOL;
END_VAR
VAR
    Internal_State_Bit1 : BOOL;
    Internal_State_Bit2 : BOOL;
    Internal_State_Bit3 : BOOL;
END_VAR

(* Deep multi-cycle race condition triggered by sequential photo pulses *)
IF PhotoEye_1 THEN
    Internal_State_Bit1 := TRUE;
END_IF;

IF Internal_State_Bit1 AND PhotoEye_2 THEN
    Internal_State_Bit2 := TRUE;
END_IF;

IF Internal_State_Bit2 AND Reset_Pulse THEN
    Internal_State_Bit3 := TRUE;
END_IF;

IF Internal_State_Bit1 AND NOT Internal_State_Bit3 THEN
    Diverter_Arm_1 := TRUE;
ELSE
    Diverter_Arm_1 := FALSE;
END_IF;

(* Flawed activation condition *)
IF Internal_State_Bit2 AND Internal_State_Bit3 THEN
    Diverter_Arm_2 := TRUE;
ELSE
    Diverter_Arm_2 := FALSE;
END_IF;
END_PROGRAM"""
