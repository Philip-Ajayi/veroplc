import xml.etree.ElementTree as ET
from typing import List
from veroplc.parser.st_ast import POU, VarDeclaration, DataType
from veroplc.parser.st_parser import StructuredTextParser

class PLCOpenXMLParser:
    """
    Parses standard IEC 61131-10 PLCopen XML interchange documents.
    Extracts POU interfaces, variable sections, and Structured Text bodies.
    """
    def __init__(self):
        self.st_parser = StructuredTextParser()

    def parse_xml(self, xml_text: str) -> List[POU]:
        # Strip XML namespaces for uniform querying
        clean_xml = ET.fromstring(xml_text)
        for elem in clean_xml.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

        pous: List[POU] = []

        for pou_node in clean_xml.findall(".//pou"):
            pou_name = pou_node.attrib.get("name", "UnnamedPOU")
            pou_type = pou_node.attrib.get("pouType", "program").upper()

            # Extract variables
            variables: List[VarDeclaration] = []
            for sec_tag, sec_name in [
                ("localVars", "VAR"),
                ("inputVars", "VAR_INPUT"),
                ("outputVars", "VAR_OUTPUT"),
                ("tempVars", "VAR_TEMP")
            ]:
                for sec in pou_node.findall(f".//interface/{sec_tag}"):
                    for v in sec.findall("./variable"):
                        v_name = v.attrib.get("name")
                        type_elem = v.find("./type")
                        t_name = "BOOL"
                        if type_elem is not None and len(type_elem) > 0:
                            t_name = type_elem[0].tag.upper()
                        variables.append(VarDeclaration(name=v_name, var_type=DataType(t_name), section=sec_name))

            # Extract ST code body
            st_text = ""
            st_elem = pou_node.find(".//body/ST")
            if st_elem is not None:
                st_text = "".join(st_elem.itertext()).strip()

            if st_text:
                # Wrap extracted body in standard ST syntax for unified AST synthesis
                synthetic_st = f"PROGRAM {pou_name}\n"
                for v in variables:
                    synthetic_st += f"{v.name} : {v.var_type.name};\n"
                synthetic_st += f"{st_text}\nEND_PROGRAM"
                
                try:
                    parsed_pous = self.st_parser.parse(synthetic_st)
                    if parsed_pous:
                        pou_obj = parsed_pous[0]
                        pou_obj.variables = variables
                        pous.append(pou_obj)
                        continue
                except Exception:
                    pass

            # Fallback POU
            pous.append(POU(name=pou_name, pou_type=pou_type, variables=variables, body=[]))

        return pous
