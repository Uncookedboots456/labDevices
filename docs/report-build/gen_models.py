"""Regenerate the draw.io sources in docs/models.

Usage: python docs/report-build/gen_models.py
Then export: drawio -x -f png --scale 1.5 --border 10 -o docs/models/<name>.png docs/models/<name>.drawio
"""

"""Generate draw.io sources: class diagram (fig2-2) + activity diagrams (fig2-13/14/15).

Label newlines use the <NL> marker.
"""
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scenes import SCENES  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / 'models'
OUT.mkdir(exist_ok=True)
FONT = 'fontFamily=Noto Sans CJK SC;fontSize=13;'


def t(s):
    return escape(s).replace('&lt;NL&gt;', '&#10;')


class Dia:
    def __init__(self, did, name, w, h):
        self.did, self.name, self.w, self.h = did, name, w, h
        self.cells = []
        self.geo = {}

    def add(self, xml):
        self.cells.append(xml)

    def cell(self, cid, value, style, x, y, w, h, kind='vertex', parent='1'):
        if parent == '1':
            self.geo[cid] = (x, y, w, h)
        self.add('<mxCell id="%s" value="%s" style="%s" %s="1" parent="%s">'
                 '<mxGeometry x="%g" y="%g" width="%g" height="%g" as="geometry"/></mxCell>'
                 % (cid, t(value), style, kind, parent, x, y, w, h))

    def anchor(self, cid, p, side):
        """Style keys pinning one edge end to point p on vertex cid (side: exit/entry)."""
        x, y, w, h = self.geo[cid]
        assert x - 6 <= p[0] <= x + w + 6 and y - 6 <= p[1] <= y + h + 6, \
            '%s: %s end %s is off vertex %s' % (self.did, side, p, cid)
        fx = min(max((p[0] - x) / w, 0), 1)
        fy = min(max((p[1] - y) / h, 0), 1)
        return '{0}X={1:.4g};{0}Y={2:.4g};{0}Dx=0;{0}Dy=0;{0}Perimeter=0;'.format(side, fx, fy)

    def link(self, eid, style, src, dst, p0, p1, pts=()):
        """Edge bound to src/dst vertices, drawn from p0 to p1 through optional waypoints."""
        style += self.anchor(src, p0, 'exit') + self.anchor(dst, p1, 'entry')
        geo = '<mxGeometry relative="1" as="geometry">'
        if pts:
            geo += '<Array as="points">%s</Array>' % ''.join('<mxPoint x="%g" y="%g"/>' % q for q in pts)
        geo += '</mxGeometry>'
        self.add('<mxCell id="%s" style="%s" edge="1" parent="1" source="%s" target="%s">%s</mxCell>'
                 % (eid, style, src, dst, geo))

    def save(self):
        xml = ('<mxfile host="app.diagrams.net"><diagram id="%s" name="%s">'
               '<mxGraphModel dx="1400" dy="1000" grid="0" gridSize="10" guides="1" tooltips="1" '
               'connect="1" arrows="1" fold="1" page="1" pageWidth="%d" pageHeight="%d" math="0" shadow="0">'
               '<root><mxCell id="0"/><mxCell id="1" parent="0"/>%s</root></mxGraphModel></diagram></mxfile>'
               % (self.did, self.name, self.w, self.h, ''.join(self.cells)))
        cells = {c.get('id'): c for c in ET.fromstring(xml).iter('mxCell')}
        for c in cells.values():
            if c.get('edge') != '1':
                continue
            for end in ('source', 'target'):
                ref = cells.get(c.get(end))
                assert ref is not None and ref.get('vertex') == '1', \
                    '%s: edge %s has no valid %s' % (self.did, c.get('id'), end)
        p = OUT / ('%s.drawio' % self.did)
        p.write_text(xml, encoding='utf-8')
        return p


# ------------------------------------------------------------------ class diagram
BOX = ('swimlane;fontStyle=1;align=center;verticalAlign=middle;startSize=28;html=1;fillColor=#F5F9FF;'
       'strokeColor=#3A6EA5;fontColor=#1B3A5C;' + FONT)
ATTR = ('text;html=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;fillColor=#FFFFFF;'
        'strokeColor=#3A6EA5;' + FONT)
OPS = ('text;html=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;fillColor=#F5F9FF;'
       'strokeColor=#3A6EA5;fontStyle=2;' + FONT)
ASSOC = 'endArrow=none;html=1;rounded=0;strokeColor=#1B3A5C;strokeWidth=1.5;' + FONT
ELAB = ('edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];'
        'labelBackgroundColor=#FFFFFF;' + FONT)
NOTE = ('shape=note;whiteSpace=wrap;html=1;size=14;align=left;verticalAlign=top;spacingLeft=8;'
        'spacingTop=6;fillColor=#FFF9C4;strokeColor=#B8A000;' + FONT)


def klass(d, cid, name, attrs, ops, x, y, w, ah, oh):
    d.cell(cid, name, BOX, x, y, w, 28 + ah + oh)
    d.cell(cid + '_a', attrs, ATTR, 0, 28, w, ah, parent=cid)
    d.cell(cid + '_o', ops, OPS, 0, 28 + ah, w, oh, parent=cid)


def assoc(d, eid, a, b, la, lb):
    d.add('<mxCell id="%s" style="%s" edge="1" parent="1" source="%s" target="%s">'
          '<mxGeometry relative="1" as="geometry"/></mxCell>' % (eid, ASSOC, a, b))
    for suf, val, x in (('a', la, -0.86), ('b', lb, 0.86)):
        d.add('<mxCell id="%s%s" value="%s" style="%s" vertex="1" connectable="0" parent="%s">'
              '<mxGeometry x="%s" y="-12" relative="1" as="geometry"><mxPoint as="offset"/></mxGeometry>'
              '</mxCell>' % (eid, suf, t(val), ELAB, eid, x))


d = Dia('class-diagram', '类图 图2-2', 1720, 1240)
klass(d, 'u', '用户', '用户标识<NL>角色集合', '提供身份上下文', 40, 330, 260, 66, 46)
klass(d, 'p', '设备权限关联', '用户标识<NL>设备标识<NL>授权人（待明确）<NL>授权描述（待明确）',
      '判定访问范围（INC1）<NL>登记授权（UC6）', 640, 40, 340, 104, 60)
klass(d, 'dd', '设备', '设备标识<NL>接入类型<NL>状态摘要', '接收操作<NL>提供状态', 1390, 330, 260, 76, 60)
klass(d, 'r', '设备使用申请', '申请标识<NL>申请人<NL>目标设备', '提交申请', 640, 350, 340, 76, 46)
klass(d, 'l', '操作日志', '操作主体<NL>目标设备<NL>操作结果<NL>字段待明确',
      '记录操作（INC2）<NL>提供审计（UC7）', 640, 640, 340, 96, 60)
klass(d, 'k', '故障工单', '来源（手工/监测）<NL>关联设备<NL>报修人<NL>处理信息<NL>状态待明确',
      '登记故障<NL>保存处理信息（UC11）', 630, 920, 380, 110, 60)
assoc(d, 'e1', 'u', 'p', '1 被授权人', '0..*')
assoc(d, 'e2', 'p', 'dd', '0..*', '1')
assoc(d, 'e3', 'u', 'r', '1', '0..*')
assoc(d, 'e4', 'r', 'dd', '0..*', '1')
assoc(d, 'e5', 'u', 'l', '1', '0..*')
assoc(d, 'e6', 'dd', 'l', '1', '0..*')
assoc(d, 'e7', 'dd', 'k', '1 关联设备', '0..*')
assoc(d, 'e8', 'u', 'k', '0..1 报修人', '0..*')
d.cell('note', '这些是分析类，不是已实现的代码类或数据库表。<NL>属性与多重性为分析设计建议，'
               '标注“待明确”的内容尚未确认。<NL>权限关联同时服务 UC6 分配与 INC1 校验，'
               '<NL>但数据联系不构成用例间的 include 关系。<NL>'
               'UC10 运维动作与 EXT2 诊断建议尚无已确认的数据概念，暂不建类。',
       NOTE, 40, 720, 460, 180)
print(d.save())

# --------------------------------------------------------------- activity helper
LANE = 'rounded=0;html=1;fillColor=#FFFFFF;strokeColor=#9AA5B1;verticalAlign=top;'
LANE_HEAD = 'rounded=0;html=1;fillColor=#F2F4F7;strokeColor=#9AA5B1;'
LANE_TITLE = 'text;html=1;fontStyle=1;align=center;verticalAlign=middle;' + FONT
ACT = ('rounded=1;arcSize=24;whiteSpace=wrap;html=1;fillColor=#F5F9FF;strokeColor=#3A6EA5;'
       'fontColor=#1B3A5C;' + FONT)
DEC = 'rhombus;whiteSpace=wrap;html=1;fillColor=#FFF4E5;strokeColor=#B26B00;' + FONT
MERGE = 'rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1B3A5C;' + FONT
START = 'ellipse;html=1;fillColor=#000000;strokeColor=#000000;'
END_OUT = 'ellipse;html=1;fillColor=none;strokeColor=#1B3A5C;strokeWidth=2;'
END_IN = 'ellipse;html=1;fillColor=#1B3A5C;strokeColor=#1B3A5C;'
FLOW = ('edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=open;endSize=12;'
        'strokeColor=#1B3A5C;strokeWidth=1.5;' + FONT)
FLAB = ('edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];'
        'labelBackgroundColor=#FFFFFF;' + FONT)


class Act:
    LANE_W = 400

    def __init__(self, did, name, lanes, height):
        self.d = Dia(did, name, 60 + self.LANE_W * len(lanes), height)
        self.i = {n: k for k, n in enumerate(lanes)}
        self.geo = {}
        self.nodes, self.edges = set(), []
        for n, k in self.i.items():
            x = 20 + self.LANE_W * k
            self.d.cell('lane%d' % k, '', LANE, x, 40, self.LANE_W, height - 80)
            self.d.cell('laneh%d' % k, '', LANE_HEAD, x, 0, self.LANE_W, 40)
            self.d.cell('lanet%d' % k, n, LANE_TITLE, x, 0, self.LANE_W, 36)

    def cx(self, lane, w, dx):
        return 20 + self.LANE_W * self.i[lane] + (self.LANE_W - w) / 2 + dx

    def box(self, nid, lane, y, text, w=230, h=76, dx=0, style=ACT):
        self.nodes.add(nid)
        x = self.cx(lane, w, dx)
        self.geo[nid] = (x, y, w, h)
        self.d.cell(nid, text, style, x, y, w, h)

    def act(self, nid, lane, y, text, w=230, h=76, dx=0):
        self.box(nid, lane, y, text, w, h, dx, ACT)

    def dec(self, nid, lane, y, text, w=200, h=120, dx=0):
        self.box(nid, lane, y, text, w, h, dx, DEC)

    def merge(self, nid, lane, y, s=44, dx=0):
        self.box(nid, lane, y, '', s, s, dx, MERGE)

    def dot(self, nid, lane, y, w, style, dx=0):
        x = self.cx(lane, w, dx)
        self.geo[nid] = (x, y, w, w)
        self.d.cell(nid, '', style, x, y, w, w)

    def final(self, nid, lane, y, dx=0):
        self.dot(nid, lane, y, 32, END_OUT, dx)
        x, yy, _, _ = self.geo[nid]
        self.d.cell(nid + 'i', '', END_IN, x + 7, yy + 7, 18, 18)

    def note(self, nid, lane, y, text, w=300, h=96, dx=0):
        self.box(nid, lane, y, text, w, h, dx, NOTE)
        self.nodes.discard(nid)

    def flow(self, eid, src, dst, label='', exit='b', entry='t', pts=(), lx=0.5, ly=-12, ox=0, oy=0):
        self.edges.append((src, dst))
        px, py = {'l': (0, 0.5), 'r': (1, 0.5), 't': (0.5, 0), 'b': (0.5, 1)}[exit]
        qx, qy = {'l': (0, 0.5), 'r': (1, 0.5), 't': (0.5, 0), 'b': (0.5, 1)}[entry]
        style = (FLOW + 'exitX=%g;exitY=%g;exitDx=0;exitDy=0;entryX=%g;entryY=%g;'
                        'entryDx=0;entryDy=0;' % (px, py, qx, qy))
        geo = '<mxGeometry relative="1" as="geometry">'
        if pts:
            geo += '<Array as="points">%s</Array>' % ''.join('<mxPoint x="%g" y="%g"/>' % p for p in pts)
        geo += '</mxGeometry>'
        self.d.add('<mxCell id="%s" style="%s" edge="1" parent="1" source="%s" target="%s">%s</mxCell>'
                   % (eid, style, src, dst, geo))
        if label:
            self.d.add('<mxCell id="%sl" value="%s" style="%s" vertex="1" connectable="0" parent="%s">'
                       '<mxGeometry x="%g" y="%g" relative="1" as="geometry"><mxPoint x="%g" y="%g"/>'
                       '</mxGeometry></mxCell>' % (eid, t(label), FLAB, eid, lx, ly, ox, oy))

    def save(self):
        srcs = {a for a, b in self.edges}
        dsts = {b for a, b in self.edges}
        no_in = sorted(n for n in self.nodes - {'s'} if n not in dsts)
        no_out = sorted(n for n in self.nodes if not n.startswith('e') and n not in srcs)
        assert not no_in, 'no incoming: %s' % no_in
        assert not no_out, 'no outgoing: %s' % no_out
        return self.d.save()


# ------------------------------------------------------- UC2 操作设备 (fig2-13)
a = Act('activity-uc2-operate', '活动图 UC2 操作设备', ['实验人员（含管理员）', '系统处理', '外部设备'], 1600)
a.dot('s', '实验人员（含管理员）', 80, 26, START)
a.act('p1', '实验人员（含管理员）', 150, '发起设备操作', w=260)
a.act('d1', '系统处理', 150, '执行登录认证（INC3）', w=300)
a.dec('c1', '系统处理', 280, '认证通过？')
a.act('d2', '系统处理', 440, '校验设备权限（INC1）', w=300)
a.dec('c2', '系统处理', 560, '权限允许？')
a.merge('m2', '实验人员（含管理员）', 380)
a.act('p2', '实验人员（含管理员）', 440, '接收拒绝结果<NL>不向设备下发指令', w=260, h=86)
a.final('e1', '实验人员（含管理员）', 600)
a.act('d3', '系统处理', 720, '经适配向设备下发操作指令', w=300)
a.act('v1', '外部设备', 720, '执行设备指令', w=240)
a.dec('c3', '系统处理', 840, '设备返回<NL>可确定结果？', w=210, h=130)
a.merge('m1', '系统处理', 1000)
a.act('d4', '系统处理', 1080, '记录操作日志（INC2）', w=300)
a.dec('c4', '系统处理', 1180, '日志写入成功？')
a.act('p5', '实验人员（含管理员）', 1360, '接收执行结果<NL>与记录情况', w=180, h=86, dx=-100)
a.act('p6', '实验人员（含管理员）', 1360, '接收记录失败<NL>单独提示', w=180, h=86, dx=100)
a.final('e2', '实验人员（含管理员）', 1500)
a.flow('f1', 's', 'p1')
a.flow('f2', 'p1', 'd1', exit='r', entry='l')
a.flow('f3', 'd1', 'c1')
a.flow('f4', 'c1', 'd2', '[是]', lx=0.5, ly=-12, ox=52)
a.flow('f5', 'c1', 'm2', '[否]', exit='l', entry='t', pts=[(220, 340)], lx=0.24, ly=-14)
a.flow('f6', 'd2', 'c2')
a.flow('f7', 'c2', 'd3', '[是]', lx=0.5, ly=-12, ox=52)
a.flow('f8', 'c2', 'm2', '[否]', exit='l', entry='r', pts=[(375, 620), (375, 402)], lx=0.62, ly=-16)
a.flow('f20', 'm2', 'p2')
a.flow('f9', 'd3', 'v1', exit='r', entry='l')
a.flow('f10', 'v1', 'c3', exit='b', entry='r', pts=[(1000, 905)], lx=0.78, ly=-16)
a.flow('f11', 'c3', 'm1', '[是]', lx=0.5, ly=-14)
a.flow('f12', 'c3', 'm1', '[否]', exit='l', entry='l', pts=[(448, 905), (448, 1022)],
       lx=0.72, ly=-16)
a.flow('f13', 'm1', 'd4')
a.flow('f14', 'd4', 'c4')
a.flow('f15', 'c4', 'p5', '[是]', exit='l', entry='t', pts=[(120, 1240)], lx=0.18, ly=-14, ox=-40)
a.flow('f19', 'p2', 'e1')
a.flow('f16', 'c4', 'p6', '[否]', exit='r', entry='t', pts=[(760, 1240), (760, 1320), (320, 1320)],
       lx=0.3, ly=-16)
a.flow('f17', 'p5', 'e2', exit='b', entry='l', pts=[(120, 1516)])
a.flow('f18', 'p6', 'e2', exit='b', entry='r', pts=[(320, 1516)])
a.note('n1', '外部设备', 1000, '设备不可达时记录能够确定的<NL>失败或未知结果，不宣称成功。', w=280, h=90)
print(a.save())

# ---------------------------------------------------- UC9 监测设备状态 (fig2-14)
m = Act('activity-uc9-monitor', '活动图 UC9 监测设备状态', ['运维人员', '系统处理', '异构设备'], 1300)
m.dot('s', '运维人员', 80, 26, START)
m.act('p1', '运维人员', 150, '参与状态监测')
m.act('d1', '系统处理', 150, '请求设备状态', w=240)
m.act('v1', '异构设备', 150, '提供状态信息', w=240)
m.dec('c1', '系统处理', 280, '取得状态？')
m.act('p2', '运维人员', 440, '接收状态未知结果<NL>不自动建单', w=240, h=86)
m.final('e1', '运维人员', 570)
m.act('d2', '系统处理', 440, '按判据评估取得的状态', w=300)
m.dec('c2', '系统处理', 560, '检测到异常？')
m.act('p3', '运维人员', 720, '接收监测结果', w=240)
m.act('d3', '系统处理', 720, '自动生成故障工单（EXT1）', w=320)
m.dec('c3', '系统处理', 850, '建单保存成功？')
m.merge('m1', '运维人员', 1000)
m.act('p4', '运维人员', 1070, '接收监测与建单结果', w=260)
m.final('e2', '运维人员', 1200)
m.flow('f1', 's', 'p1')
m.flow('f2', 'p1', 'd1', exit='r', entry='l')
m.flow('f3', 'd1', 'v1', exit='r', entry='l')
m.flow('f4', 'v1', 'c1', '返回状态', exit='b', entry='r', pts=[(1070, 340)], lx=0.7, ly=-14)
m.flow('f5', 'c1', 'p2', '[否]', exit='l', entry='t', pts=[(200, 340)], lx=0.24, ly=-14)
m.flow('f6', 'c1', 'd2', '[是]', exit='b', entry='t', lx=0.5, ly=-12, ox=52)
m.flow('f7', 'd2', 'c2')
m.flow('f8', 'c2', 'p3', '[正常]', exit='l', entry='r', pts=[(340, 620), (340, 758)], lx=0.1, ly=-14)
m.flow('f9', 'c2', 'd3', '[异常]', lx=0.5, ly=-16)
m.flow('f10', 'd3', 'c3')
m.flow('f11', 'c3', 'm1', '[成功]', exit='l', entry='t', pts=[(200, 910)], lx=0.26, ly=-14)
m.flow('f12', 'c3', 'm1', '[失败]', exit='b', entry='r', pts=[(600, 1022)], lx=0.6, ly=-16)
m.flow('f13', 'm1', 'p4')
m.flow('f14', 'p4', 'e2')
m.flow('f15', 'p3', 'e2', exit='l', entry='l', pts=[(40, 758), (40, 1216)])
m.flow('f16', 'p2', 'e1')
m.note('n1', '系统处理', 1060, '通信失败记为状态未知，不进入异常判断；<NL>异常阈值与建单去重待明确。',
       w=300, h=100)
m.note('n2', '异构设备', 720, '自动建单不触发<NL>自动化运维（UC10）', w=260, h=80)
print(m.save())

# ----------------------------------------------- UC11 处理故障工单 (fig2-15)
ai = Act('activity-uc11-ticket-ai', '活动图 UC11 处理故障工单', ['运维人员', '系统处理', 'AI Agent服务'], 1660)
ai.dot('s', '运维人员', 80, 26, START)
ai.act('p1', '运维人员', 150, '打开待处理工单')
ai.act('d1', '系统处理', 150, '展示工单故障上下文', w=280)
ai.dec('c1', '运维人员', 280, '需要 AI 辅助？<NL>EXT2：需要辅助诊断', w=220, h=130)
ai.act('d2', '系统处理', 470, '准备并发送诊断上下文', w=300)
ai.act('a1', 'AI Agent服务', 470, '分析故障<NL>返回诊断建议', w=260, h=86)
ai.dec('c2', '系统处理', 620, '取得有效建议？')
ai.merge('m2', '系统处理', 765)
ai.act('d3', '系统处理', 835, '展示诊断建议或辅助不可用', w=300, h=86)
ai.merge('m1', '运维人员', 940)
ai.act('p2', '运维人员', 1020, '人工判断并处理', w=240)
ai.act('p3', '运维人员', 1140, '提交处理信息', w=240)
ai.act('d5', '系统处理', 1140, '保存处理信息', w=280)
ai.dec('c3', '系统处理', 1270, '保存成功？')
ai.merge('m3', '运维人员', 1350)
ai.act('p4', '运维人员', 1410, '接收保存结果<NL>失败时提示未记录', w=260, h=86)
ai.final('e1', '运维人员', 1560)
ai.flow('f1', 's', 'p1')
ai.flow('f2', 'p1', 'd1', exit='r', entry='l')
ai.flow('f3', 'd1', 'c1', pts=[(600, 250), (200, 250)])
ai.flow('f4', 'c1', 'd2', '[请求]', exit='r', entry='l', pts=[(455, 345)], lx=0.55, ly=-14)
ai.flow('f5', 'd2', 'a1', exit='r', entry='l')
ai.flow('f6', 'a1', 'c2', exit='b', entry='r', pts=[(1030, 670)], lx=0.72, ly=-14)
ai.flow('f7', 'c2', 'm2', '[是]', lx=0.5, ly=-12, ox=28)
ai.flow('f8', 'c2', 'm2', '[否]', exit='l', entry='l', pts=[(430, 680), (430, 787)], lx=0.3, ly=-14)
ai.flow('f18', 'm2', 'd3')
ai.flow('f9', 'd3', 'm1', exit='l', entry='r', pts=[(385, 878), (385, 962)], lx=0.52, ly=-14)
ai.flow('f10', 'c1', 'm1', '[未请求]', exit='b', entry='t', lx=0.28, ly=-16)
ai.flow('f11', 'm1', 'p2')
ai.flow('f12', 'p2', 'p3')
ai.flow('f13', 'p3', 'd5', exit='r', entry='l')
ai.flow('f14', 'd5', 'c3')
ai.flow('f15', 'c3', 'm3', '[是]', exit='l', entry='t', pts=[(220, 1330)], lx=0.16, ly=-14)
ai.flow('f16', 'c3', 'm3', '[否]', exit='b', entry='r', pts=[(620, 1400), (340, 1400), (340, 1372)], lx=0.42, ly=-16)
ai.flow('f19', 'm3', 'p4')
ai.flow('f17', 'p4', 'e1')
ai.note('n1', 'AI Agent服务', 780, 'AI 只提供建议，不执行设备动作；<NL>建议不等于工单关闭。', w=260, h=90)
print(ai.save())

# ============================================================ sequence diagrams
LIFELINE = ('shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=0;'
            'startSize=56;fillColor=#F5F9FF;strokeColor=#3A6EA5;fontColor=#1B3A5C;' + FONT)
MSGROW = 'endArrow=open;endSize=11;html=1;rounded=0;strokeColor=#1B3A5C;strokeWidth=1.5;' + FONT
FRAME = 'rounded=0;html=1;fillColor=none;strokeColor=#666666;' + FONT
FRAME_LABEL = 'text;html=1;align=left;verticalAlign=middle;fillColor=#FFFFFF;strokeColor=none;' + FONT

SCENE_META = {
    '操作设备': ('uc2-operate', '图2-3', '图2-4', (5, 9, 'opt [校验通过]')),
    '接入设备': ('uc5-connect', '图2-5', '图2-6', (5, 9, 'opt [认证通过]')),
    '人工故障报修': ('uc4-report', '图2-7', '图2-8', None),
    '异常监测与自动建单': ('uc9-monitor', '图2-9', '图2-10', (7, 8, 'opt [监测到异常]')),
    '工单处理与按需AI辅助': ('uc11-ticket-ai', '图2-11', '图2-12', (6, 12, 'opt [运维人员请求AI辅助]')),
}


def message(d, eid, src, dst, p0, p1, dashed=False, lw=()):
    d.link(eid, MSGROW + ('dashed=1;' if dashed else ''), src, dst, p0, p1, lw)


def txtcell(d, cid, value, x, y, w, h=20, align='center'):
    cell = ('<mxCell id="%s" value="%s" style="text;html=1;align=%s;verticalAlign=middle;'
            'labelBackgroundColor=#FFFFFF;' + FONT + '" vertex="1" connectable="0" parent="1">'
            '<mxGeometry x="%g" y="%g" width="%g" height="%g" as="geometry"/></mxCell>')
    d.add(cell % (cid, t(value), align, x, y, w, h))


def msg_label(d, eid, x, y, text, w=260):
    txtcell(d, '%sl' % eid, text, x - w / 2, y - 22, w)


def is_reply(text):
    return any(k in text for k in ('返回', '展示', '提供'))


def sequence(sc):
    slug, fig, _, frame = SCENE_META[sc['key']]
    objs, msgs = sc['objs'], sc['msgs']
    gap = 186 if len(objs) > 5 else 205
    xs = [110 + i * gap for i in range(len(objs))]
    row0, step = 220, 48
    ys, cur = [], row0
    for i, (a, b, _) in enumerate(msgs):
        if frame and i == frame[0] - 1 and i and msgs[i - 1][0] == msgs[i - 1][1]:
            cur += 44  # keep a self-message loop and the frame label apart
        ys.append(cur)
        cur += step * (1.5 if a == b else 1.0)
    height = cur + 46
    width = xs[-1] + 120
    d = Dia('seq-' + slug, '序列图 %s %s' % (fig, sc['key']), width, height)
    for i, o in enumerate(objs):
        d.cell('lif%d' % i, o, LIFELINE, xs[i] - 86, 40, 172, height - 90)
    if frame:
        first, last, text = frame
        top = ys[first - 1] - 46
        bottom = ys[last - 1] + 26
        span = msgs[first - 1:last]
        left = min(min(xs[a], xs[b]) for a, b, _ in span) - 100
        right = max(max(xs[a], xs[b]) for a, b, _ in span) + 100
        d.cell('frame', '', FRAME, left, top, right - left, bottom - top)
        d.cell('framel', text, FRAME_LABEL, left + 8, top + 1, 300, 22)
    for k, (a, b, text) in enumerate(msgs):
        y = ys[k]
        eid = 'm%d' % k
        la, lb = 'lif%d' % a, 'lif%d' % b
        if a == b:
            message(d, eid, la, la, (xs[a] + 8, y), (xs[a] + 8, y + 26), is_reply(text),
                    lw=[(xs[a] + 74, y), (xs[a] + 74, y + 26)])
            txtcell(d, '%sl' % eid, text, xs[a] + 84, y + 4, 210, align='left')
        else:
            message(d, eid, la, lb, (xs[a], y), (xs[b], y), is_reply(text))
            msg_label(d, eid, (xs[a] + xs[b]) / 2, y, text)
    return d.save()


# ========================================================= communication diagrams
OBJ = ('rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F9FF;strokeColor=#3A6EA5;'
       'fontColor=#1B3A5C;' + FONT)
COMM_POS = {
    4: [(140, 145), (455, 145), (775, 145), (775, 435)],
    5: [(160, 140), (520, 140), (900, 140), (900, 450), (520, 450)],
    6: [(160, 140), (520, 140), (520, 400), (900, 140), (900, 400), (900, 640)],
    7: [(160, 140), (520, 140), (520, 400), (900, 140), (900, 400), (900, 640), (160, 640)],
}
COMM_SIZE = (168, 74)


def line_rect(center, p, u, w, h, forward=True):
    hw, hh = w / 2, h / 2
    ts = []
    if u[0]:
        ts += [(center[0] - hw - p[0]) / u[0], (center[0] + hw - p[0]) / u[0]]
    if u[1]:
        ts += [(center[1] - hh - p[1]) / u[1], (center[1] + hh - p[1]) / u[1]]
    ok = [t for t in ts
          if abs(p[1] + t * u[1] - center[1]) <= hh + 1e-6
          and abs(p[0] + t * u[0] - center[0]) <= hw + 1e-6]
    cand = [t for t in ok if (t > 0 if forward else t < 0)]
    t = (min(cand) if forward else max(cand)) if cand else 0
    return p[0] + t * u[0], p[1] + t * u[1]


def border_hit(c, other, w, h):
    dx, dy = other[0] - c[0], other[1] - c[1]
    t = min((w / 2) / abs(dx) if dx else 1e9, (h / 2) / abs(dy) if dy else 1e9)
    return c[0] + dx * t, c[1] + dy * t


def communication(sc):
    slug, seqfig, fig, _ = SCENE_META[sc['key']]
    objs, msgs = sc['objs'], sc['msgs']
    pos = COMM_POS[len(objs)]
    w, h = COMM_SIZE
    width = max(p[0] for p in pos) + w / 2 + 70
    height = max(p[1] for p in pos) + h / 2 + 70
    d = Dia('comm-' + slug, '通信图 %s %s' % (fig, sc['key']), width, height)
    d.cell('legend', '编号与%s逐条一致；消息内容见该场景的序列图' % seqfig,
           'text;html=1;align=left;verticalAlign=middle;' + FONT, 40, height - 44, 640, 26)
    for i, o in enumerate(objs):
        d.cell('obj%d' % i, o, OBJ, pos[i][0] - w / 2, pos[i][1] - h / 2, w, h)
    pairs = {}
    for a, b, text in msgs:
        pairs.setdefault((min(a, b), max(a, b)), []).append((a, b, text))
    for (a, b), group in sorted(pairs.items()):
        if a == b:
            x, y = pos[a]
            nb = [pos[m[1]] if m[0] == a else pos[m[0]] for m in msgs
                  if m[0] != m[1] and a in (m[0], m[1])]
            sx = sum(q[0] - x for q in nb)
            sy = sum(q[1] - y for q in nb)
            side = min(((-sx, 'left'), (sx, 'right'), (-sy, 'top'), (sy, 'bottom')))[1]
            eid = 'self%d' % a
            if side in ('left', 'right'):
                sgn = 1 if side == 'right' else -1
                bx = x + sgn * w / 2
                p0, p1 = (bx + 4 * sgn, y - 12), (bx + 4 * sgn, y + 14)
                wp = [(bx + 62 * sgn, y - 12), (bx + 62 * sgn, y + 14)]
                lx, ly, al = (bx + 70 * sgn, y - 30, 'left') if sgn > 0 else (bx - 250, y - 30, 'left')
            else:
                sgn = 1 if side == 'bottom' else -1
                by = y + sgn * h / 2
                p0, p1 = (x - 12, by + 4 * sgn), (x + 14, by + 4 * sgn)
                wp = [(x - 12, by + 50 * sgn), (x + 14, by + 50 * sgn)]
                lx, ly, al = (x + 22, by + 8, 'left') if sgn > 0 else (x + 22, by - 66, 'left')
            message(d, eid, 'obj%d' % a, 'obj%d' % a, p0, p1, lw=wp)
            nos = ', '.join(m[2].split(' ')[0] for m in group)
            txtcell(d, '%sl' % eid, nos + ' 自身判断', lx, ly, 180, 22, align=al)
            continue
        pa, pb = pos[a], pos[b]
        dx, dy = pb[0] - pa[0], pb[1] - pa[1]
        ln = math.hypot(dx, dy)
        ux, uy, nx, ny = dx / ln, dy / ln, -dy / ln, dx / ln
        dirs = {}
        for a2, b2, text in group:
            if a2 == b2:
                continue
            dirs.setdefault((a2, b2) == (a, b), []).append((a2, b2, text))
        for idx, (fwd, ms) in enumerate(sorted(dirs.items(), reverse=True)):
            sgn = 1 if fwd else -1
            off = 18 * sgn
            u = (ux, uy)
            p0 = line_rect(pa, (pa[0] + nx * off, pa[1] + ny * off), u, w, h, True)
            p1 = line_rect(pb, (pb[0] + nx * off, pb[1] + ny * off), u, w, h, False)
            src, dst = 'obj%d' % a, 'obj%d' % b
            if not fwd:
                p0, p1, src, dst = p1, p0, dst, src
            eid = 'dir%d%d%d' % (a, b, idx)
            message(d, eid, src, dst, p0, p1)
            nos = ', '.join(m[2].split(' ')[0] for m in ms)
            lx = (p0[0] + p1[0]) / 2 + nx * 14 * sgn - 45
            ly = (p0[1] + p1[1]) / 2 + ny * 14 * sgn - 11
            txtcell(d, '%sl' % eid, nos, lx, ly, 90, 22)
    return d.save()


for _sc in SCENES:
    print(sequence(_sc))
    print(communication(_sc))

# ================================================== state / component / deploy
STATE = ('rounded=1;arcSize=18;whiteSpace=wrap;html=1;fillColor=#F5F9FF;strokeColor=#3A6EA5;'
         'fontColor=#1B3A5C;' + FONT)
COMP = ('rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F9FF;strokeColor=#3A6EA5;'
        'fontColor=#1B3A5C;' + FONT)
ARTIFACT = ('shape=module;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3A6EA5;'
            'fontColor=#1B3A5C;' + FONT)
NODE = ('rounded=0;whiteSpace=wrap;html=1;verticalAlign=top;fillColor=#FFFFFF;strokeColor=#1B3A5C;'
        'strokeWidth=2;fontColor=#1B3A5C;fontStyle=1;' + FONT)
ARROW = ('endArrow=open;endSize=11;html=1;rounded=0;strokeColor=#1B3A5C;strokeWidth=1.5;' + FONT)
DASH = 'dashed=1;' + ARROW


def edge(d, eid, src, dst, p0, p1, label='', pts=(), lx=None, ly=None, dashed=False, w=220,
         align='center', h=22):
    d.link(eid, DASH if dashed else ARROW, src, dst, p0, p1, pts)
    if label:
        cx = lx if lx is not None else (p0[0] + p1[0]) / 2
        cy = ly if ly is not None else (p0[1] + p1[1]) / 2 - 22
        txtcell(d, eid + 'l', label, cx - w / 2 if align == 'center' else cx, cy, w, h, align)


def device_state():
    d = Dia('state-device', '状态图 图2-16 设备状态观测摘要', 1320, 800)
    d.cell('s', '', START, 60, 300, 26, 26)
    d.cell('u', '未知', STATE, 170, 265, 180, 90)
    d.cell('n', '正常', STATE, 540, 265, 180, 90)
    d.cell('e', '异常', STATE, 900, 265, 180, 90)
    edge(d, 't0', 's', 'u', (86, 313), (170, 313), '')
    edge(d, 't1', 'u', 'n', (350, 310), (540, 310), '有效采样 [结果正常]', lx=445, ly=250, w=240)
    edge(d, 't2', 'n', 'e', (720, 310), (900, 310), '新采样 [异常]', lx=810, ly=250, w=200)
    edge(d, 't3', 'e', 'n', (930, 355), (690, 355), '新采样 [正常]', pts=[(930, 400), (690, 400)],
         lx=810, ly=418, w=200)
    edge(d, 't4', 'n', 'u', (630, 265), (240, 265), '状态采样 [通信失败或不可判定]',
         pts=[(630, 195), (240, 195)], lx=430, ly=173, w=300)
    edge(d, 't5', 'e', 'u', (990, 265), (300, 265), '状态采样 [通信失败或不可判定]',
         pts=[(990, 120), (300, 120)], lx=660, ly=98, w=300)
    edge(d, 't6', 'u', 'e', (260, 355), (990, 355), '有效采样 [结果异常]', pts=[(260, 520), (990, 520)],
         lx=625, ly=498, w=240)
    d.cell('note', '对象是设备状态的观测摘要，不是设备接入生命周期；'
                   '<NL>该摘要随设备持续采样更新，因此不设终止状态。'
                   '<NL>进入异常态对应 UC9 的“检测到异常”扩展点条件；'
                   '<NL>异常阈值、通信失败是否算异常、建单去重策略均待明确。',
           NOTE, 200, 600, 780, 130)
    return d.save()


def ticket_state():
    d = Dia('state-ticket', '状态图 图2-17 故障工单信息', 1290, 660)
    d.cell('s', '', START, 40, 280, 26, 26)
    d.cell('a', '已登记', STATE, 290, 245, 190, 90)
    d.cell('b', '处理中', STATE, 660, 245, 190, 90)
    d.cell('c', '处理信息已记录', STATE, 1030, 245, 200, 90)
    edge(d, 't1', 's', 'a', (66, 293), (290, 293), '提交报修或异常建单 [登记成功]', lx=178, ly=262, w=220)
    edge(d, 't2', 'a', 'b', (480, 290), (660, 290), '开始处理', lx=570, ly=262, w=160)
    edge(d, 't3', 'b', 'c', (850, 290), (1030, 290), '提交处理信息<NL>[保存成功]', lx=940, ly=244, w=170,
         h=42)
    edge(d, 't4', 'c', 'b', (1130, 335), (755, 335), '继续补充处理信息',
         pts=[(1130, 450), (755, 450)], lx=942, ly=424, w=200)
    edge(d, 't5', 'b', 'b', (720, 245), (790, 245), '请求 AI 辅助 [需要辅助诊断] / 取得建议或报告失败',
         pts=[(720, 175), (790, 175)], lx=755, ly=148, w=380)
    d.cell('note', '候选信息生命周期：未规定关闭状态与审批流，'
                   '<NL>关闭条件满足前不设终止状态。'
                   '<NL>AI 辅助不推进状态；工单最终状态集与关闭条件待明确。',
           NOTE, 290, 520, 660, 100)
    return d.save()


def component():
    d = Dia('component', '构件图 图2-18', 1340, 800)
    boxes = {
        'ui': ('«component»<NL>用户交互', 50, 150, 280, 120),
        'use': ('«component»<NL>设备使用与接入', 450, 70, 340, 120),
        'perm': ('«component»<NL>权限与日志', 450, 300, 340, 120),
        'mon': ('«component»<NL>状态监测、运维与工单', 450, 530, 340, 120),
        'dev': ('«component»<NL>设备交互适配', 930, 70, 300, 120),
        'ai': ('«component»<NL>AI交互适配', 930, 530, 300, 120),
    }
    for k, (txt, x, y, w, h) in boxes.items():
        d.cell(k, txt, COMP, x, y, w, h)
    edge(d, 'd1', 'ui', 'use', (330, 170), (450, 170), '请求使用或接入', dashed=True, lx=390, ly=144, w=120)
    edge(d, 'd2', 'ui', 'mon', (120, 270), (450, 590), '监测、运维或工单请求', pts=[(120, 590)],
         dashed=True, lx=285, ly=566, w=200)
    edge(d, 'd3', 'use', 'perm', (620, 190), (620, 300), '身份 权限 日志', dashed=True, lx=632, ly=234,
         w=140, align='left')
    edge(d, 'd7', 'ui', 'perm', (230, 270), (450, 360), '权限分配或日志审计请求', pts=[(230, 360)],
         dashed=True, lx=340, ly=336, w=220)
    edge(d, 'd4', 'use', 'dev', (790, 130), (930, 130), '设备调用', dashed=True, lx=860, ly=100, w=160)
    edge(d, 'd5', 'mon', 'dev', (790, 560), (930, 160), '状态及运维交互', pts=[(860, 560), (860, 160)],
         dashed=True, lx=870, ly=340, w=140, align='left')
    edge(d, 'd6', 'mon', 'ai', (790, 620), (930, 620), '[请求AI辅助]', dashed=True, lx=860, ly=596, w=140)
    d.cell('note', '构件按职责划分，不意味独立进程或微服务；'
                   '<NL>部署节点、数据库位置与 AI 服务提供方仍待明确。',
           NOTE, 60, 660, 640, 80)
    return d.save()


def deploy():
    d = Dia('deploy', '部署图 图2-19', 1340, 830)
    d.cell('term', '«device»<NL>人员终端<NL>交互客户端', COMP, 40, 150, 200, 140)
    d.cell('host', '«device» 候选管理主机<NL>软路由或局域网 Linux 主机（方案待定）', NODE, 360, 50, 440, 620)
    d.cell('app', '«artifact»<NL>设备管理应用<NL>含逻辑构件', ARTIFACT, 400, 220, 360, 150)
    d.cell('db', '«artifact»<NL>逻辑数据存储（位置待定）', ARTIFACT, 400, 430, 360, 120)
    d.cell('dev', '«device»<NL>异构设备<NL>USB / 蓝牙 / Zigbee<NL>适配或网关位置待定', COMP, 900, 80, 300, 220)
    d.cell('ai', '«node»<NL>AI Agent 服务<NL>位置与协议待明确', COMP, 900, 470, 300, 180)
    edge(d, 'd1', 'term', 'host', (240, 220), (360, 220), '局域网<NL>（协议待定）', lx=300, ly=174, w=110,
         h=42)
    edge(d, 'd2', 'app', 'dev', (760, 260), (900, 260), '设备通信', lx=830, ly=232, w=160)
    edge(d, 'd3', 'app', 'ai', (760, 330), (900, 480), 'AI 接口（协议待定）',
         pts=[(830, 330), (830, 480)], lx=838, ly=385, w=170, align='left')
    edge(d, 'd4', 'app', 'db', (580, 370), (580, 430), '读写', lx=590, ly=389, w=60, align='left')
    d.cell('note', '候选部署示意：不确认端口、云厂商、数据库或容器。'
                   '<NL>AI 服务与异构设备都在系统边界外，只参与 UC2/UC9/EXT2。',
           NOTE, 40, 700, 640, 90)
    return d.save()


# ================================== candidate design (not in report; see docs/development-plan.md)
PKG = ('shape=folder;tabWidth=110;tabHeight=22;tabPosition=left;whiteSpace=wrap;html=1;spacingTop=22;'
       'fillColor=#F5F9FF;strokeColor=#3A6EA5;fontColor=#1B3A5C;' + FONT)
PKG_OUTER = ('shape=folder;tabWidth=110;tabHeight=22;tabPosition=left;html=1;verticalAlign=top;align=left;'
             'spacingLeft=12;spacingTop=24;fontStyle=1;fillColor=#FFFFFF;strokeColor=#3A6EA5;'
             'fontColor=#1B3A5C;' + FONT)
REALIZE = ('endArrow=block;endFill=0;endSize=14;dashed=1;html=1;rounded=0;strokeColor=#1B3A5C;'
           'strokeWidth=1.5;' + FONT)
ER_REL = 'html=1;rounded=0;endFill=0;startFill=0;endSize=14;startSize=14;strokeColor=#1B3A5C;strokeWidth=1.5;'
ER_END = {'1': 'ERmandOne', '0..1': 'ERzeroToOne', '0..*': 'ERzeroToMany'}


def note_label(d, cid, text, x, y, w=160, h=22):
    txtcell(d, cid, text, x, y, w, h, align='left')


def dclass(d, cid, name, attrs, ops, x, y, w, head=28, dashed=False):
    """Class or entity box: attribute and operation compartments are optional, height follows lines."""
    style = BOX.replace('startSize=28', 'startSize=%d' % head) + ('dashed=1;' if dashed else '')
    ah = 20 * (attrs.count('<NL>') + 1) + 14 if attrs else 0
    oh = 20 * (ops.count('<NL>') + 1) + 14 if ops else 0
    d.cell(cid, name, style, x, y, w, head + ah + oh)
    if attrs:
        d.cell(cid + '_a', attrs, ATTR + ('dashed=1;' if dashed else ''), 0, head, w, ah, parent=cid)
    if ops:
        d.cell(cid + '_o', ops, OPS, 0, head + ah, w, oh, parent=cid)
    return y + head + ah + oh


def package():
    d = Dia('package', '候选包图', 1600, 1010)
    W, H = 300, 110
    d.cell('ui', '用户交互<NL>三类人员入口', PKG, 610, 40, W, 90)
    d.cell('db', '数据存储<NL>技术待定（B09）', PKG, 1220, 40, W, 90)
    d.cell('biz', '业务功能', PKG_OUTER, 40, 190, 1520, 440)
    pk = {
        'use': ('设备使用<NL>UC1 申请 · UC2 操作 · UC3 查看状态', 80, 290),
        'con': ('设备接入<NL>UC5 · G1–G3', 460, 290),
        'auth': ('身份与权限<NL>INC3 认证 · INC1 校验 · UC6 分配', 840, 290),
        'log': ('日志审计<NL>INC2 记录 · UC7 审计', 1220, 290),
        'mon': ('监测与运维<NL>UC9 监测 · UC10 运维', 840, 470),
        'tkt': ('故障工单<NL>UC4 · UC8 · UC11 · EXT1', 1220, 470),
    }
    for k, (txt, x, y) in pk.items():
        d.cell(k, txt, PKG, x, y, W, H)
    d.cell('dev', '设备适配<NL>USB / 蓝牙 / Zigbee 适配实现（G1–G3）', PKG, 80, 720, 1060, H)
    d.cell('ai', 'AI 交互适配<NL>EXT2', PKG, 1220, 720, W, H)
    edge(d, 'p1', 'ui', 'biz', (760, 130), (760, 190), '«use»', dashed=True, lx=770, ly=148, w=60,
         align='left')
    edge(d, 'p2', 'biz', 'db', (1370, 190), (1370, 130), '持久化', dashed=True, lx=1380, ly=148, w=80,
         align='left')
    edge(d, 'p3', 'use', 'auth', (200, 290), (920, 290), 'INC3 认证 · INC1 校验', pts=[(200, 262), (920, 262)],
         dashed=True, lx=560, ly=238, w=200)
    edge(d, 'p4', 'use', 'log', (140, 290), (1340, 290), 'INC2 记录日志', pts=[(140, 232), (1340, 232)],
         dashed=True, lx=1100, ly=238, w=140)
    edge(d, 'p5', 'con', 'auth', (760, 345), (840, 345), 'INC3', dashed=True, lx=800, ly=320, w=60)
    edge(d, 'p6', 'mon', 'tkt', (1140, 525), (1220, 525), 'EXT1', dashed=True, lx=1180, ly=500, w=60)
    edge(d, 'p7', 'use', 'dev', (230, 400), (230, 720), '下发指令', dashed=True, lx=238, ly=650, w=100,
         align='left')
    edge(d, 'p8', 'con', 'dev', (610, 400), (610, 720), '接入', dashed=True, lx=618, ly=650, w=60,
         align='left')
    edge(d, 'p9', 'mon', 'dev', (990, 580), (990, 720), '读取状态 · 运维动作', dashed=True, lx=998, ly=650,
         w=160, align='left')
    edge(d, 'p10', 'tkt', 'ai', (1370, 580), (1370, 720), '[请求AI辅助]', dashed=True, lx=1378, ly=650,
         w=140, align='left')
    d.cell('note', '候选包划分，用于组织后续代码，不代表已实现模块；虚线箭头为包依赖。'
                   '<NL>与图2-18对应：设备使用、设备接入 → 设备使用与接入；身份与权限、日志审计 → 权限与日志；'
                   '<NL>监测与运维、故障工单 → 状态监测、运维与工单。其他入口的访问控制见 B10，不画成 include。'
                   '<NL>EXT1 只依赖故障工单，不指向 UC10；AI 交互适配只返回建议，不依赖设备适配。',
           NOTE, 40, 870, 1100, 110)
    return d.save()


def design_adapters():
    d = Dia('design-adapters', '设备与AI适配接口设计类图', 1700, 1160)
    callers = [('c1', '设备使用服务<NL>UC2 · UC3', 40), ('c2', '设备接入服务<NL>UC5 · G1–G3', 320),
               ('c3', '监测与运维服务<NL>UC9 · UC10', 600), ('c4', '工单处理服务<NL>UC11 · EXT2', 1270)]
    for cid, txt, x in callers:
        d.cell(cid, '«control»<NL>' + txt, COMP, x, 40, 240, 90)
    dclass(d, 'reg', '设备适配注册表', '适配器映射：接入类型 → 适配器',
           '取得适配器(接入类型) : 设备适配接口', 280, 220, 360)
    dclass(d, 'dif', '«interface»<NL>设备适配接口', '',
           '接入(接入参数) : 接入结果<NL>下发指令(设备标识, 指令) : 执行结果<NL>读取状态(设备标识) : 状态采样'
           '<NL>执行运维动作(设备标识, 动作) : 执行结果（B05）', 280, 400, 420, head=48)
    dclass(d, 'res', '«datatype»<NL>执行结果', '结果：成功 / 失败 / 未知<NL>设备返回信息', '', 800, 360, 260,
           head=48)
    dclass(d, 'smp', '«datatype»<NL>状态采样', '是否取得<NL>原始读数（随设备，B08）<NL>采样时间', '',
           800, 500, 260, head=48)
    for cid, name, attr, x in (('usb', 'USB适配器（G1）', '串口或 HID 参数（B08）', 40),
                               ('ble', '蓝牙适配器（G2）', '蓝牙地址与服务标识（B08）', 360),
                               ('zig', 'Zigbee适配器（G3）', '协调器或网关连接（B08）', 680)):
        dclass(d, cid, name, attr, '', x, 680, 260)
    edge(d, 'u1', 'c1', 'reg', (160, 130), (280, 250), '«use»', pts=[(160, 250)], dashed=True,
         lx=168, ly=180, w=60, align='left')
    edge(d, 'u2', 'c2', 'reg', (440, 130), (440, 220), '«use»', dashed=True, lx=448, ly=164, w=60,
         align='left')
    edge(d, 'u3', 'c3', 'reg', (720, 130), (640, 250), '«use»', pts=[(720, 250)], dashed=True,
         lx=728, ly=180, w=60, align='left')
    edge(d, 'a1', 'reg', 'dif', (460, 316), (460, 400), '按接入类型选取', lx=470, ly=346, w=140,
         align='left')
    txtcell(d, 'a1m0', '1', 438, 318, 20)
    txtcell(d, 'a1m1', '1..*', 420, 376, 36)
    edge(d, 'r1', 'dif', 'res', (700, 430), (800, 430), '«use»', dashed=True, lx=750, ly=406, w=60)
    edge(d, 'r2', 'dif', 'smp', (700, 520), (800, 520), '«use»', dashed=True, lx=750, ly=496, w=60)
    d.link('g1', REALIZE, 'usb', 'dif', (170, 680), (380, 542), [(170, 610), (380, 610)])
    d.link('g2', REALIZE, 'ble', 'dif', (490, 680), (490, 542))
    d.link('g3', REALIZE, 'zig', 'dif', (740, 680), (600, 542), [(740, 610), (600, 610)])

    dclass(d, 'aif', '«interface»<NL>AI诊断接口', '',
           '请求诊断(诊断上下文) : 诊断建议<NL>超时或失败时返回“辅助不可用”', 1180, 400, 420, head=48)
    dclass(d, 'ctx', '«datatype»<NL>诊断上下文', '工单描述<NL>设备类型与近期状态<NL>字段与脱敏（B07）', '',
           1120, 620, 240, head=48)
    dclass(d, 'adv', '«datatype»<NL>诊断建议', '建议内容<NL>是否留存（B07）', '', 1400, 620, 240, head=48)
    dclass(d, 'cli', 'AI Agent服务客户端', '提供方与协议（B07）', '', 1260, 900, 260)
    edge(d, 'u4', 'c4', 'aif', (1390, 130), (1390, 400), '«use» [运维人员请求AI辅助]', dashed=True,
         lx=1398, ly=250, w=220, align='left')
    edge(d, 'r3', 'aif', 'ctx', (1240, 502), (1240, 620), '«use»', dashed=True, lx=1248, ly=556, w=60,
         align='left')
    edge(d, 'r4', 'aif', 'adv', (1520, 502), (1520, 620), '«use»', dashed=True, lx=1528, ly=556, w=60,
         align='left')
    d.link('g4', REALIZE, 'cli', 'aif', (1380, 900), (1380, 502))
    d.cell('note', '接口设计草图：签名为候选，参数与返回的具体字段随 B05、B07、B08 确定。'
                   '<NL>三个适配器是 G1–G3 的实现形式，接入时按所选类型取其一，不顺序执行三种接入。'
                   '<NL>执行结果区分成功、失败、未知，对应图2-13“设备返回可确定结果？”分支。'
                   '<NL>AI 诊断接口只返回建议，不持有设备适配接口：AI 不操作设备，建议不触发 UC10。',
           NOTE, 40, 880, 1060, 120)
    return d.save()


def er_rel(d, eid, a, b, p0, p1, ca, cb, label='', lx=0, ly=0, w=120, dashed=False, pts=()):
    style = ER_REL + 'startArrow=%s;endArrow=%s;' % (ER_END[ca], ER_END[cb]) + ('dashed=1;' if dashed else '')
    d.link(eid, style, a, b, p0, p1, pts)
    if label:
        txtcell(d, eid + 'l', label, lx, ly, w)


def er_concept():
    d = Dia('er-concept', '概念ER草图', 1640, 1400)
    dclass(d, 'u', '用户', 'PK 用户标识<NL>姓名<NL>角色集合（B10）', '', 40, 420, 260)
    dclass(d, 'dv', '设备', 'PK 设备标识<NL>接入类型：USB/蓝牙/Zigbee<NL>状态摘要<NL>型号与连接参数（B08）', '',
           1340, 420, 260)
    dclass(d, 'pm', '设备权限关联', 'PK 授权标识<NL>授权范围（B02）<NL>有效期（B02，可选）', '', 640, 40, 320)
    dclass(d, 'rq', '设备使用申请', 'PK 申请标识<NL>提交时间<NL>使用说明<NL>处理状态（B01）', '', 640, 300, 320)
    dclass(d, 'lg', '操作日志', 'PK 日志标识<NL>时间<NL>操作内容<NL>结果：成功/失败/未知<NL>其他字段（B06）', '',
           640, 580, 320)
    dclass(d, 'tk', '故障工单', 'PK 工单标识<NL>来源：人工报修/监测建单<NL>故障描述<NL>处理信息<NL>状态（B03）', '',
           640, 860, 320)
    dclass(d, 'tr', '工单处理记录（候选）', 'PK 记录标识<NL>处理内容 · 时间<NL>处理人（B03）', '', 360, 1120, 280,
           dashed=True)
    dclass(d, 'ad', 'AI诊断建议（候选）', 'PK 建议标识<NL>建议内容 · 时间<NL>请求人（B07）', '', 960, 1120, 280,
           dashed=True)
    dclass(d, 'op', '运维执行记录（候选）', 'PK 记录标识<NL>动作 · 时间 · 结果<NL>执行人（B05）', '', 1340, 800, 260,
           dashed=True)
    er_rel(d, 'r1', 'u', 'pm', (300, 440), (640, 100), '1', '0..*', '被授权', 420, 250, 60)
    er_rel(d, 'r2', 'u', 'rq', (300, 460), (640, 360), '1', '0..*', '提交', 470, 388, 40)
    er_rel(d, 'r3', 'u', 'lg', (300, 480), (640, 650), '1', '0..*', '执行', 470, 548, 40)
    er_rel(d, 'r4', 'u', 'tk', (300, 500), (640, 930), '0..1', '0..*', '报修', 420, 700, 40)
    er_rel(d, 'r5', 'dv', 'pm', (1340, 440), (960, 100), '1', '0..*', '授权对象', 1110, 250, 80)
    er_rel(d, 'r6', 'dv', 'rq', (1340, 460), (960, 360), '1', '0..*', '目标', 1130, 388, 40)
    er_rel(d, 'r7', 'dv', 'lg', (1340, 480), (960, 650), '1', '0..*', '被操作', 1140, 548, 60)
    er_rel(d, 'r8', 'dv', 'tk', (1340, 500), (960, 930), '1', '0..*', '关联', 1150, 700, 40)
    er_rel(d, 'r9', 'rq', 'pm', (800, 300), (800, 142), '0..1', '0..1', '据此授权（B01）', 810, 220, 140,
           dashed=True)
    er_rel(d, 'r10', 'tk', 'tr', (720, 1002), (500, 1120), '1', '0..*', '', dashed=True,
           pts=[(720, 1070), (500, 1070)])
    er_rel(d, 'r11', 'tk', 'ad', (880, 1002), (1100, 1120), '1', '0..*', '', dashed=True,
           pts=[(880, 1070), (1100, 1070)])
    er_rel(d, 'r12', 'dv', 'op', (1470, 542), (1470, 800), '1', '0..*', '', dashed=True)
    d.cell('note', '实线实体对应图2-2的六个分析类；虚线实体与虚线联系为候选，取决于括号中的待确认事项。'
                   '<NL>乌鸦脚记法：短竖线为 1，圆圈为 0，三叉为多。'
                   '<NL>只表达概念与联系，不代表已确定的表结构、字段类型或外键；数据库选型见 B09。',
           NOTE, 40, 1280, 1000, 96)
    return d.save()


print(device_state())
print(ticket_state())
print(component())
print(deploy())
print(package())
print(design_adapters())
print(er_concept())
