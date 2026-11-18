from pathlib import Path
import math, json, re, xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from scenes import SCENES

ROOT=Path(__file__).resolve().parents[2]
AS=ROOT/'docs/report-assets'; AS.mkdir(exist_ok=True)
BUILD=ROOT/'docs/report-build'
TITLE='实验室异构设备智能运维管理系统'
FONT='C:/Windows/Fonts/msyh.ttc'
S=2
class Canvas:
    def __init__(self,w=1000,h=660):
        self.w,self.h=w,h; self.im=Image.new('RGB',(w*S,h*S),'white');self.d=ImageDraw.Draw(self.im)
    def line(self,pts,dash=False,width=2):
        pts=[(x*S,y*S) for x,y in pts]
        if not dash:self.d.line(pts,fill='#333333',width=width*S);return
        for a,b in zip(pts,pts[1:]):
            length=math.dist(a,b)
            for t in range(0,int(length),12*S):
                u=min(t+6*S,length)
                self.d.line([(a[0]+(b[0]-a[0])*v/length,a[1]+(b[1]-a[1])*v/length) for v in (t,u)],fill='#555555',width=S)
    def text(self,x,y,text,size=22,center=False,bg=False):
        f=ImageFont.truetype(FONT,size*S)
        box=self.d.multiline_textbbox((0,0),text,font=f,spacing=4*S)
        ww,hh=box[2]-box[0],box[3]-box[1]
        xx=x*S-ww/2 if center else x*S; yy=y*S-hh/2 if center else y*S
        if bg:self.d.rectangle((xx-4*S,yy-2*S,xx+ww+4*S,yy+hh+4*S),fill='white')
        self.d.multiline_text((xx,yy-box[1]),text,font=f,fill='#111111',spacing=4*S,align='center' if center else 'left')
    def box(self,x,y,w,h,text='',size=22,kind='rect'):
        bb=(x*S,y*S,(x+w)*S,(y+h)*S)
        if kind=='ellipse':self.d.ellipse(bb,fill='white',outline='#333333',width=2*S)
        elif kind=='diamond':self.d.polygon([(x*S,(y+h/2)*S),((x+w/2)*S,y*S),((x+w)*S,(y+h/2)*S),((x+w/2)*S,(y+h)*S)],fill='white',outline='#333333',width=2*S)
        elif kind=='round':self.d.rounded_rectangle(bb,radius=14*S,fill='white',outline='#333333',width=2*S)
        else:self.d.rectangle(bb,fill='white',outline='#333333',width=2*S)
        if text:self.text(x+w/2,y+h/2,text,size,True)
    def arrow(self,pts,label='',dash=False,triangle=False,labelpos=None,size=20,head=True):
        self.line(pts,dash)
        if head:
            a,b=pts[-2:]; ang=math.atan2(b[1]-a[1],b[0]-a[0]); k=15 if triangle else 11
            p=[(b[0]-k*math.cos(ang)+k*.48*math.sin(ang),b[1]-k*math.sin(ang)-k*.48*math.cos(ang)),b,(b[0]-k*math.cos(ang)-k*.48*math.sin(ang),b[1]-k*math.sin(ang)+k*.48*math.cos(ang))]
            if triangle:self.d.polygon([(x*S,y*S) for x,y in p],fill='white',outline='#333333',width=2*S)
            else:self.line(p)
        if label:
            x,y=labelpos or ((pts[0][0]+pts[-1][0])/2,(pts[0][1]+pts[-1][1])/2-16)
            self.text(x,y,label,size,True,True)
    def actor(self,x,y,name,size=18):
        self.d.ellipse(((x-10)*S,y*S,(x+10)*S,(y+20)*S),outline='#333333',width=2*S)
        self.line([(x,y+20),(x,y+55)]);self.line([(x-20,y+32),(x+20,y+32)]);self.line([(x-19,y+77),(x,y+55),(x+19,y+77)])
        self.text(x,y+98,name,size,True)
    def save(self,name):
        p=AS/(name+'.png');self.im.save(p,dpi=(250,250));return p

def intersect(rect,other,ellipse=False):
    x,y,w,h=rect; cx,cy=x+w/2,y+h/2;dx,dy=other[0]-cx,other[1]-cy
    if ellipse:t=1/math.sqrt((dx/(w/2))**2+(dy/(h/2))**2)
    else:t=min((w/2/abs(dx)) if dx else 1e9,(h/2/abs(dy)) if dy else 1e9)
    return cx+dx*t,cy+dy*t

source=ET.parse(ROOT/'docs/lab-device-usecase.drawio')
cells={c.get('id'):c for c in source.findall('.//mxCell')}
ids=['UC1','UC2','UC3','UC4','UC5','UC6','UC7','UC8','UC9','UC10','UC11','INC1','INC2','INC3','EXT1','EXT2','G1','G2','G3']
names={i:cells[i].get('value').split('\n')[0] for i in ids}
actors=['Admin','Stu','Ops','Dev','AI']
edges=[(c.get('source'),c.get('target'),c.get('value'),c.get('style')) for c in cells.values() if c.get('edge')]
assert len(ids)==19 and sum(v=='«include»' for a,b,v,s in edges)==5 and sum(v=='«extend»' for a,b,v,s in edges)==2

def usecase():
    c=Canvas(1200,960); geo={}
    for i,n in cells.items():
        if n.get('vertex'):
            g=n.find('mxGeometry');geo[i]=tuple(float(g.get(k,'0')) for k in ['x','y','width','height'])
    for i in ['UC9','UC11']:
        x,y,w,h=geo[i];geo[i]=(x,y,w,80)
    x,y,w,h=geo['UC9'];geo['UC9']=(x,y-10,w,h)
    c.box(200,20,820,890);c.text(610,43,TITLE,21,True)
    for a,b,v,s in edges:
        ra,rb=geo[a],geo[b];ca=(ra[0]+ra[2]/2,ra[1]+ra[3]/2);cb=(rb[0]+rb[2]/2,rb[1]+rb[3]/2)
        aa=intersect(ra,cb,a in ids);bb=intersect(rb,ca,b in ids)
        if a=='UC2' and b=='Dev':
            c.arrow([(410,455),(480,455),(480,350),(1040,350),(1040,510),(1090,510)],head=False);continue
        if a=='UC9' and b=='Dev':
            c.arrow([(420,680),(450,680),(450,690),(1040,690),(1040,520),(1090,520)],head=False);continue
        c.arrow([aa,bb],v or '',dash='dashed=1' in s,triangle='endArrow=block' in s,head='endArrow=none' not in s,size=17)
    for i in ids:
        x,y,w,h=geo[i];txt=i+'\n'+names[i]
        if i=='UC9':txt+='\n检测到异常'
        if i=='UC11':txt+='\n需要辅助诊断'
        c.box(x,y,w,h,txt,16,'ellipse')
    for i in actors:
        x,y,w,h=geo[i];c.actor(x+w/2,y,cells[i].get('value'),18)
    for i in ['N1','N2']:
        x,y,w,h=geo[i];c.box(x,y,w,h,cells[i].get('value').replace('扩展点: ','').replace('条件: ','条件 '),16)
    return c.save('fig2-1')

def sequence(sc,num):
    objs=sc['objs'];n=len(objs);msgs=sc['msgs'];h=125+len(msgs)*38
    c=Canvas(1000,h);xs=[65+i*(870/(n-1)) for i in range(n)]
    for x,o in zip(xs,objs):c.box(x-60,20,120,60,o,19);c.line([(x,80),(x,h-20)],True)
    frames={'操作设备':(5,9,'opt [校验通过]'),'接入设备':(5,9,'opt [认证通过]'),'异常监测与自动建单':(7,8,'opt [监测到异常]'),'工单处理与按需AI辅助':(6,12,'opt [运维人员请求AI辅助]')}
    if sc['key'] in frames:
        first,last,label=frames[sc['key']];top=105+(first-1)*38-26;bottom=105+(last-1)*38+18
        c.d.rectangle((5*S,top*S,995*S,bottom*S),outline='#666666',width=S)
        c.text(170 if sc['key']=='异常监测与自动建单' else 785,top+9,label,18,True,True)
    for k,(a,b,t) in enumerate(msgs):
        y=105+k*38
        if a==b:c.arrow([(xs[a],y),(xs[a]+45,y),(xs[a]+45,y+18),(xs[a],y+18)],t,labelpos=(xs[a]+145,y-7),size=18)
        else:c.arrow([(xs[a],y),(xs[b],y)],t,dash=('返回' in t),size=19)
    return c.save('fig2-'+str(num))

def communication(sc,num):
    n=len(sc['objs']);c=Canvas(1000,610)
    positions={4:[(115,90),(410,90),(760,90),(760,375)],5:[(115,90),(420,90),(785,90),(785,385),(420,385)],6:[(115,90),(410,90),(410,340),(780,90),(780,340),(780,520)],7:[(105,90),(375,90),(375,330),(765,90),(765,330),(765,515),(105,515)]}[n]
    rects=[(x-80,y-35,160,70) for x,y in positions]
    pairs={}
    for a,b,t in sc['msgs']:pairs.setdefault(tuple(sorted((a,b))),[]).append((a,b,t.split(' ')[0]))
    for (a,b),messages in pairs.items():
        if a==b:
            x,y=positions[a];c.arrow([(x+80,y),(x+118,y),(x+118,y+70),(x,y+70),(x,y+35)],', '.join(m[2] for m in messages)+' 自身判断',labelpos=(min(x+180,900),y+125),size=21);continue
        aa=intersect(rects[a],positions[b]);bb=intersect(rects[b],positions[a])
        c.line([aa,bb]);dx,dy=bb[0]-aa[0],bb[1]-aa[1];length=math.hypot(dx,dy)
        grouped={}
        for fr,to,no in messages:grouped.setdefault((fr,to),[]).append(no)
        for off,((fr,to),nos) in enumerate(grouped.items()):
            # Directed numbered messages are drawn beside the fixed structural link.
            t=.5;xx,yy=aa[0]+dx*t,aa[1]+dy*t
            v=1 if fr==a else -1
            side=v
            if (a,b)==(2,4):
                t=.32 if v==1 else .5;xx,yy=aa[0]+dx*t,aa[1]+dy*t;side=-v
            ox,oy=-dy/length*35*side,dx/length*35*side
            c.arrow([(xx+ox-v*dx/length*17,yy+oy-v*dy/length*17),(xx+ox+v*dx/length*17,yy+oy+v*dy/length*17)],', '.join(nos),labelpos=(xx+ox*2,yy+oy*2),size=23)
    for r,o in zip(rects,sc['objs']):c.box(*r,o,22)
    c.text(25,574,'编号与对应序列图逐条一致  条件及消息内容见序列图',21)
    return c.save('fig2-'+str(num))

def states(kind,num):
    c=Canvas(1000,570)
    if kind=='device':
        for x,t in [(80,'未知'),(430,'正常'),(780,'异常')]:c.box(x,180,150,90,t,24,'round')
        c.d.ellipse((40*S,218*S,58*S,236*S),fill='black');c.arrow([(58,227),(80,227)])
        c.arrow([(230,205),(430,205)],'有效采样 [正常]',labelpos=(330,168),size=20)
        c.arrow([(230,255),(300,255),(300,350),(850,350),(850,270)],'有效采样 [异常]',labelpos=(565,333),size=20)
        c.arrow([(580,205),(780,205)],'新采样 [异常]',labelpos=(675,168),size=20)
        c.arrow([(780,245),(580,245)],'新采样 [正常]',labelpos=(675,285),size=20)
        c.arrow([(480,180),(480,100),(155,100),(155,180)],'状态不可判定',labelpos=(318,82),size=20)
        c.arrow([(865,180),(865,65),(140,65),(140,180)],'状态不可判定',labelpos=(680,44),size=20)
        c.text(500,445,'对象是设备状态观测摘要  不是设备接入生命周期\n进入异常态对应UC9异常条件  建单去重策略待明确',23,True)
    else:
        c.d.ellipse((35*S,235*S,55*S,255*S),fill='black')
        for x,t in [(90,'已登记'),(425,'处理中'),(760,'处理信息已记录')]:c.box(x,200,205,90,t,22,'round')
        c.arrow([(55,245),(90,245)],'登记成功',labelpos=(165,151))
        c.arrow([(295,245),(425,245)],'开始处理',labelpos=(360,207),size=21)
        c.arrow([(630,245),(760,245)],'保存成功',labelpos=(695,207),size=21)
        c.arrow([(965,275),(985,275),(985,390),(530,390),(530,290)],'继续补充处理信息',labelpos=(744,369),size=21)
        c.arrow([(490,200),(490,100),(580,100),(580,200)],'请求辅助 / 取得建议或报告失败',labelpos=(528,66),size=20)
        c.text(500,475,'候选信息生命周期  未规定关闭状态与审批流\nAI辅助不推进状态  关闭条件及最终工单状态集待明确',23,True)
    return c.save('fig2-'+str(num))

def architecture(kind,num):
    c=Canvas(1000,650)
    if kind=='component':
        boxes=[(20,70,235,100,'«component»\n用户交互'),(360,30,290,100,'«component»\n设备使用与接入'),(360,220,290,100,'«component»\n权限与日志'),(360,420,290,100,'«component»\n状态监测与工单'),(735,30,245,100,'«component»\n设备交互适配'),(735,420,245,100,'«component»\nAI交互适配')]
        for x,y,w,h,t in boxes:c.box(x,y,w,h,t,24)
        links=[([(255,100),(360,80)],'请求使用或接入',(307,55)), ([(255,140),(300,140),(300,470),(360,470)],'监测或工单请求',(166,312)), ([(500,130),(500,220)],'身份 权限 日志',(512,176)), ([(650,80),(735,80)],'设备调用',(698,56)), ([(650,460),(700,460),(700,115),(735,115)],'状态及运维交互',(821,270)), ([(650,470),(735,470)],'[请求AI辅助]',(696,548))]
        for p,t,lp in links:c.arrow(p,t,True,labelpos=lp,size=20)
        c.text(500,595,'构件是职责划分  不意味着独立进程或微服务',23,True)
    else:
        c.box(15,75,225,160,'«device»\n人员终端\n交互客户端',24)
        c.box(330,40,340,420);c.text(500,78,'«device» 候选管理主机',24,True)
        c.text(500,120,'软路由或局域网 Linux 主机',21,True)
        c.box(365,165,270,115,'«artifact»\n设备管理应用\n包含逻辑构件',23)
        c.box(365,325,270,90,'«artifact»\n逻辑数据存储 待定',23)
        c.box(750,40,230,200,'«device»\n异构设备\nUSB 蓝牙 Zigbee\n适配或网关位置待定',22)
        c.box(750,355,230,150,'«node»\nAI Agent服务\n服务位置待明确',23)
        c.arrow([(240,150),(330,150)],'局域网\n协议待定',head=False,labelpos=(285,278),size=20)
        c.arrow([(670,170),(750,170)],'设备通信\n对应接入类型',head=False,labelpos=(823,292),size=20)
        c.arrow([(670,430),(750,430)],'AI接口\n协议待定',head=False,labelpos=(704,555),size=20)
        c.arrow([(500,280),(500,325)],'读写',labelpos=(555,302),size=19)
        c.text(500,610,'候选部署示意  不确定端口 云厂商 数据库或容器',22,True)
    return c.save('fig2-'+str(num))

MODEL_FIGURES = {
    2: 'class-diagram',
    13: 'activity-uc2-operate',
    14: 'activity-uc9-monitor',
    15: 'activity-uc11-ticket-ai',
}
FIGS = {num: ROOT / 'docs' / 'models' / (name + '.png')
        for num, name in MODEL_FIGURES.items()}
FIGS[1]=usecase()
for i,sc in enumerate(SCENES):FIGS[3+i*2]=sequence(sc,3+i*2);FIGS[4+i*2]=communication(sc,4+i*2)
FIGS[16]=states('device',16);FIGS[17]=states('ticket',17);FIGS[18]=architecture('component',18);FIGS[19]=architecture('deploy',19)

doc=Document();sec=doc.sections[0];sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=sec.bottom_margin=Cm(2.54);sec.left_margin=sec.right_margin=Cm(3.175)
sec.header_distance=sec.footer_distance=Cm(1.25);sec.different_first_page_header_footer=True
for st in ['Normal','Title','Heading 1','Heading 2','Heading 3','Heading 4','Caption']:
    s=doc.styles[st];s.font.name='宋体';s.font.color.rgb=__import__('docx').shared.RGBColor(0,0,0);s._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体')
    s.font.italic=False
    s.paragraph_format.space_after=Pt(6)
    ppr=s.element.find(qn('w:pPr'))
    if ppr is not None:
        for border in list(ppr.findall(qn('w:pBdr'))):ppr.remove(border)
norm=doc.styles['Normal'];norm.font.size=Pt(12);norm.paragraph_format.line_spacing=1.5;norm.paragraph_format.first_line_indent=Pt(24);norm.paragraph_format.space_after=Pt(4)
for name,size in [('Title',24),('Heading 1',18),('Heading 2',14),('Heading 3',12),('Heading 4',12)]:
    s=doc.styles[name];s.font.name='黑体';s._element.rPr.rFonts.set(qn('w:eastAsia'),'黑体');s.font.size=Pt(size);s.font.bold=True;s.paragraph_format.first_line_indent=Pt(0);s.paragraph_format.keep_with_next=True
doc.styles['Caption'].font.size=Pt(10.5);doc.styles['Caption'].paragraph_format.first_line_indent=Pt(0)
foot=sec.footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.CENTER;foot.paragraph_format.first_line_indent=Pt(0)
def field(p,instruction,text=''):
    r=p.add_run();f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),instruction);rr=OxmlElement('w:r');tt=OxmlElement('w:t');tt.text=text;rr.append(tt);f.append(rr);r._r.addnext(f)
field(foot,'PAGE','1')
settings=doc.settings.element;u=OxmlElement('w:updateFields');u.set(qn('w:val'),'true');settings.append(u)
break_pending=False
def apply_break(q):
    global break_pending
    if break_pending:q.paragraph_format.page_break_before=True;break_pending=False
    return q
def p(t,style=None):return apply_break(doc.add_paragraph(t,style))
def h(t,l=1):
    if re.match(r'^\d+\.\d+\.\d+\.\d+ ',t):l=4
    return apply_break(doc.add_heading(t,l))
def page():
    global break_pending
    if doc.sections[-1].orientation==WD_ORIENT.LANDSCAPE:orientation(False)
    else:break_pending=True
def flat(t):
    q=p('');q.paragraph_format.first_line_indent=Pt(0)
    m=re.match(r'表(\d+)-(\d+) (.*)',t)
    if m:q.add_run('表'+m[1]+'-');field(q,'SEQ Table'+m[1]+' \\* ARABIC',m[2]);q.add_run(' '+m[3]);q.paragraph_format.keep_with_next=True
    else:q.add_run(t)
    return q
def table(headers,rows,widths=None,size=10.5):
    t=doc.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.autofit=False
    if widths:
        for col,width in zip(t.columns,widths):col.width=Cm(width)
    for i,a in enumerate(headers):t.rows[0].cells[i].text=a
    for row in rows:
        for cell,a in zip(t.add_row().cells,row):cell.text=str(a)
    for ri,row in enumerate(t.rows):
        trPr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');trPr.append(cant)
        if ri==0:rep=OxmlElement('w:tblHeader');trPr.append(rep)
        for ci,cell in enumerate(row.cells):
            if widths:cell.width=Cm(widths[ci])
            tcPr=cell._tc.get_or_add_tcPr();m=OxmlElement('w:tcMar')
            for k,v in [('top','60'),('bottom','60'),('left','100'),('right','100')]:
                e=OxmlElement('w:'+k);e.set(qn('w:w'),v);e.set(qn('w:type'),'dxa');m.append(e)
            tcPr.append(m);b=OxmlElement('w:tcBorders')
            for k in ['top','left','bottom','right']:
                e=OxmlElement('w:'+k);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');b.append(e)
            tcPr.append(b)
            if ri==0:sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E7EDF3');tcPr.append(sh)
            for pp in cell.paragraphs:
                pp.paragraph_format.first_line_indent=Pt(0);pp.paragraph_format.line_spacing=1.15;pp.paragraph_format.space_after=Pt(2)
                for r in pp.runs:r.font.size=Pt(size);r.bold=ri==0
    return t
bookid=1
def caption(num,name):
    global bookid
    q=p('', 'Caption');q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.paragraph_format.keep_with_next=False
    start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),str(bookid));start.set(qn('w:name'),f'fig2_{num}');q._p.append(start)
    q.add_run('图2-');field(q,'SEQ Figure \\* ARABIC',str(num))
    e=OxmlElement('w:bookmarkEnd');e.set(qn('w:id'),str(bookid));q._p.append(e);bookid+=1
    q.add_run(' '+name)
def fig(num,name,width=14.4):
    q=p('');q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.paragraph_format.first_line_indent=Pt(0);q.paragraph_format.keep_with_next=True;q.paragraph_format.space_after=Pt(4)
    q.paragraph_format.line_spacing=1.0
    q.add_run().add_picture(str(FIGS[num]),width=Cm(width));caption(num,name)

def orientation(landscape=False,a3=False):
    s=doc.add_section(WD_SECTION_START.NEW_PAGE)
    if landscape:
        s.orientation=WD_ORIENT.LANDSCAPE;s.page_width=Cm(42 if a3 else 29.7);s.page_height=Cm(29.7 if a3 else 21)
        s.left_margin=s.right_margin=Cm(1.5);s.top_margin=s.bottom_margin=Cm(1.5)
    else:
        s.orientation=WD_ORIENT.PORTRAIT;s.page_width=Cm(21);s.page_height=Cm(29.7)
        s.left_margin=s.right_margin=Cm(3.175);s.top_margin=s.bottom_margin=Cm(2.54)
    s.different_first_page_header_footer=False

def widefig(num,name,width):
    if num in (13,14,15):
        orientation()
        section = doc.sections[-1]
        section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Cm(1.5)
        with Image.open(FIGS[num]) as img:
            width = min(17.5, 21.45 * img.width / img.height)
        fig(num,name,width)
        return
    orientation(True)
    # Fit the diagram and its explanatory paragraph on one landscape sheet.
    if num in (3,5,7,9,11,18,19):width=21.0
    if num==2:width=18.0
    if num in (18,19):width=20.0
    fig(num,name,width)

# Cover: personal fields deliberately remain empty.
q=p('基于 UML 的系统分析与设计','Title');q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.paragraph_format.space_before=Pt(55)
q=p('课程项目报告','Title');q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.paragraph_format.space_after=Pt(55)
q=p(TITLE,'Title');q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.paragraph_format.space_after=Pt(55)
for label in ['学校','学院','姓名','学号','专业班级','授课教师','完成时间']:
    q=flat(label+'：________________________');q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.paragraph_format.space_after=Pt(13)
page();q=flat('目录');q.paragraph_format.keep_with_next=True
q.runs[0].font.size=Pt(18);q.runs[0].font.bold=True;q.runs[0].font.name='黑体';q.runs[0]._r.rPr.rFonts.set(qn('w:eastAsia'),'黑体')
field(p(''),'TOC \\o "1-3" \\h \\z \\u','目录将在 Word 中更新')
page();h('1 需求分析')
h('1.1 项目背景与目标',2)
p('实验室同时使用 USB、蓝牙和 Zigbee 等设备。部分设备不能直接接入网络，设备连接、状态查询和维护记录分散在不同工具中，人员需要切换不同操作入口。零散云服务与本地设备并存，也使访问权限及故障追踪难以统一。')
p('本项目拟通过软路由或局域网 Linux 主机整合异构设备，使实验人员按授权使用设备，管理员集中处理接入、权限及审计，运维人员开展状态监测、自动化运维与故障工单处理。AI Agent 服务在运维人员请求时提供故障分析建议，辅助人工判断。')
p('本报告完成需求分析与 UML 建模。用例范围已确定，静态、动态及部署模型在此基础上给出分析设计方案。系统尚无业务实现，未确定技术栈、数据库、接口协议或实际部署设备，也未开展真实硬件验证。设计方案中的未决业务细节集中列入附录 B。')
page();h('1.2 系统边界与参与者',2)
p('系统边界包含申请使用、操作、查看、报修、接入、授权、审计、工单管理、监测、运维及条件性故障分析。软路由和网关属于部署背景，不新增为用例参与者。异构设备与 AI 服务是边界外的交互方，不是人员登录角色。')
flat('表1-1 参与者及直接关联')
table(['ID 与参与者','直接关联用例','业务职责'],[
('Admin 实验室管理员','UC5、UC6、UC7、UC8','接入设备、分配权限、审计日志、管理工单'),('Stu 实验人员 学生','UC1、UC2、UC3、UC4','申请、操作、查看状态、人工报修'),('Ops 运维人员','UC9、UC10、UC11','监测状态、执行运维、处理工单'),('Dev 异构设备','UC2、UC9','接受操作并提供监测交互'),('AI AI Agent服务','EXT2','响应辅助故障分析')],[4.1,3.4,7.1])
p('Admin 泛化到 Stu，管理员继承实验人员的用例关联。Ops 没有与其他角色的泛化，不能从图中推导出运维人员具有管理员或实验人员的全部职责。人员关联也不能替代实现阶段的完整访问控制规则。')
page();h('1.3 功能需求与用例清单',2)
p('功能清单按基准图转录。核心功能用 UC 标识，包含行为用 INC 标识，扩展行为用 EXT 标识，接入特化用 G 标识。编号用于跨模型追溯，不要求一个用例对应一个页面或数据表。')
flat('表1-2 全部用例及需求要点')
rows=[]
summaries=['实验人员提交设备使用意图；包含登录认证','按授权操作设备；包含认证、权限校验与日志记录','向实验人员展示设备状态','由实验人员主动描述并提交故障','管理员接入设备；包含认证和三种接入特化','管理员配置人员与设备的访问权限','管理员查阅并审计已有操作日志','管理员管理故障工单；不等同实际处理','运维人员与设备交互监测；异常时条件建单','运维人员执行自动化运维；动作与触发待明确','运维人员记录处理；请求时取得AI诊断','判定当前主体对目标设备的操作权限','记录设备操作相关结果，供审计使用','验证身份有效性；不要求逐次输入凭据','监测到设备状态异常时扩展UC9','运维人员请求AI辅助时扩展UC11','UC5的USB接入形式','UC5的蓝牙接入形式','UC5的Zigbee接入形式']
for i,s in zip(ids,summaries):rows.append((i,names[i],s))
table(['用例ID','名称','需求要点'],rows,[1.7,4.5,8.4],10.5)
page();h('1.4 业务约束与待明确事项',2)
p('UC2 的权限校验、日志记录和登录认证属于其包含行为。设计中应避免未经授权的设备操作，并使实际执行结果能够追踪。其他入口虽然没有 include 连线，仍需在实现时制定适当安全控制；不能据此允许未授权访问，也不能在原图中补造包含关系。')
p('EXT1 的基础用例是 UC9，扩展点为“检测到异常”，触发条件是“监测到设备状态异常”。EXT2 的基础用例是 UC11，扩展点为“需要辅助诊断”，触发条件是“运维人员请求AI辅助”。AI 分析保留在范围内，但不强制用于每张工单。自动建单及 AI 分析均不能推导出自动修复或自动执行 UC10。')
p('三种设备接入是 UC5 的特化，每次接入选择适用的具体形式，不是顺序执行三种接入。项目不增加预约排期、多级审批、采购库存、资产折旧、借还、计费、消息通知、多租户或额外设备协议。')
flat('表1-3 未决问题及建模处理')
table(['事项','当前依据','本报告处理'],[
('申请是否审批','UC1仅说明申请','仅表达申请提交，不画审批链'),('权限粒度与占用规则','UC6及INC1，无粒度规定','使用授权描述，不固定独占或共享'),('工单状态与关闭条件','UC8及UC11，无状态流规定','状态图仅为候选信息生命周期'),('异常阈值与监测周期','UC9及EXT1，无具体数值','以异常判据占位，不填写指标'),('运维动作与自动触发','UC10未细化','只表达执行与结果，不擅自重启或刷写'),('日志及AI上下文','INC2、EXT2，无字段规定','提出必要概念，字段和保留规则待明确'),('部署与具体技术','局域网主机背景','展示候选节点，不选框架、数据库或云厂商')],[3.8,4.3,6.5])
h('1.5 质量要求与验证边界',2)
p('质量要求围绕权限、操作结果与日志一致性、监测异常建单、按需 AI 辅助展开。未授权操作应被拒绝；记录失败不能冒充记录成功；未知状态不应未经规则确认直接当作异常；AI 不可用时应能明确区分辅助失败与工单处理结果。这些是设计与后续验收方向，不是已执行测试。响应时间、容量及运维成功率没有已确认数值，不在报告中编造。')
page();h('2 系统建模')
h('2.1 用例模型',2);h('2.1.1 系统总体用例图',3)
p('图2-1按仓库用例图的参与者、19个用例和关系绘制，用例ID用于与表1-2核对。展示标题统一为正式项目名称；原文件仍保留旧系统边界标题“实验室设备统一管理与智能运维系统”，此差异不改变功能范围。总体图采用横向整页以保持可读性。')
p('总体图中实线关联表示参与交互，虚线 include 和 extend 分别表达包含与条件扩展，空心三角指向一般参与者或一般用例。两条说明注释不计入用例数量。图中的关联没有表达调用顺序。')
orientation(True,True)
fig(1,'系统总体用例图',32.0)
s=doc.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.PORTRAIT;s.page_width=Cm(21);s.page_height=Cm(29.7);s.left_margin=s.right_margin=Cm(3.175);s.top_margin=s.bottom_margin=Cm(2.54);s.different_first_page_header_footer=False
h('2.1.2 参与者职责与用例关系',3)
p('图2-1中的管理员既具有直接关联的管理用例，也通过泛化继承实验人员的关联；继承方向是 Admin→Stu。外部设备直接参与 UC2、UC9，外部 AI 服务直接参与 EXT2。管理员不是所有角色的总父类，Dev 和 AI 也不属于内部人员权限体系。')
flat('表2-1 必须保持的用例关系')
table(['类型','起点到终点','含义'],[
('include','UC2→INC1','操作设备包含权限校验'),('include','UC2→INC2','操作设备包含记录操作日志'),('include','UC1→INC3','申请使用设备包含登录认证'),('include','UC2→INC3','操作设备包含登录认证'),('include','UC5→INC3','接入设备包含登录认证'),('extend','EXT1→UC9','扩展点 检测到异常；条件 监测到设备状态异常'),('extend','EXT2→UC11','扩展点 需要辅助诊断；条件 运维人员请求AI辅助'),('泛化','G1→UC5','USB接入是一种接入设备形式'),('泛化','G2→UC5','蓝牙接入是一种接入设备形式'),('泛化','G3→UC5','Zigbee接入是一种接入设备形式'),('参与者泛化','Admin→Stu','管理员继承实验人员的用例关联')],[2.3,3.7,8.6])
p('图后关系检查重点是方向和条件：extend 箭头从扩展用例指向基础用例；泛化三角指向一般用例；include 箭头指向被包含行为。N1、N2只解释各自扩展条件，不引入业务功能。')
h('2.1.3 用例说明',3)
p('以下逐项记录目标、参与者、触发、前置、基本流程、异常、后置及模型对应。基准图未规定的输入校验、成功回执、信息保存和失败提示均为本报告分析设计建议；不能据此认定字段或实现策略已经确认。管理员在 UC1至UC4中的参与通过泛化继承。')

RECORDS=[
('UC1','实验人员；管理员继承','提交对目标设备的使用申请；人员选择申请入口触发','目标设备可识别是设计前提；包含登录认证','1 人员提出使用意图。2 系统执行INC3验证身份。3 人员提交目标设备与必要说明。4 系统登记申请并返回提交结果。','步骤2认证失败则结束且不登记；步骤3信息不足则补充后继续；步骤4登记失败返回失败。','成功形成可追溯申请，失败不报告已登记；申请不自动产生设备权限。','UC1→INC3；图2-1、图2-2；不重复绘制简单提交交互图。','审批、申请字段、有效期及申请与授权的业务规则待明确。'),
('UC2','实验人员、异构设备；管理员继承','在允许的访问范围内操作目标设备；人员发起操作','目标设备可识别；身份与权限按INC3、INC1校验','1 人员发起操作。2 系统完成身份和设备权限校验。3 校验通过后与设备交互。4 记录操作日志。5 返回执行与记录结果。','步骤2失败不下发指令；步骤3设备不可达返回失败或未知结果；步骤4记录失败单独报告，不宣称全部成功。','成功或失败的实际结果与记录情况可区分；不能绕过校验。','包含INC1、INC2、INC3；图2-3、图2-4、图2-13。','具体指令、权限粒度、日志失败处置待明确；步骤顺序为设计建议。'),
('UC3','实验人员；管理员继承','查看目标设备当前可提供的状态；人员请求查询','查询访问范围待明确；设备可识别为设计前提','1 人员指定设备。2 系统取得可提供的状态摘要。3 展示状态及可用性说明。','步骤2无设备或无状态时返回无可用结果；不能把未知展示为正常。','完成一次状态查看，不自动建立监测任务。','图2-1、图2-2、图2-16；无独立交互图，查询无复杂分支。','查询授权、状态时效、显示字段与刷新策略待明确。'),
('UC4','实验人员；管理员继承','主动提交设备故障描述；人员发现故障触发','目标设备及故障描述可识别为设计前提','1 人员提交设备和故障现象。2 系统检查信息。3 登记人工报修。4 返回登记结果。','步骤2信息不足则补充后重新提交；步骤3失败不返回受理成功。','产生人工故障记录；统一映射为工单属于分析设计建议。','图2-7、图2-8、图2-17；与EXT1来源区分。','字段、重复报修处理、人工报修与工单关联规则待明确。'),
('UC5','实验室管理员','接入设备使其可由系统识别并交互；管理员发起接入','包含INC3；管理员选择一种支持的接入类型','1 管理员提交接入请求。2 系统执行登录认证。3 选用G1、G2或G3对应形式。4 完成设备交互。5 返回并登记接入结果。','步骤2认证失败结束；步骤4接入失败不标为成功；重新接入条件待明确。','成功形成可识别设备，失败返回原因；不自动授予人员操作权限。','包含INC3；G1/G2/G3泛化到UC5；图2-5、图2-6。','设备型号、识别字段、驱动与网关连接方案待明确。'),
('UC6','实验室管理员','分配人员的设备访问权限；管理员发起分配','具备管理授权与有效目标为设计前提，具体控制待明确','1 管理员指定主体与设备。2 给出拟分配的访问范围。3 系统检查并保存权限关联。4 返回配置结果。','步骤2授权表达不完整则补充；步骤3保存失败时保留可确定的原状态，不宣称新权限生效。','成功的权限关联可供INC1读取；不从申请自动推定已授权。','图2-1、图2-2；不添加UC6与INC1的include关系。','权限粒度、覆盖或叠加规则、有效期及撤销规则待明确。'),
('UC7','实验室管理员','检查设备操作记录；管理员发起审计','在有授权的审计范围内读取日志为设计前提','1 管理员提出审计目标。2 系统读取相应日志。3 展示操作主体、目标及可用结果。4 管理员检查记录。','步骤2无记录显示无结果；读取失败报告失败，不生成虚假记录。','完成记录查阅；不自动改写历史日志或执行设备动作。','图2-1、图2-2；与INC2的写入职责区分。','日志字段、检索条件、保留时长、篡改保护措施待明确。'),
('UC8','实验室管理员','管理已有故障工单信息；管理员选择管理入口','具备工单管理权限且目标可识别为设计前提','1 管理员定位工单。2 系统展示可用信息。3 管理员执行待明确范围内的管理操作。4 系统返回管理结果。','步骤1目标不存在返回无结果；步骤3操作边界未定义时不能自行执行派单或关闭；保存失败返回失败。','保存经明确规则允许的管理结果；不替代运维实际处理。','图2-1、图2-2、图2-17；无独立管理流程图，业务操作待明确。','管理动作清单、派单与关闭规则未确认。'),
('UC9','运维人员、异构设备','取得并评估设备状态；运维人员参与监测','目标设备可识别；监测方式与异常判据待明确','1 系统与设备交互取得状态。2 按判据判断。3 正常时返回监测结果。4 异常时在“检测到异常”扩展点触发EXT1。','步骤1获取失败标记状态未知；是否当作异常待明确；步骤4建单失败分别报告异常与建单失败。','产生监测结果；满足条件时产生自动工单。','EXT1扩展UC9；图2-9、图2-10、图2-14、图2-16。','周期、阈值、通信失败判定、重复异常去重待明确。'),
('UC10','运维人员','执行自动化运维以完成明确的维护目标；运维人员参与执行','动作已被明确且目标可识别为设计前提','1 运维人员进入运维执行场景。2 系统取得明确的动作和目标。3 按动作执行维护。4 记录或返回可确定的执行结果。','步骤2动作未定义时不能自行选择重启、更新或修复；步骤3失败返回实际结果。','完成所选维护动作的结果反馈；未确认成功标准不报告修复成功。','图2-1、图2-18、图2-19；动作与触发未明确，暂不绘制具体交互图。','动作清单、调度方式、触发条件、授权、回滚及结果存储待明确。'),
('UC11','运维人员','处理故障工单并保留处理信息；人员打开处理场景','工单存在且处理访问范围明确为设计前提','1 查看故障上下文。2 判断是否请求AI辅助。3 请求时触发EXT2；未请求则继续人工处理。4 提交并保存处理信息。','步骤3AI失败可继续人工处理；步骤4保存失败报告未保存。','形成处理信息；不自动等同工单关闭，也不自动执行UC10。','EXT2扩展UC11；扩展点“需要辅助诊断”；图2-11、图2-12、图2-15、图2-17。','处理动作、状态变化、关闭与复核规则待明确。'),
('INC1','由UC2包含；当前操作人员的身份上下文','判定目标设备操作是否获授权；UC2执行时触发','有可验证的主体、设备及授权描述为设计前提','1 接收主体与操作目标。2 读取可用权限关联。3 返回允许或拒绝结果。','步骤2缺少或不能取得有效授权时，采用拒绝下发的设计建议；授权判定规则待明确。','返回校验结果；不新增、批准或修改权限。','UC2→INC1；图2-3、图2-4、图2-13；无新增人员直接关联。','权限粒度、规则冲突及缓存策略待明确。'),
('INC2','由UC2包含；操作协调对象提供上下文','记录设备操作以支持审计；UC2执行中触发','操作上下文与可确定结果为设计前提','1 接收操作上下文。2 写入可追溯日志。3 返回记录结果。','步骤2写入失败需与设备执行结果区分；重试、补写或阻断规则待明确。','成功形成操作日志供UC7审计；失败不能报告已经记录。','UC2→INC2；图2-2、图2-3、图2-4；不擅自规定其他用例必须写相同日志。','字段、保留时间、记录失败策略待明确。'),
('INC3','由UC1、UC2、UC5包含；相应人员提供身份','验证身份有效性；基础用例需要认证时触发','存在身份信息或有效会话为设计前提','1 取得凭据或会话上下文。2 验证身份有效性。3 向基础用例返回认证结果。','步骤2验证失败，基础用例不执行需认证的目标行为；凭据补充策略待明确。','取得认证结果；成功不代表已获得目标设备权限。','UC1/UC2/UC5→INC3；图2-3至图2-6。','认证方式、会话期限与其他入口安全控制待明确。'),
('EXT1','在UC9中由监测条件触发；无新增直接人员关联','在异常条件下自动生成故障工单','UC9位于“检测到异常”扩展点且监测到设备状态异常','1 接收异常设备与可用状态信息。2 登记来源为监测的工单。3 返回建单结果给UC9。','步骤2失败时保留异常结果并报告未建单；重复异常合并规则待明确。','成功形成自动工单；不自动调用UC10。','EXT1→UC9；条件“监测到设备状态异常”；图2-9、图2-10、图2-14。','异常证据字段、去重、重试及工单关联待明确。'),
('EXT2','AI Agent服务直接关联；运维人员经UC11请求','按请求取得AI故障分析以辅助诊断','UC11位于“需要辅助诊断”扩展点且运维人员请求AI辅助','1 准备故障上下文。2 向AI Agent服务请求分析。3 展示有效建议或失败说明。4 返回UC11继续处理。','步骤2或3服务不可用、超时、返回无效时，报告辅助不可用并回到人工处理。','获得诊断参考或明确失败结果；AI不直接操作设备。','EXT2→UC11；条件“运维人员请求AI辅助”；图2-11、图2-12、图2-15。','服务提供方、输入范围、结果形式、超时和脱敏策略待明确。'),
('G1','继承UC5的实验室管理员参与语境','以USB形式接入设备；管理员选择USB','复用UC5及INC3；USB接入环境可用为设计前提','复用UC5步骤1、2、5；步骤3选择USB适配，步骤4识别并连接USB目标设备。','认证失败沿用UC5；USB设备不能识别或连接时返回接入失败。','成功形成USB设备接入结果；不执行蓝牙或Zigbee步骤。','G1→UC5；图2-1、图2-5、图2-6；共享公共交互图。','USB型号、驱动、可用指令、热插拔规则待明确。'),
('G2','继承UC5的实验室管理员参与语境','以蓝牙形式接入设备；管理员选择蓝牙','复用UC5及INC3；蓝牙接入环境可用为设计前提','复用UC5步骤1、2、5；步骤3选择蓝牙适配，步骤4建立目标设备连接。','认证失败沿用UC5；目标不可达或连接失败时返回失败。','成功形成蓝牙接入结果；不要求依次执行其他特化。','G2→UC5；图2-1、图2-5、图2-6；共享公共交互图。','配对、服务类型、设备身份与连接恢复规则待明确。'),
('G3','继承UC5的实验室管理员参与语境','以Zigbee形式接入设备；管理员选择Zigbee','复用UC5及INC3；Zigbee接入环境可用为设计前提','复用UC5步骤1、2、5；步骤3选择Zigbee适配，步骤4经待定接入设施与设备交互。','认证失败沿用UC5；设备不能接入或适配交互失败时返回失败。','成功形成Zigbee接入结果；网关不是新增用例参与者。','G3→UC5；图2-1、图2-5、图2-6；共享公共交互图。','协调器、网关位置、入网方式与设备型号待明确。')]

for k,rec in enumerate(RECORDS):
    if k%2==0 and k>0:page()
    i,who,goal,pre,basic,alt,post,rel,tbd=rec
    h(f'2.1.3.{k+1} {i} {names[i]}',3)
    for label,text in [('参与者',who),('目标与触发',goal),('前置条件',pre),('基本流程',basic),('备选与异常流程',alt),('后置条件',post),('关联用例与图示',rel),('待明确事项',tbd)]:
        q=p('');q.paragraph_format.line_spacing=1.15;q.paragraph_format.space_after=Pt(4)
        r=q.add_run(label+'：');r.bold=True;q.add_run(text)

page();h('2.2 静态模型',2);h('2.2.1 领域类及职责',3)
p('从使用申请、设备操作、访问分配、日志审计和工单处理可识别出用户、设备、设备使用申请、设备权限关联、操作日志、故障工单六个领域概念。图2-2将这些概念表达为分析类，并用必要属性及职责说明其用途；这些分析类不是已经实现的代码类或数据库表。')
flat('表2-2 分析类来源与职责')
table(['候选类','用例来源','职责及字段状态'],[
('用户','UC1/2/4/6、INC3','提供主体身份与角色上下文；不按角色建立继承树'),('设备','UC1/2/3/5/9/10','提供设备标识、接入形式和可用状态摘要'),('设备使用申请','UC1','保存人员设备使用意图；审批状态未定义'),('设备权限关联','UC6、INC1','表达人员与设备授权；授权描述尚待明确'),('操作日志','INC2、UC7','保存可审计操作结果；字段与保留期未定'),('故障工单','UC4/8/11、EXT1','关联故障设备与处理信息；人工报修映射为设计建议')],[3.3,3.6,7.7])
h('2.2.2 类关系与类图',3)
p('设计建议中，一条申请关联一个申请人和一个目标设备；一个人员或设备可对应零到多条申请。每条权限关联对应一个用户与一个设备，从而表达二者间的多对多访问范围。每条操作日志对应一个操作主体和目标设备。以上多重性按单设备业务记录的简化分析方案提出，多设备申请及复合操作待明确。')
p('一个工单建议关联一个目标设备，可有零或一个人工报修人：自动监测建单允许没有人工报修人，避免强行为 EXT1 伪造人员来源。工单来源用手工或监测区分，处理信息不默认包含关闭或审批状态。AI 服务在交互模型中作为外部协作方，不强行持久化为领域实体。')
widefig(2,'领域分析类图',20.0)
p('图2-2中的权限关联支持 UC6 分配及 INC1 校验，但这种数据联系不增加用例间的 include 连线。日志实体只表达记录与审计的共用信息，不能把 UC7 审计和 INC2 写日志合并。角色集合用于表示职责上下文；用例参与者泛化不直接转换成代码继承。')
page();h('2.3 动态模型',2);h('2.3.1 序列图与协作图',3)
p('本报告将协作图统一称为通信图。序列图按时间排列消息，通信图显示同一组对象间的结构联系并标注消息编号。五组关键场景复用相同编号、对象及消息语义；图中入口、协调和适配对象均为候选设计职责，不代表选定的框架或部署进程。')
for k,sc in enumerate(SCENES):
    if k:page()
    h(f'2.3.1.{k+1} {sc["key"]}',3)
    p(sc['goal']);p('对应范围：'+sc['refs']+'。');p('基本流程：'+sc['basic']);p('备选流程：'+sc['alt'])
    p('对象职责：人员提出业务意图，入口承接交互，协调对象组织业务过程；适配或记录对象分别承担外部通信和信息登记。消息编号表示本场景的建议执行顺序，方括号表示条件，不新增用例关系。')
    widefig(3+k*2,sc['key']+'序列图',24.0);p(sc['after'])
    widefig(4+k*2,sc['key']+'通信图',24.0);p('通信图实线表示对象间的结构联系，联系旁的方向箭头及编号表示消息发送方向和顺序；同编号的消息内容与对应序列图一致，条件及返回含义见序列图。通信图没有重新定义异常流程。')

page();h('2.3.2 活动图',3);h('2.3.2.1 设备操作活动',3)
p('图2-13对应 UC2 及三个包含行为。人员发起操作后由系统校验身份和设备权限；拒绝分支直接结束反馈，不到达设备指令节点。通过分支经设备返回结果后记录日志，再向人员反馈。日志失败作为结果的一部分报告，具体补偿规则仍待明确。')
widefig(13,'设备操作活动图',20.0);p('三个泳道把人员请求、系统判断和外部设备交互分开。该图没有规定反复输入凭据，也没有为其他入口补画认证包含关系。设备执行失败与日志写入失败应分别表示，便于后续验证实际失败路径。')
page();h('2.3.2.2 异常监测与建单活动',3)
p('图2-14对应 UC9、EXT1。运维人员参与监测，系统取得设备状态后依据待定判据判断。正常分支返回监测结果；监测到异常的分支进入自动建单。通信失败引起的状态未知是否符合异常条件尚待明确，不能默认进入建单分支。')
widefig(14,'异常监测与自动建单活动图',20.0);p('建单是异常分支中的扩展行为，工单登记成功与否不改写已取得的异常监测结果。该流程没有自动执行运维节点，避免将 EXT1 错误解释为 UC10 的触发器。')
page();h('2.3.2.3 故障处理与辅助诊断活动',3)
p('图2-15对应 UC11、EXT2。运维人员查看工单后决定是否请求 AI 辅助。请求分支把诊断上下文交给外部 AI 服务，返回建议或辅助不可用说明；未请求分支直接进入人工处理。两个分支汇合后，由运维人员提交处理信息并由系统保存。')
widefig(15,'工单处理与按需AI辅助活动图',20.0);p('AI 泳道只包含分析返回，不含设备操作或工单关闭。运维人员保留建议判断职责；服务失败不应阻止人工处理。保存处理信息的成功条件与工单最终关闭条件分别待明确。')

page();h('2.3.3 状态图',3);h('2.3.3.1 设备状态观测摘要',3)
p('图2-16选择“设备状态观测摘要”作为状态对象，描述系统当前掌握的状态是否可判定，不描述设备整个物理生命周期。未知、正常、异常是便于 UC3 和 UC9 共享状态信息的候选集合；有效采样是否过期、异常判据及通信失联解释需进一步确定。')
flat('表2-3 设备状态候选转换')
table(['当前状态','事件与条件','动作与目标'],[('未知','取得有效采样且判定正常','保存摘要→正常'),('未知或正常','有效采样判定异常','保存异常摘要→异常'),('异常','有效采样判定正常','保存恢复摘要→正常'),('正常或异常','状态无法判定','标明未知→未知')],[3.1,5.5,6])
widefig(16,'设备状态观测摘要候选状态图',24.0);p('异常条件为 EXT1 提供触发依据，但状态转换图不确定重复采样是否重复建单。工单去重必须另行制定，不能从自循环或状态变化次数推导。对象状态也不直接触发 UC10。')
page();h('2.3.3.2 故障工单信息生命周期',3)
p('图2-17给出工单信息生命周期的候选分析方案，不固定业务最终状态流。已登记表示故障信息形成记录；处理中表示运维人员已进入处理场景；处理信息已记录表示本次信息保存成功。后者不等同故障解决或工单关闭。')
flat('表2-4 工单信息候选转换')
table(['当前状态','事件与条件','动作与目标'],[('尚未记录','登记成功','保存故障信息→已登记'),('已登记','运维人员开始处理','进入处理场景→处理中'),('处理中','保存处理信息成功','保存记录→处理信息已记录'),('处理信息已记录','继续补充处理','返回处理中'),('处理中','请求AI辅助','取得建议或失败说明→仍处理中')],[3.6,5.0,6.0])
widefig(17,'故障工单信息生命周期候选状态图',24.0);p('人工报修与自动监测来源都可以进入登记状态；统一记录方式仍是候选设计。工单关闭、重新打开、指派、复核及合法管理动作没有已确认规则，因此没有补画这些转换，也没有绘制最终关闭节点。')

page();h('2.4 构件与部署模型',2);h('2.4.1 构件职责及依赖',3)
p('图2-18以职责划分逻辑构件。用户交互承接人员请求；设备使用与接入组织申请、操作和接入；权限与日志提供身份上下文、授权判断及审计记录；状态监测与工单组织监测、建单和处理；设备交互适配及 AI 交互适配分别隔离外部通信差异。')
widefig(18,'系统逻辑构件图',24.0);p('图中的虚线依赖指向被使用职责。设备使用与接入依赖权限与日志，保证 UC2 包含行为有承载位置；状态监测与工单依赖设备适配取得状态，仅在运维请求时依赖 AI 适配完成诊断。UC10 的具体动作未定，暂由设备交互与维护协调职责承载，不能将此分组误读成已确定运维实现。')
p('构件可以在同一管理应用中实现，不预设微服务或独立进程。工单管理与处理可共享信息而保留职责差异；不要求一个领域类对应一个构件。')
page();h('2.4.2 部署节点与通信关系',3)
p('图2-19展示一个候选部署：人员终端通过局域网访问管理应用；管理应用位于软路由或局域网 Linux 主机；主机通过对应接入形式与设备交互；外部 AI 服务通过待定接口响应诊断请求。逻辑存储表示信息持久化职责，不指定数据库产品。')
widefig(19,'候选部署图',24.0);p('设备节点与主机之间的通信路径代表 USB、蓝牙、Zigbee 对应交互，适配器、协调器或网关的实际位置尚待明确。AI 服务的位置可以在实验室或外部环境中确定，本图不选定云服务商、端口、认证协议或容器方案。')
p('部署模型承载已有用例，不新增“网关管理员”等参与者，也不把非联网设备描述为已具备 IP 接口。主机选择需要后续结合设备支持、运行负载和维护条件评估；当前图仅完成节点与边界分析，未进行安装或连通性验证。')

page();h('3 模型一致性检查与总结');h('3.1 用例及跨模型一致性',2)
p('报告的需求与用例模型覆盖五个参与者及19个用例。UC1至UC11的直接职责、Admin到Stu泛化、5条包含、2条条件扩展及3条接入泛化均与基准图对应。原始用例图保持不变，展示图只统一标题并加注追溯ID。')
p('交互模型采用五组相同对象与编号消息的序列图、通信图。活动图进一步解释校验拒绝、正常与异常监测、请求与未请求AI辅助。类图为权限校验、日志审计和故障记录提供分析对象；候选状态图只说明信息生命周期，不将未定业务状态当成已确认规则。构件图与部署图分别说明职责和节点。')
flat('表3-1 一致性核对项目')
table(['核对项','报告对应位置','结论与限制'],[('参与者和用例','表1-1、表1-2、图2-1','五个参与者、19个用例均有说明'),('包含与泛化方向','表2-1、图2-1','方向与基准保持一致'),('按条件触发扩展','图2-9至2-12、图2-14/15','正常或未请求时跳过扩展'),('设备权限与日志','图2-2至2-4、图2-13','建议流程保持校验与记录职责'),('配对交互一致','图2-3至2-12','每组对象、消息编号及语义一致'),('模型设计状态','图2-2至2-19、附录B','设计方案不等同业务实现或用户确认'),('构件与部署区分','图2-18、图2-19','分别表达逻辑职责与候选物理节点')],[3.5,4.5,6.6])
h('3.2 后续验证计划',2)
p('下表列出后续实现时的验证场景，所有场景当前均未执行。模拟设备检查应验证流程与失败处理；真实硬件验证还需检查具体 USB、蓝牙、Zigbee 设备指令及状态获取。模拟通过不能代替真实设备验证，文档一致性核对也不能代替运行测试。')
page();flat('表3-2 后续行为验证计划')
table(['用例范围','拟验证输入或条件','期望结果','当前状态'],[
('UC1、INC3','认证成功或失败提交申请','成功登记；失败不登记','未执行'),('UC2、INC1','无有效设备授权','不向设备下发指令','未执行'),('UC2、INC2','授权通过、设备返回结果','日志与可确定结果对应','未执行'),('UC2、INC2','设备执行或日志写入失败','分别报告失败，不伪报全成功','未执行'),('UC3、UC9','设备没有可用状态','明确未知，非默认正常','未执行'),('UC4、EXT1','分别人工报修与监测异常','来源可区分，登记结果明确','未执行'),('UC5、G1/G2/G3','逐种接入成功与连接失败','只执行选定形式，失败不标成功','未执行'),('UC6、UC7','权限保存与日志审计','权限结果可核对，读取失败明确','未执行'),('UC8、UC11','管理操作与运维处理','按确认职责执行与保存','未执行'),('UC9、EXT1','正常与异常监测结果','正常不建单，异常触发扩展','未执行'),('UC10','明确动作与失败条件后','按定义动作执行并反馈','未执行'),('UC11、EXT2','未请求与请求AI辅助','未请求不调用，请求才调用','未执行'),('EXT2','AI超时或无有效返回','报告辅助失败，可继续人工处理','未执行')],[2.5,4.2,5.8,2.1],10.5)
h('3.3 建模总结',2)
p('本报告形成需求说明、19项用例记录、领域分析类、五组关键交互模型，以及活动、状态、构件和部署模型。设备操作的校验与日志、异常时自动建单、按请求AI辅助是建模重点，未扩展为自动修复或图外业务。当前成果属于分析设计；后续需明确申请授权、工单状态、异常判据、运维动作、设备与AI接口，修订模型并开展实现和验证，再选择具体技术及部署方案。')

orientation(True);h('附录 A 用例与模型追溯表')
p('需求说明统一见1.3；每个用例的记录见2.1.3对应编号；所有用例均在图2-1展示。下表细列对象、交互、活动状态及构件部署对应。不需要独立细化图的用例注明原因，未决功能不以空白冒充已覆盖。')
# wide appendix with full required columns
detail={
'UC1':('用户、申请、设备','无独立图 简单提交','无独立图 申请状态待定','设备使用与接入'),
'UC2':('用户、设备、权限、日志','2-3、2-4','2-13','设备使用、权限日志、设备适配'),
'UC3':('设备、用户','无独立图 简单查询','2-16','用户交互、设备状态职责'),
'UC4':('用户、设备、工单','2-7、2-8','2-17','工单职责'),
'UC5':('设备、接入协调','2-5、2-6','无独立图 公共接入交互已说明','接入、设备适配'),
'UC6':('用户、权限、设备','无独立图 粒度待明确','无独立图 授权规则待明确','权限职责'),
'UC7':('操作日志、用户','无独立图 读写区别已说明','无独立图 审计非状态对象','日志职责'),
'UC8':('故障工单','无独立图 管理动作待明确','2-17 候选','工单职责'),
'UC9':('设备、监测协调','2-9、2-10','2-14、2-16','监测、设备适配'),
'UC10':('设备、维护协调候选','待设计 动作触发未明','待设计 动作触发未明','设备交互与维护职责'),
'UC11':('工单、处理协调','2-11、2-12','2-15、2-17','工单职责'),
'INC1':('设备权限关联','2-3、2-4','2-13','权限职责'),
'INC2':('操作日志','2-3、2-4','2-13','日志职责'),
'INC3':('用户、认证对象','2-3至2-6','2-13','认证职责'),
'EXT1':('工单、监测协调','2-9、2-10','2-14、2-17','监测与工单'),
'EXT2':('AI交互对象、外部服务','2-11、2-12','2-15、2-17','AI交互适配'),
'G1':('设备、USB适配候选','2-5、2-6 公共图','无独立图 仅补接入差异','接入、设备适配'),
'G2':('设备、蓝牙适配候选','2-5、2-6 公共图','无独立图 仅补接入差异','接入、设备适配'),
'G3':('设备、Zigbee适配候选','2-5、2-6 公共图','无独立图 仅补接入差异','接入、设备适配')}
rows=[]
for k,i in enumerate(ids):
    ob,inter,act,co=detail[i];rows.append((i,'1.3',f'2.1.3.{k+1}',ob,inter,act,co+'；图2-18/19','用例已定；细化为设计建议'))
table(['用例ID','需求','说明','类或对象','交互图 图号','活动或状态图','构件与部署关联','设计状态'],rows,[1.5,1.0,2.0,3.6,3.2,4.3,5.8,3.2],10)
s=doc.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.PORTRAIT;s.page_width=Cm(21);s.page_height=Cm(29.7);s.left_margin=s.right_margin=Cm(3.175);s.top_margin=s.bottom_margin=Cm(2.54)
h('附录 B 待明确事项')
table(['编号','待明确问题','影响模型'],[
('B01','设备申请是否审批，申请与授权的联系','UC1、UC6、申请类'),('B02','权限粒度、有效期、共享与独占规则','UC2、UC6、INC1、权限类'),('B03','工单管理动作、状态集合和关闭条件','UC8、UC11、图2-17'),('B04','监测周期、异常阈值、未知状态及去重规则','UC9、EXT1、图2-14/16'),('B05','运维动作、执行授权、自动触发和失败恢复','UC10、构件职责'),('B06','日志字段、保留期、记录失败和审计范围','INC2、UC7、操作场景'),('B07','AI提供方、诊断输入、返回形式、超时及脱敏','EXT2、图2-11/12/15/19'),('B08','设备型号、协议适配、USB驱动、蓝牙及Zigbee设施','G1/G2/G3、图2-5/6/19'),('B09','技术栈、数据持久化与主机或网关拓扑','图2-18/19'),('B10','其他入口访问控制、并发与数据一致性策略','所有实现入口')],[1.5,8.2,4.9])
p('以上事项会影响后续细化设计。涉及改变业务范围、角色权限或用例关系的决定，应先确认并同步基准图和项目说明；既定范围内的普通实现细节可结合设备与运行条件选择简单方案。')
h('附录 C 建模依据与图示索引')
p('功能及角色依据为项目AGENTS.md和docs/lab-device-usecase.drawio；章节与图文组织依据为docs/report-writing-standard.md。参考作品为《软件工程专业学籍管理系统》UML课程作品，仅借鉴“需求—用例—静态—动态—部署”的组织方式，不沿用原作者个人资料、原业务或旧工具要求。')
p('图2-1为总体用例图；图2-2为领域分析类图；图2-3至2-12为五组序列图和通信图；图2-13至2-15为三张活动图；图2-16、图2-17为两张候选状态图；图2-18、图2-19为构件图和候选部署图。图号连续，图文对应见附录A。')

# Materialize cross-reference fields without changing their visible text.
for pp in doc.paragraphs:
    if pp.style.name=='Caption':continue
    for r in list(pp.runs):
        txt=r.text
        if not re.search(r'图2-\d+',txt):continue
        parts=re.split(r'(图2-\d+)',txt);r.text='';anchor=r._r
        for part in parts:
            rr=OxmlElement('w:r');tt=OxmlElement('w:t');tt.text=part;rr.append(tt)
            if re.fullmatch(r'图2-\d+',part):
                n=int(part[3:]);f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),f'REF fig2_{n} \\h');f.append(rr);anchor.addnext(f);anchor=f
            else:anchor.addnext(rr);anchor=rr
doc.core_properties.author='';doc.core_properties.last_modified_by='';doc.core_properties.title=TITLE+' UML项目报告';doc.core_properties.subject='需求分析与UML建模';doc.core_properties.comments=''
OUT=ROOT/'docs'/f'{TITLE}-UML项目报告.docx';doc.save(OUT)
(BUILD/'model-check.json').write_text(json.dumps({'actors':actors,'usecases':ids,'relations':edges,'figures':19,'scenes':SCENES},ensure_ascii=False,indent=2),encoding='utf-8')
print(str(OUT))
