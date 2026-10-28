import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from app.models.schemas import VariableDeclaration, VariableRole, VariableType

class PLCOpenXMLParser:
    """Ingests IEC 61131-10 PLCopen XML schemas and converts POUs to Structured Text."""

    NAMESPACES = {
        'plc': 'http://www.plcopen.org/xml/tc6_0201',
        'xhtml': 'http://www.w3.org/1999/xhtml'
    }

    @classmethod
    def parse_xml_to_st(cls, xml_content: str) -> str:
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid PLCopen XML document: {str(e)}")

        # Find first Program POU
        pous = root.findall('.//{*}pou')
        if not pous:
            pous = root.findall('.//pou')

        if not pous:
            raise ValueError("No Program Organization Units (POUs) found in PLCopen XML")

        pou = pous[0]
        pou_name = pou.attrib.get('name', 'PLC_PRG')

        var_blocks: Dict[VariableRole, List[VariableDeclaration]] = {
            VariableRole.INPUT: [],
            VariableRole.OUTPUT: [],
            VariableRole.INTERNAL: []
        }

        # Extract Variables
        interface = pou.find('{*}interface')
        if interface is None:
            interface = pou.find('interface')

        if interface is not None:
            for child in interface:
                tag = child.tag.split('}')[-1]
                role = None
                if tag == 'inputVars':
                    role = VariableRole.INPUT
                elif tag == 'outputVars':
                    role = VariableRole.OUTPUT
                elif tag == 'localVars':
                    role = VariableRole.INTERNAL

                if role:
                    for var_elem in child.findall('{*}variable') or child.findall('variable'):
                        v_name = var_elem.attrib.get('name')
                        type_elem = var_elem.find('{*}type') or var_elem.find('type')
                        v_type = VariableType.BOOL
                        if type_elem is not None and len(type_elem) > 0:
                            t_tag = type_elem[0].tag.split('}')[-1].upper()
                            if "INT" in t_tag:
                                v_type = VariableType.INT
                            elif "TIME" in t_tag:
                                v_type = VariableType.TIME

                        init_val = False if v_type == VariableType.BOOL else 0
                        var_blocks[role].append(
                            VariableDeclaration(name=v_name, var_type=v_type, role=role, initial_value=init_val)
                        )

        # Extract Body ST
        body_elem = pou.find('{*}body') or pou.find('body')
        st_content = ""
        if body_elem is not None:
            st_elem = body_elem.find('{*}ST') or body_elem.find('ST')
            if st_elem is not None:
                xhtml_p = st_elem.find('{*}p') or st_elem.find('p')
                if xhtml_p is not None and xhtml_p.text:
                    st_content = xhtml_p.text
                elif st_elem.text:
                    st_content = st_elem.text

        # Synthesize Structured Text representation
        st_lines = [f"PROGRAM {pou_name}"]
        for role, decls in var_blocks.items():
            if decls:
                st_lines.append(f"  {role.value}")
                for d in decls:
                    st_lines.append(f"    {d.name} : {d.var_type.value};")
                st_lines.append("  END_VAR")

        st_lines.append(st_content if st_content.strip() else "  ;")
        st_lines.append("END_PROGRAM")

        return "\n".join(st_lines)
