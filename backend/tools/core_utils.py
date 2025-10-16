import io
import zipfile
import xml.etree.ElementTree as ET

from typing import List, Optional


def extract_office_xml_text(file_bytes: bytes, mime_type: str) -> Optional[str]:
    """
    Very light-weight XML scraper for Word, Excel, PowerPoint files.
    Returns plain-text if something readable is found, else None.
    No external deps – just std-lib zipfile + ElementTree.
    """
    shared_strings: List[str] = []
    ns_excel_main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            targets: List[str] = []
            if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                targets = ["word/document.xml"]
            elif mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                targets = [n for n in zf.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
            elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                targets = [n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
                try:
                    shared_strings_xml = zf.read("xl/sharedStrings.xml")
                    ss_root = ET.fromstring(shared_strings_xml)
                    for si in ss_root.findall(f"{{{ns_excel_main}}}si"):
                        parts = []
                        for t in si.findall(f".//{{{ns_excel_main}}}t"):
                            if t.text:
                                parts.append(t.text)
                        if parts:
                            shared_strings.append("".join(parts))
                except KeyError:
                    pass
                except ET.ParseError:
                    pass
                except Exception:
                    pass
            else:
                return None  

            pieces: List[str] = []
            for member in targets:
                try:
                    xml_content = zf.read(member)
                except KeyError:
                    continue
                try:
                    root = ET.fromstring(xml_content)
                except ET.ParseError:
                    continue

                member_texts: List[str] = []

                if mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                    for c in root.findall(f".//{{{ns_excel_main}}}c"):
                        v = c.find(f"{{{ns_excel_main}}}v")
                        if v is None or v.text is None:
                            continue
                        cell_type = c.get("t")
                        if cell_type == "s":
                            try:
                                idx = int(v.text)
                                if 0 <= idx < len(shared_strings):
                                    member_texts.append(shared_strings[idx])
                                else:
                                    continue
                            except Exception:
                                continue
                        else:
                            member_texts.append(v.text)
                else:
                    for elem in root.iter():
                        tag = elem.tag
                        if isinstance(tag, str) and tag.endswith("}t") and elem.text:
                            txt = elem.text.strip()
                            if txt:
                                member_texts.append(txt)
                        elif tag == "t" and elem.text:
                            txt = elem.text.strip()
                            if txt:
                                member_texts.append(txt)

                if member_texts:
                    pieces.append(" ".join(member_texts))

            if not pieces:
                return None

            text = "\n\n".join(pieces).strip()
            return text or None

    except zipfile.BadZipFile:
        return None
    except ET.ParseError:
        return None
    except Exception:
        return None
