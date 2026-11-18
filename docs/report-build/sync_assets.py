from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import xml.etree.ElementTree as E
root=Path(__file__).resolve().parents[2]
builder=root/'docs/report-build/build_report.py'
build_context={'__file__':str(builder)}
exec(compile(builder.read_text(encoding='utf-8').split('doc=Document();')[0],str(builder),'exec'),build_context)
report=next(p for p in (root/'docs').glob('*-UML*.docx') if not p.name.startswith('~$'))
temp=report.with_suffix('.tmp.docx')
with ZipFile(report) as src,ZipFile(temp,'w',ZIP_DEFLATED) as out:
    for entry in src.infolist():
        data=src.read(entry.filename)
        if entry.filename.startswith('word/media/image') and entry.filename.endswith('.png'):
            n=int(entry.filename.rsplit('image',1)[1][:-4])
            # Preserve the draw.io figures already sized in the report by the builder.
            if n not in build_context['MODEL_FIGURES']:
                data=build_context['FIGS'][n].read_bytes()
        if entry.filename=='docProps/core.xml':
            data=('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                  'xmlns:dc="http://purl.org/dc/elements/1.1/">'
                  '<dc:title>实验室异构设备智能运维管理系统 UML项目报告</dc:title>'
                  '<dc:subject>需求分析与UML建模</dc:subject><dc:creator/>'
                  '<cp:lastModifiedBy/><cp:revision>1</cp:revision></cp:coreProperties>').encode('utf-8')
        out.writestr(entry,data)
temp.replace(report)
print('Refreshed legacy figures and cleared personal metadata')
