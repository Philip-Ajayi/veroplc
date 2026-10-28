import pytest
from app.parser.st_parser import StructuredTextParser
from app.parser.plcopen_parser import PLCOpenXMLParser
from app.models.schemas import VariableRole, VariableType

SAMPLE_ST = """PROGRAM TestProg
  VAR_INPUT
    Button : BOOL;
  END_VAR
  VAR_OUTPUT
    Lamp : BOOL;
  END_VAR
  VAR
    Counter : INT;
  END_VAR

  IF Button THEN
    Lamp := TRUE;
  ELSE
    Lamp := FALSE;
  END_IF;
END_PROGRAM"""

def test_st_parser_extracts_ast():
    parser = StructuredTextParser()
    ast = parser.parse(SAMPLE_ST)
    assert ast.name == "TestProg"
    assert len(ast.variables) == 3
    assert len(ast.body) == 1

SAMPLE_PLCOPEN_XML = """<?xml version="1.0" encoding="utf-8"?>
<project xmlns="http://www.plcopen.org/xml/tc6_0201">
  <types><pous>
    <pou name="ElevatorControl" pouType="program">
      <interface>
        <inputVars>
          <variable name="Floor1_Sensor"><type><BOOL/></type></variable>
        </inputVars>
        <outputVars>
          <variable name="Motor_Up"><type><BOOL/></type></variable>
        </outputVars>
      </interface>
      <body>
        <ST><xhtml:p xmlns:xhtml="http://www.w3.org/1999/xhtml">
          IF Floor1_Sensor THEN Motor_Up := FALSE; END_IF;
        </xhtml:p></ST>
      </body>
    </pou>
  </pous></types>
</project>"""

def test_plcopen_xml_to_st_conversion():
    st_result = PLCOpenXMLParser.parse_xml_to_st(SAMPLE_PLCOPEN_XML)
    assert "PROGRAM ElevatorControl" in st_result
    assert "Floor1_Sensor : BOOL;" in st_result
    assert "Motor_Up : BOOL;" in st_result
