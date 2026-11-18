from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as E
import json, re

root=Path(__file__).resolve().parents[2]
report=next(p for p in (root/'docs').glob('*-UML*.docx') if not p.name.startswith('~$'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(report) as z:
    tree=E.fromstring(z.read('word/document.xml'))
    text=''.join(tree.itertext())
    bookmarks={e.get('{'+ns['w']+'}name') for e in tree.findall('.//w:bookmarkStart',ns)}
    fields=[e.get('{'+ns['w']+'}instr','') for e in tree.findall('.//w:fldSimple',ns)]
    fields += [e.text or '' for e in tree.findall('.//w:instrText',ns)]
    refs=[m.group(1) for f in fields if (m:=re.search(r'REF (fig2_\d+)',f))]
    images=[p for p in z.namelist() if p.startswith('word/media/')]
    assert len(images)==19,len(images)
    assert all(b in bookmarks for b in refs)
    assert not any(t in text for t in ['错误!','错误！','Error!','未找到引用源'])
    for i in list(range(1,12)):
        assert f'UC{i}' in text
    for i in ['INC1','INC2','INC3','EXT1','EXT2','G1','G2','G3']:assert i in text
    assert 'REF fig2_19' in ''.join(fields)
    print(json.dumps({'images':len(images),'figure_bookmarks':len([b for b in bookmarks if b and b.startswith('fig2_')]),'figure_refs':len(refs),'all_19_usecases_present':True,'broken_reference_text':False},ensure_ascii=False))
