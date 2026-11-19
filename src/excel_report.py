"""
엑셀 리포트 만들기

빈 포맷(엑셀 템플릿)에 데이터를 넣고, 월 블록과 Suspect List 를 만들어서 xlsx 로 저장한다.
서식과 수식은 템플릿 안에 이미 들어 있고, 이 파일은 아래만 한다.
    1. 숨김 시트(users, daily_activity, payments, funnel_events, abuser_metrics)에 데이터를 넣는다
    2. 월마다 월 블록(일자 행 + Summary 행)을 만든다. 월이 바뀌면 새 월이 자동으로 추가된다
    3. 의심 계정 목록(Suspect List)을 만든다
"""
import copy
import datetime as dt
import re
import zipfile
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.formatting.formatting import ConditionalFormattingList
from openpyxl.formula.translate import Translator
from openpyxl.utils import get_column_letter as L
from openpyxl.drawing.spreadsheet_drawing import SpreadsheetDrawing
from openpyxl.workbook.properties import CalcProperties
from openpyxl.worksheet._writer import WorksheetWriter
from openpyxl.writer.excel import ExcelWriter

from abuser import GOLD_CV_MAX, ITEM_CV_MAX, FAST_DUNGEON_HRS     # config 시트에 기록할 판정 기준

# ------------------------------------------------------------
# Windows 에서 openpyxl 이 저장 중 만드는 임시 파일(AppData\\Local\\Temp\\openpyxl.xxxx)이
# 백신/OneDrive 등에 잡혀 [WinError 32] 가 나는 경우가 있어서, 임시 파일 없이 메모리에서 저장하도록 바꿔 둔다.
# ------------------------------------------------------------
def _write_worksheet_in_memory(self, ws):
    ws._drawing = SpreadsheetDrawing()
    ws._drawing.charts = ws._charts
    ws._drawing.images = ws._images
    writer = WorksheetWriter(ws, out=BytesIO())
    writer.write()
    ws._rels = writer._rels
    self._archive.writestr(ws.path[1:], writer.read())
    self.manifest.append(ws)


ExcelWriter.write_worksheet = _write_worksheet_in_memory


# ============================================================
# 설정
# ============================================================
TIER_DAYS = 90           # 과금 등급 기준 기간 (템플릿의 config 시트 TierStart 수식과 같은 값)
GRADE_KO = {"normal": "정상", "suspected": "의심", "highly_suspected": "고위험 의심"}
BLOCK_SHEETS = ["Overview", "New Users", "Funnel"]     # 월 블록이 있는 시트


def py(d):
    """pandas 날짜 -> 파이썬 datetime (비어 있으면 None)"""
    return None if pd.isna(d) else d.to_pydatetime()


# ============================================================
# 2. 숨김 시트에 원본 데이터 넣기
#    (수식은 열 전체를 참조하므로 행이 몇 개든 템플릿 수식을 고칠 필요가 없다)
# ============================================================
def fresh_sheet(wb, title):
    """같은 자리에 같은 이름의 빈 숨김 시트를 새로 만든다."""
    idx = wb.sheetnames.index(title)
    wb.remove(wb[title])
    ws = wb.create_sheet(title, idx)
    ws.sheet_state = "hidden"
    return ws


def fill_raw_sheets(wb, users, daily, pay, events, acct):
    signup = users.set_index("user_id")["signup_date"].to_dict()
    last_active = daily.groupby("user_id")["date"].max().to_dict()

    # users: + last_active(값), spend_90d / in_tier_scope(수식: 최근 90일 결제액, 과금 등급 대상 여부)
    ws = fresh_sheet(wb, "users")
    ws.append(["user_id", "signup_date", "country", "platform", "device_id", "last_active", "spend_90d", "in_tier_scope"])
    for i, u in enumerate(users.itertuples(index=False)):
        x = i + 2
        ws.append([u.user_id, py(u.signup_date), u.country, u.platform, u.device_id, py(last_active.get(u.user_id, pd.NaT)),
                   f'=SUMIFS(payments!$C:$C,payments!$A:$A,A{x},payments!$D:$D,">="&config!$B$2)',
                   f"=IF(OR(F{x}>=config!$B$2,G{x}>0),1,0)"])

    # daily_activity: 날짜순 + signup_date(값)
    ws = fresh_sheet(wb, "daily_activity")
    cols = ["user_id", "date", "sessions", "playtime_min", "level", "gold_earned", "items_acquired"]
    ws.append(cols + ["signup_date"])
    d = daily.sort_values(["date", "user_id"]).reset_index(drop=True)
    dates = d["date"].dt.to_pydatetime()
    sdates = [py(signup.get(uid, pd.NaT)) for uid in d["user_id"]]
    for i, row in enumerate(d[cols].itertuples(index=False)):
        r = list(row)
        r[1] = dates[i]
        ws.append(r + [sdates[i]])

    # payments: 시간순 + date, first_in_day(수식), signup_date(값), first_ever(수식)
    ws = fresh_sheet(wb, "payments")
    ws.append(["user_id", "paid_at", "amount_krw", "date", "first_in_day", "signup_date", "first_ever"])
    p = pay.sort_values("paid_at").reset_index(drop=True)
    for i, row in enumerate(p.itertuples(index=False)):
        x = i + 2
        ws.append([row.user_id, py(row.paid_at), row.amount_krw, f"=INT(B{x})",
                   f"=IF(COUNTIFS($A$2:A{x},A{x},$D$2:D{x},D{x})=1,1,0)", py(signup.get(row.user_id, pd.NaT)),
                   f"=IF(COUNTIFS($A$2:A{x},A{x})=1,1,0)"])

    # funnel_events: + signup_date(값)
    ws = fresh_sheet(wb, "funnel_events")
    ws.append(["user_id", "event", "event_time", "signup_date"])
    for row in events.itertuples(index=False):
        ws.append([row.user_id, row.event, py(row.event_time), py(signup.get(row.user_id, pd.NaT))])

    # abuser_metrics: 판정 대상 계정의 지표(값) + 신호 5개 / 신호 수 / 등급(수식)
    ws = fresh_sheet(wb, "abuser_metrics")
    ws.append(["user_id", "active_days", "avg_playtime_min", "gold_per_hour", "items_per_hour", "gold_cv", "item_cv",
               "tut_to_dungeon_hrs", "f_playtime", "f_gold_speed", "f_item_speed", "f_regular", "f_fast_growth",
               "n_signals", "risk"])
    for i, a in enumerate(acct.itertuples(index=False)):
        x = i + 2
        vals = [a.user_id] + [None if (pd.isna(v) or not np.isfinite(v)) else float(v) for v in
                              (a.active_days, a.avg_playtime_min, a.gold_per_hour, a.items_per_hour,
                               a.gold_cv, a.item_cv, a.tut_to_dungeon_hrs)]
        ws.append(vals + [
            f"=IF(C{x}>config!$B$6,1,0)", f"=IF(D{x}>config!$B$7,1,0)", f"=IF(E{x}>config!$B$8,1,0)",
            f"=IF(OR(AND(ISNUMBER(F{x}),F{x}<config!$B$3),AND(ISNUMBER(G{x}),G{x}<config!$B$4)),1,0)",
            f"=IF(AND(ISNUMBER(H{x}),H{x}<config!$B$5),1,0)", f"=SUM(I{x}:M{x})",
            f'=IF(N{x}>=3,"highly_suspected",IF(N{x}=2,"suspected","normal"))'])

    # config: 판정 기준값 (설정 구간의 숫자와 같게 맞춤)
    cfg = wb["config"]
    cfg["B3"], cfg["B4"], cfg["B5"] = GOLD_CV_MAX, ITEM_CV_MAX, FAST_DUNGEON_HRS


# ============================================================
# 3. 월 블록 만들기 (Overview / New Users / Funnel)
#    템플릿에 들어 있는 월 블록 하나(일자 행 + Summary 행)를 견본으로 삼아 월마다 복제한다.
# ============================================================
def find_prototype(ws):
    """견본 월 블록의 첫 일자 행과 Summary 행 번호."""
    first = None
    for r in range(1, ws.max_row + 1):
        v = ws.cell(r, 2).value
        if first is None and isinstance(v, (dt.datetime, dt.date)):
            first = r
        if isinstance(v, str) and v.endswith(" Summary"):
            return first, r
    raise SystemExit(f"'{ws.title}' 시트에서 견본 월 블록(… Summary 행)을 찾지 못했습니다.")


def move(formula, origin, target):
    """수식을 origin 칸에서 target 칸으로 복사한 것처럼 행/열 참조를 옮긴다."""
    return Translator(formula, origin=origin).translate_formula(target)


def rebuild_blocks(ws, months):
    first0, sum0 = find_prototype(ws)
    ncol = ws.max_column

    # 견본 (서식, 값/수식)
    day_proto = {c: (copy.copy(ws.cell(first0, c)._style), ws.cell(first0, c).value) for c in range(2, ncol + 1)}
    sum_proto = {c: (copy.copy(ws.cell(sum0, c)._style), ws.cell(sum0, c).value) for c in range(2, ncol + 1)}
    day_h, sum_h = ws.row_dimensions[first0].height, ws.row_dimensions[sum0].height

    # 조건부 서식: 월 블록 안의 규칙은 견본으로 저장, 그 밖의 규칙(카드 등)은 그대로 유지
    block_rules, other_rules = [], []
    for cf in ws.conditional_formatting:
        ranges = list(cf.sqref.ranges)
        inside = all(first0 <= r.min_row and r.max_row <= sum0 - 1 for r in ranges)
        below = all(r.min_row >= first0 for r in ranges)           # 견본 블록 아래(다른 월 블록)의 규칙은 버림. 새로 만든다
        for rule in cf.rules:
            if inside:
                block_rules.append((rule.priority or 0, ranges, rule))
            elif not below:
                other_rules.append((rule.priority or 0, ranges, rule))
    ws.conditional_formatting = ConditionalFormattingList()
    for _, ranges, rule in sorted(other_rules, key=lambda t: t[0]):
        rule = copy.deepcopy(rule)
        rule.priority = 0
        ws.conditional_formatting.add(" ".join(str(r) for r in ranges), rule)
    block_rules.sort(key=lambda t: t[0])

    # 기존 월 블록 삭제
    ws.delete_rows(first0, ws.max_row - first0 + 1)
    for r in [r for r in ws.row_dimensions if r >= first0]:
        del ws.row_dimensions[r]

    r = first0
    for mi, m0 in enumerate(months):
        is_last = mi == len(months) - 1
        days = pd.date_range(m0, m0 + pd.offsets.MonthEnd(0))
        first = r
        for d in days:
            for c, (style, val) in day_proto.items():
                cell = ws.cell(r, c)
                cell._style = copy.copy(style)
                if c == 2:
                    cell.value = d.to_pydatetime()
                elif isinstance(val, str) and val.startswith("="):
                    cell.value = move(val, f"{L(c)}{first0}", f"{L(c)}{r}")
            rd = ws.row_dimensions[r]
            rd.outlineLevel, rd.hidden = 1, not is_last           # 이전 월은 접어두고 Summary 행의 [+] 로 펼침
            if day_h:
                rd.height = day_h
            r += 1
        last = r - 1

        # Summary 행: 수식을 옮긴 뒤 합계 범위를 이 달의 첫~마지막 일자 행으로 맞춤
        for c, (style, val) in sum_proto.items():
            cell = ws.cell(r, c)
            cell._style = copy.copy(style)
            if c == 2:
                cell.value = f"{m0:%Y-%m} Summary"
            elif isinstance(val, str) and val.startswith("="):
                f = move(val, f"{L(c)}{sum0}", f"{L(c)}{r}")
                cell.value = re.sub(r"(\$?[A-Z]{1,3})\$?\d+:(\$?[A-Z]{1,3})\$?\d+", rf"\g<1>{first}:\g<2>{last}", f)
        rd = ws.row_dimensions[r]
        rd.collapsed = not is_last
        if sum_h:
            rd.height = sum_h

        # 조건부 서식 복제 (회색 처리, 주말 색, 히트맵, 데이터 막대)
        for _, ranges, rule in block_rules:
            new_ranges, top_left_old, top_left_new = [], None, None
            for rg in ranges:
                lo = first + (rg.min_row - first0)
                hi = last if rg.max_row == sum0 - 1 else first + (rg.max_row - first0)
                new_ranges.append(f"{L(rg.min_col)}{lo}:{L(rg.max_col)}{hi}")
                if top_left_old is None:
                    top_left_old, top_left_new = f"{L(rg.min_col)}{rg.min_row}", f"{L(rg.min_col)}{lo}"
            new_rule = copy.deepcopy(rule)
            new_rule.priority = 0
            if new_rule.formula:
                new_rule.formula = [move("=" + f, top_left_old, top_left_new)[1:] for f in new_rule.formula]
            ws.conditional_formatting.add(" ".join(new_ranges), new_rule)
        r += 1


# ============================================================
# 4. Suspect List (의심 계정만 abuser_metrics 시트의 행을 참조하는 수식으로)
# ============================================================
def fill_suspect_list(wb, acct):
    ws = wb["Suspect List"]
    head, first = 4, 5
    last_col = ws.max_column
    proto = {c: copy.copy(ws.cell(first, c)._style) for c in range(2, last_col + 1)}
    height = ws.row_dimensions[first].height
    rules = [(rule.priority or 0, rule) for cf in ws.conditional_formatting for rule in cf.rules]

    ws.delete_rows(first, max(ws.max_row - first + 1, 1))
    for r in [r for r in ws.row_dimensions if r >= first]:
        del ws.row_dimensions[r]

    sus = acct[acct["risk"] != "normal"].sort_values(["n_signals", "user_id"], ascending=[False, True])
    for k, idx in enumerate(sus.index):
        r, m = first + k, idx + 2                                 # acct 의 idx 번째 행 = abuser_metrics 시트의 idx+2 행
        ref = lambda col: f"abuser_metrics!${col}${m}"
        row = [f"={ref('A')}",
               f'=IF({ref("O")}="highly_suspected","고위험 의심",IF({ref("O")}="suspected","의심","정상"))',
               f"={ref('N')}"]
        row += [f'=IF({ref(col)}=1,"●","")' for col in "IJKLM"]
        row += [f'=IF(ISNUMBER({ref(col)}),{ref(col)},"")' for col in "BCDEFGH"]
        for j, v in enumerate(row):
            cell = ws.cell(r, 2 + j)
            cell._style = copy.copy(proto[2 + j])
            cell.value = v
        if height:
            ws.row_dimensions[r].height = height

    n = len(sus)
    ws.conditional_formatting = ConditionalFormattingList()
    if n:
        for _, rule in sorted(rules, key=lambda t: t[0]):
            rule = copy.deepcopy(rule)
            rule.priority = 0
            ws.conditional_formatting.add(f"C{first}:C{first + n - 1}", rule)
        ws.auto_filter.ref = f"B{head}:{L(last_col)}{first + n - 1}"
    return sus


def hide_green_triangles(path):
    """셀 왼쪽 위 초록 삼각형(일치하지 않는 수식 등)을 끈다. openpyxl에 기능이 없어서 저장 후 xml에 직접 넣는다."""
    tag = '<ignoredErrors><ignoredError sqref="A1:ZZ10000" formula="1" formulaRange="1" numberStoredAsText="1"/></ignoredErrors>'
    tmp = Path(path).with_suffix(".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", item.filename):
                xml = data.decode("utf-8")
                m = re.search(r"<(drawing|legacyDrawing|tableParts|extLst)[ />]", xml)
                pos = m.start() if m else xml.rindex("</worksheet>")
                data = (xml[:pos] + tag + xml[pos:]).encode("utf-8")
            zout.writestr(item, data)
    tmp.replace(path)


# ============================================================
# 5. 리포트 만들기 / 저장
# ============================================================
def build_workbook(template, users, daily, pay, events, acct, asof):
    """템플릿을 열어 데이터와 월 블록, Suspect List 를 채운 워크북과 의심 계정 표를 돌려준다."""
    wb = load_workbook(template)
    fill_raw_sheets(wb, users, daily, pay, events, acct)

    months = list(pd.date_range(daily["date"].min().replace(day=1), asof.replace(day=1), freq="MS"))
    for name in BLOCK_SHEETS:
        rebuild_blocks(wb[name], months)
    sus = fill_suspect_list(wb, acct)

    wb.calculation = CalcProperties(fullCalcOnLoad=True)         # 엑셀이 열 때 전부 다시 계산
    return wb, sus


def save_workbook(wb, xlsx):
    wb.save(xlsx)
    hide_green_triangles(xlsx)
