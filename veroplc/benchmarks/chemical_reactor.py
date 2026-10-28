CHEMICAL_REACTOR_LEGACY_ST = """PROGRAM Chemical_Reactor_V1
VAR_INPUT
    EStop_Active : BOOL;
    Tank_Level_High : BOOL;
    Acid_Demand : BOOL;
    Caustic_Demand : BOOL;
END_VAR
VAR_OUTPUT
    Acid_Feed_Pump : BOOL;
    Caustic_Feed_Pump : BOOL;
    Emergency_Dump_Valve : BOOL;
END_VAR
VAR
    Feed_Interlock : BOOL;
END_VAR

IF EStop_Active THEN
    Emergency_Dump_Valve := TRUE;
    Acid_Feed_Pump := FALSE;
    Caustic_Feed_Pump := FALSE;
ELSE
    Emergency_Dump_Valve := FALSE;
    IF Acid_Demand AND NOT Caustic_Demand THEN
        Acid_Feed_Pump := TRUE;
        Caustic_Feed_Pump := FALSE;
    ELSE
        IF Caustic_Demand AND NOT Acid_Demand THEN
            Caustic_Feed_Pump := TRUE;
            Acid_Feed_Pump := FALSE;
        ELSE
            Acid_Feed_Pump := FALSE;
            Caustic_Feed_Pump := FALSE;
        END_IF;
    END_IF;
END_IF;
END_PROGRAM"""

CHEMICAL_REACTOR_MIGRATED_FLAWED_ST = """PROGRAM Chemical_Reactor_V2
VAR_INPUT
    EStop_Active : BOOL;
    Tank_Level_High : BOOL;
    Acid_Demand : BOOL;
    Caustic_Demand : BOOL;
END_VAR
VAR_OUTPUT
    Acid_Feed_Pump : BOOL;
    Caustic_Feed_Pump : BOOL;
    Emergency_Dump_Valve : BOOL;
END_VAR
VAR
    Feed_Interlock : BOOL;
END_VAR

(* REGRESSION: Inverted priority check allows dual feeding during demand reset *)
IF EStop_Active THEN
    Emergency_Dump_Valve := TRUE;
ELSE
    Emergency_Dump_Valve := FALSE;
END_IF;

IF Acid_Demand THEN
    Acid_Feed_Pump := TRUE;
ELSE
    Acid_Feed_Pump := FALSE;
END_IF;

(* Flaw: Evaluated independently without mutual lock! *)
IF Caustic_Demand THEN
    Caustic_Feed_Pump := TRUE;
ELSE
    Caustic_Feed_Pump := FALSE;
END_IF;
END_PROGRAM"""
