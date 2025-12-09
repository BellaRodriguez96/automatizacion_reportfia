import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from xml.sax.saxutils import escape
from zipfile import ZipFile


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""

WORKBOOK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""

WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>
"""

APP = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
</Properties>
"""

CORE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>
</cp:coreProperties>
"""


def _column_letter(index: int) -> str:
    """Convierte un índice basado en cero en letra de columna de Excel."""
    result = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _build_sheet_xml(headers: list[str], rows: list[list[str]]) -> str:
    xml_rows = []
    all_rows = [headers] + rows
    for row_idx, values in enumerate(all_rows, start=1):
        cells = []
        for col_idx, value in enumerate(values):
            col_letter = _column_letter(col_idx)
            text = escape(str(value))
            cells.append(
                f'<c r="{col_letter}{row_idx}" t="inlineStr"><is><t>{text}</t></is></c>'
            )
        xml_rows.append(f'<row r="{row_idx}">{"".join(cells)}</row>')
    body = "".join(xml_rows)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{body}</sheetData>"
        "</worksheet>"
    )


def create_basic_excel(headers: list[str], rows: list[list[str]]) -> Path:
    """Genera un archivo XLSX mínimo con los datos entregados."""
    destination = Path(tempfile.gettempdir()) / f"recursos_{uuid4().hex}.xlsx"
    created = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    sheet_xml = _build_sheet_xml(headers, rows)
    with ZipFile(destination, "w") as zipper:
        zipper.writestr("[Content_Types].xml", CONTENT_TYPES)
        zipper.writestr("_rels/.rels", RELS)
        zipper.writestr("docProps/app.xml", APP)
        zipper.writestr("docProps/core.xml", CORE_TEMPLATE.format(created=created))
        zipper.writestr("xl/workbook.xml", WORKBOOK)
        zipper.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS)
        zipper.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return destination
