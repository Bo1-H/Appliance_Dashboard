# =============================================================================
#  에너지 라벨 분석 대시보드  v5.0  (멀티 제품군)
#  실행: pip install dash plotly pandas numpy requests  →  python energy_dashboard.py
#  접속: http://127.0.0.1:8050
# =============================================================================

import datetime, json, io
from collections import OrderedDict
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import (
    ALL, Dash, Input, Output, State,
    callback_context, dcc, html,
)
from dash.exceptions import PreventUpdate

# ─────────────────────────────────────────────────────────────────────────────
#  0. 연도 상수
# ─────────────────────────────────────────────────────────────────────────────
CURRENT_YEAR = datetime.datetime.now().year
YEAR_MIN     = CURRENT_YEAR - 10
YEAR_MAX     = CURRENT_YEAR

# ─────────────────────────────────────────────────────────────────────────────
#  1. 제품 설정 (Config-driven)
# ─────────────────────────────────────────────────────────────────────────────
PRODUCTS = OrderedDict()

# 1. 식기세척기
PRODUCTS["dishwasher"] = {
    "label": "🍽️ 식기세척기",
    "api_id": "q8py-6w3f",
    "keyword_map": {
        "Brand Name": (["brand"], []),
        "Model Number": (["model", "number"], ["additional"]),
        "Additional Model Info": (["additional", "model"], []),
        "Type": (["type"], ["tub", "drying", "date", "fuel", "product", "installation", "cooking"]),
        "Width (inches)": (["width"], []),
        "Depth (inches)": (["depth"], []),
        "Capacity (Place Settings)": (["capacity"], []),
        "Tub Material": (["tub"], []),
        "Drying Method": (["dry"], []),
        "Annual Energy Use (kWh/yr)": (["annual", "energy", "use"], ["federal", "standard", "better"]),
        "US Federal Standard (kWh/yr)": (["federal", "standard", "kwh"], ["better", "water", "gallon"]),
        "% Better than US Federal Standard (Energy)": (["better", "federal"], ["water", "gallon"]),
        "Water Use (gallons/cycle)": (["water", "use"], ["federal", "standard", "better"]),
        "US Federal Standard (gallons/cycle)": (["federal", "standard"], ["kwh", "better", "energy", "annual"]),
        "% Better than US Federal Standard (Water)": (["better", "federal"], ["kwh", "energy", "annual"]),
        "Date Certified": (["date", "certif"], []),
        "Date Available On Market": (["date", "available"], []),
    },
    "numeric_order": [
        "Annual Energy Use (kWh/yr)", "Water Use (gallons/cycle)", "Capacity (Place Settings)",
        "% Better than US Federal Standard (Energy)", "% Better than US Federal Standard (Water)",
        "Depth (inches)", "Width (inches)",
    ],
    "default_n": 3,
    "color_cols": ["Brand Name", "Tub Material", "Drying Method"],
    "filters": [
        {"col": "Drying Method", "label": "건조 방식", "icon": "💨"},
        {"col": "Tub Material", "label": "터브 소재", "icon": "🪣"},
        {"col": "Type", "label": "제품 유형", "icon": "📐"},
    ],
    "kpis": [
        {"label": "평균 연간 에너지", "col": "Annual Energy Use (kWh/yr)", "fmt": "{:.1f} kWh", "color": "#1a7c5c"},
        {"label": "평균 물 사용량", "col": "Water Use (gallons/cycle)", "fmt": "{:.2f} gal/cycle", "color": "#7b3f9e"},
        {"label": "에너지 절감률", "col": "% Better than US Federal Standard (Energy)", "fmt": "{:.1f}%", "color": "#c0392b"},
        {"label": "물 절감률", "col": "% Better than US Federal Standard (Water)", "fmt": "{:.1f}%", "color": "#e67e22"},
    ],
    "fill_defaults": {"Model Number": "N/A", "Tub Material": "Unknown", "Drying Method": "Unknown", "Type": "Unknown"},
    "core_dropna": ["Annual Energy Use (kWh/yr)", "Water Use (gallons/cycle)"],
}

# 2. 건조기
PRODUCTS["dryer"] = {
    "label": "👕 건조기",
    "api_id": "t9u7-4d2j",
    "keyword_map": {
        "Brand Name": (["brand"], []),
        "Model Number": (["model", "number"], ["additional", "identifier", "washer"]),
        "Product Type": (["product", "type"], []),
        "Fuel Type": (["fuel"], []),
        "Heat Pump": (["heat", "pump"], ["paired"]),
        "Vented or Ventless": (["vented"], []),
        "Drum Capacity (cu-ft)": (["drum", "capacity"], []),
        "Width (inches)": (["width"], []),
        "Height (inches)": (["height"], []),
        "Depth (inches)": (["depth"], []),
        "Combined Energy Factor (CEF)": (["combined", "energy", "factor"], ["max"]),
        "Estimated Annual Energy Use (kWh/yr)": (["annual", "energy"], ["test", "factor", "combined"]),
        "Calculated CEF - Max Dryness (lbs/kWh)": (["calculated", "max", "dryness"], []),
        "Estimated Energy Test Cycle Time (min)": (["test", "cycle", "time"], []),
        "Voltage (V)": (["voltage"], []),
        "Markets": (["market"], ["date", "available"]),
        "Refrigerant Type": (["refrigerant", "type"], ["gwp"]),
        "Refrigerant GWP": (["gwp"], []),
        "Date Available On Market": (["date", "available"], []),
        "Date Certified": (["date", "certif"], []),
    },
    "numeric_order": [
        "Estimated Annual Energy Use (kWh/yr)", "Combined Energy Factor (CEF)",
        "Drum Capacity (cu-ft)", "Estimated Energy Test Cycle Time (min)",
        "Calculated CEF - Max Dryness (lbs/kWh)", "Voltage (V)",
        "Width (inches)", "Height (inches)", "Depth (inches)",
    ],
    "default_n": 3,
    "color_cols": ["Brand Name", "Fuel Type", "Vented or Ventless"],
    "filters": [
        {"col": "Fuel Type", "label": "연료 유형", "icon": "⚡"},
        {"col": "Vented or Ventless", "label": "배기 방식", "icon": "🌀"},
        {"col": "Product Type", "label": "제품 유형", "icon": "📐"},
        {"col": "Heat Pump", "label": "히트펌프", "icon": "🔥"},
        {"col": "Markets", "label": "마켓", "icon": "🌍"},
        {"col": "Refrigerant Type", "label": "냉매 유형", "icon": "❄️"},
        {"col": "Refrigerant GWP", "label": "냉매 GWP", "icon": "🌡️"},
    ],
    "kpis": [
        {"label": "평균 연간 에너지", "col": "Estimated Annual Energy Use (kWh/yr)", "fmt": "{:.1f} kWh", "color": "#1a7c5c"},
        {"label": "평균 CEF", "col": "Combined Energy Factor (CEF)", "fmt": "{:.2f}", "color": "#7b3f9e"},
        {"label": "평균 드럼 용량", "col": "Drum Capacity (cu-ft)", "fmt": "{:.1f} cu-ft", "color": "#c0392b"},
    ],
    "fill_defaults": {
        "Model Number": "N/A", "Fuel Type": "Unknown", "Vented or Ventless": "Unknown",
        "Product Type": "Unknown", "Heat Pump": "Unknown", "Markets": "Unknown",
        "Refrigerant Type": "Unknown", "Refrigerant GWP": "Unknown",
    },
    "core_dropna": ["Estimated Annual Energy Use (kWh/yr)"],
}

# 3. 전기 쿠킹
PRODUCTS["cooking"] = {
    "label": "🍳 전기 쿠킹",
    "api_id": "m6gi-ng33",
    "keyword_map": {
        "Brand Name": (["brand"], ["partner"]),
        "Model Number": (["model", "number"], ["additional", "identifier"]),
        "Product Type": (["product", "type"], []),
        "Installation Type": (["installation"], []),
        "Cooking Top Technology": (["cooking", "technology"], ["zone", "time"]),
        "Control Type": (["control", "type"], []),
        "Width (inches)": (["width"], []),
        "Height (inches)": (["height"], []),
        "Depth (inches)": (["depth"], []),
        "Number of Cooking Zones": (["number", "cooking", "zone"], ["size", "wattage"]),
        "Voltage (volts)": (["voltage"], []),
        "Amperage (amps)": (["amperage"], []),
        "Annual Energy Consumption (kWh/yr)": (["annual", "energy"], ["low", "oven", "cooking"]),
        "Low Power Mode - Cooktop (kWh/yr)": (["low", "power", "cooking"], ["oven"]),
        "Low Power Mode - Oven (kWh/yr)": (["low", "power", "oven"], ["cooking"]),
        "Avg Cooking Zone Time (min)": (["average", "cooking", "zone", "time"], []),
        "Markets": (["market"], ["date", "available"]),
        "Date Available On Market": (["date", "available"], []),
        "Date Certified": (["date", "certif"], []),
    },
    "numeric_order": [
        "Annual Energy Consumption (kWh/yr)",
        "Low Power Mode - Cooktop (kWh/yr)", "Low Power Mode - Oven (kWh/yr)",
        "Avg Cooking Zone Time (min)",
        "Amperage (amps)", "Number of Cooking Zones",
        "Width (inches)", "Height (inches)", "Depth (inches)",
    ],
    "default_n": 3,
    "color_cols": ["Brand Name", "Product Type", "Cooking Top Technology",
                   "Installation Type", "Control Type"],
    "filters": [
        {"col": "Product Type", "label": "제품 유형", "icon": "🍳"},
        {"col": "Installation Type", "label": "설치 유형", "icon": "🔧"},
        {"col": "Cooking Top Technology", "label": "조리 기술", "icon": "🔥"},
        {"col": "Control Type", "label": "제어 방식", "icon": "🎛️"},
        {"col": "Markets", "label": "마켓", "icon": "🌍"},
    ],
    "kpis": [
        {"label": "평균 연간 에너지", "col": "Annual Energy Consumption (kWh/yr)", "fmt": "{:.1f} kWh", "color": "#1a7c5c"},
        {"label": "평균 전류", "col": "Amperage (amps)", "fmt": "{:.1f}A", "color": "#7b3f9e"},
        {"label": "평균 조리 구역", "col": "Number of Cooking Zones", "fmt": "{:.1f}개", "color": "#c0392b"},
        {"label": "평균 조리 시간", "col": "Avg Cooking Zone Time (min)", "fmt": "{:.1f}분", "color": "#e67e22"},
    ],
    "fill_defaults": {
        "Model Number": "N/A", "Product Type": "Unknown",
        "Installation Type": "Unknown", "Cooking Top Technology": "Unknown",
        "Control Type": "Unknown", "Markets": "Unknown",
    },
    "core_dropna": ["Annual Energy Consumption (kWh/yr)"],
}

# ─────────────────────────────────────────────────────────────────────────────
#  2. 헬퍼 함수
# ─────────────────────────────────────────────────────────────────────────────

def _norm_col(c: str) -> str:
    return (c.strip().lower()
             .replace("_", " ").replace("(", " ").replace(")", " ")
             .replace("/", " ").replace("%", " ").replace("-", " "))


def _find_col(columns: list[str], include: list[str], exclude: list[str]) -> str | None:
    best, best_score = None, -1
    for col in columns:
        norm   = _norm_col(col)
        tokens = set(norm.split())
        if any(kw in tokens for kw in exclude):
            continue
        score = sum(1 for kw in include if kw in tokens or any(kw in t for t in tokens))
        if score == len(include) and score > best_score:
            best, best_score = col, score
    return best


def _fetch_api_data(api_id: str) -> tuple[pd.DataFrame | None, str]:
    """API ID에 따라 데이터 페치 (JSON 시도 후 CSV 폴백)"""
    api_url = f"https://data.energystar.gov/resource/{api_id}.json?$limit=50000"
    csv_url = f"https://data.energystar.gov/api/views/{api_id}/rows.csv?accessType=DOWNLOAD"

    try:
        import requests
        print(f"  ⏳  API(JSON) {api_id} 요청 중...")
        resp = requests.get(api_url, timeout=30)
        resp.raise_for_status()
        records = resp.json()
        if records:
            print(f"  ✅  JSON 응답 {len(records)}건")
            return pd.DataFrame(records), ""
        return None, "API가 빈 결과를 반환했습니다."
    except Exception as e:
        print(f"  ⚠️  API(JSON) 실패: {e}")
        err_json = str(e)

    try:
        import requests
        print(f"  ⏳  CSV {api_id} 다운로드 중...")
        resp = requests.get(csv_url, timeout=60)
        resp.raise_for_status()
        raw = pd.read_csv(io.StringIO(resp.text))
        print(f"  ✅  CSV {len(raw)}건")
        return raw, ""
    except Exception as e:
        print(f"  ⚠️  CSV 실패: {e}")
        err_csv = str(e)

    return None, f"JSON: {err_json}\nCSV: {err_csv}"


def _clean_product_data(raw: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, list[str]]:
    """설정 기반 데이터 정제"""
    cols_orig = raw.columns.tolist()
    missing   = []
    df        = pd.DataFrame()

    for our_col, (inc, exc) in config["keyword_map"].items():
        found = _find_col(cols_orig, inc, exc)
        if found is not None:
            df[our_col] = raw[found].copy()
        else:
            missing.append(our_col)

    if "Brand Name" not in df.columns or df["Brand Name"].isna().all():
        return pd.DataFrame(), missing

    # 숫자형 변환
    num_cols = config["numeric_order"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace("%", "").str.strip(), errors="coerce"
            )

    # 출시연도: "Date Available On Market" 우선, 없으면 "Date Certified" 폴백
    for date_col in ["Date Available On Market", "Date Certified"]:
        if date_col in df.columns:
            dt    = pd.to_datetime(df[date_col], errors="coerce")
            valid = dt.notna().sum()
            if valid > len(df) * 0.3:
                df["Release Year"] = dt.dt.year
                print(f"  📅  Release Year → {date_col} ({valid}건 파싱)")
                break
    if "Release Year" not in df.columns:
        df["Release Year"] = CURRENT_YEAR

    # 기본값 채우기 (컬럼 없으면 생성, 있으면 NaN을 기본값으로 채움)
    for c, default in config["fill_defaults"].items():
        if c not in df.columns:
            df[c] = default
        else:
            df[c] = df[c].fillna(default)

    # Core 컬럼 기준 dropna
    core = [c for c in config["core_dropna"] if c in df.columns]
    if core:
        df = df.dropna(subset=core, how="all")

    # ── 단위 정규화: mm 단위로 보이는 치수(>100) → inches 변환 ──
    for dim_col in [c for c in df.columns if "(inches)" in c]:
        if dim_col in df.columns:
            vals = pd.to_numeric(df[dim_col], errors="coerce")
            mm_mask = vals > 100
            if mm_mask.any():
                df.loc[mm_mask, dim_col] = vals[mm_mask] / 25.4
                print(f"  🔄  {dim_col}: {mm_mask.sum()}건 mm→inches 변환")

    df["Release Year"] = df["Release Year"].fillna(CURRENT_YEAR).astype(int)
    if missing:
        print(f"  ⚠️  매핑 실패 컬럼: {missing}")
    return df.reset_index(drop=True), missing

# ─────────────────────────────────────────────────────────────────────────────
#  3. 데이터 로딩 (모든 제품 시도)
# ─────────────────────────────────────────────────────────────────────────────
LOADED = {}  # pkey -> {"df": df, "df_raw": raw_df, "brands": [...], ...}

for pkey, pcfg in PRODUCTS.items():
    print(f"\n📦  {pcfg['label']} 로딩 중...")
    raw, api_error = _fetch_api_data(pcfg["api_id"])

    if raw is not None:
        df_raw = raw.copy()
        df, missing = _clean_product_data(raw, pcfg)

        if len(df) >= 10:
            brands = sorted(df["Brand Name"].dropna().unique().tolist())
            top5   = df["Brand Name"].value_counts().nlargest(5).index.tolist()

            numeric_cols = [c for c in pcfg["numeric_order"] if c in df.columns]
            default_numeric = numeric_cols[:pcfg["default_n"]]

            color_cols = [c for c in pcfg["color_cols"] if c in df.columns]

            # 색상 맵 생성
            _PAL_SRC = {
                "Brand Name": (px.colors.qualitative.Bold
                              + px.colors.qualitative.Vivid
                              + px.colors.qualitative.Safe),
                "Tub Material": px.colors.qualitative.Set2,
                "Drying Method": px.colors.qualitative.Pastel,
                "Fuel Type": px.colors.qualitative.Set3,
                "Vented or Ventless": px.colors.qualitative.Pastel,
                "Product Type": px.colors.qualitative.Light24,
                "Cooking Top Technology": px.colors.qualitative.Safe,
                "Installation Type": px.colors.qualitative.Pastel,
                "Control Type": px.colors.qualitative.Set1,
                "Markets": px.colors.qualitative.Dark2,
                "Heat Pump": px.colors.qualitative.Pastel,
                "Type": px.colors.qualitative.Set2,
            }
            color_maps = {}
            for col in color_cols:
                pal  = _PAL_SRC.get(col, px.colors.qualitative.Bold)
                vals = sorted(df[col].dropna().unique().tolist())
                color_maps[col] = {v: pal[i % len(pal)] for i, v in enumerate(vals)}

            # 필터값 목록
            all_filters = {}
            for f in pcfg["filters"]:
                col = f["col"]
                if col in df.columns:
                    all_filters[col] = sorted(df[col].dropna().unique().tolist())

            LOADED[pkey] = {
                "df": df,
                "df_raw": df_raw,
                "brands": brands,
                "top5": top5,
                "numeric_cols": numeric_cols,
                "default_numeric": default_numeric,
                "color_cols": color_cols,
                "color_maps": color_maps,
                "all_filters": all_filters,
            }
            print(f"  ✅  {len(df):,}건 로딩 완료")
        else:
            print(f"  ⚠️  유효한 행이 {len(df)}건뿐이어서 스킵됨")
    else:
        print(f"  ❌  API 오류: {api_error[:100]}")

print(f"\n총 {len(LOADED)}개 제품군 로딩 완료\n")

# ─────────────────────────────────────────────────────────────────────────────
#  4. 공통 스타일
# ─────────────────────────────────────────────────────────────────────────────
CARD  = {"backgroundColor":"white","borderRadius":"12px","padding":"20px 24px",
         "boxShadow":"0 2px 12px rgba(0,0,0,0.08)","marginBottom":"20px"}
LABEL = {"fontWeight":"600","fontSize":"12px","color":"#555","marginBottom":"8px",
         "display":"block","letterSpacing":"0.4px","textTransform":"uppercase"}
BTN_BLUE  = {"backgroundColor":"#2a5298","color":"white","border":"none",
             "borderRadius":"6px","padding":"8px 14px","fontSize":"13px",
             "fontWeight":"700","cursor":"pointer","whiteSpace":"nowrap"}
BTN_GREEN = {**BTN_BLUE, "backgroundColor":"#1a7c5c","padding":"7px 12px","fontSize":"12px"}
CHIP = {"display":"inline-flex","alignItems":"center","gap":"5px",
        "backgroundColor":"#eef3fc","border":"1px solid #c5d8f5",
        "borderRadius":"20px","padding":"4px 10px 4px 12px",
        "fontSize":"12px","fontWeight":"500","color":"#1a3a6b"}

_CHKBOX_INPUT = {"cursor":"pointer","marginRight":"6px","width":"14px","height":"14px",
                 "accentColor":"#2a5298"}
_CHKBOX_LABEL = {"display":"flex","alignItems":"center","marginBottom":"6px",
                 "fontSize":"13px","color":"#333","cursor":"pointer","lineHeight":"1.4"}

# ─────────────────────────────────────────────────────────────────────────────
#  5. 앱 초기화
# ─────────────────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    title="에너지 라벨 분석 대시보드",
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
    ],
)

# ── 모바일 반응형 CSS ──────────────────────────────────────────────
app.index_string = '''<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
<style>
/* ── 모바일 반응형 ── */
@media (max-width: 768px) {
    /* 헤더 */
    .dash-header { flex-direction: column !important; padding: 14px 16px !important; gap: 10px; }
    .dash-header h1 { font-size: 16px !important; }
    .dash-header p  { font-size: 11px !important; }
    .dash-header button { font-size: 11px !important; padding: 6px 10px !important; width: 100%; }

    /* 탭 */
    .tab { padding: 10px 12px !important; font-size: 12px !important; }

    /* 컨텐츠 영역 */
    .tab-content { padding: 12px 10px !important; }

    /* KPI 카드 */
    .kpi-row { flex-direction: column !important; gap: 8px !important; }
    .kpi-row > div { min-width: unset !important; }

    /* 컨트롤 패널 */
    .ctrl-panel { padding: 12px 14px !important; }
    .ctrl-row { flex-direction: column !important; gap: 12px !important; }
    .ctrl-row > div { min-width: unset !important; flex: unset !important; width: 100% !important; }

    /* 필터 영역 */
    .filter-area { flex-direction: column !important; gap: 16px !important; }
    .filter-area > div { min-width: unset !important; flex: unset !important; width: 100% !important;
                         padding-left: 0 !important; border-left: none !important;
                         border-top: 1px dashed #e0e0e0; padding-top: 12px; }
    .filter-area > div:first-child { border-top: none; padding-top: 0; }

    /* 차트 */
    .splom-graph { height: 500px !important; }
    .year-chart  { height: 280px !important; }

    /* 차트 헤더 */
    .chart-header { flex-direction: column !important; gap: 8px !important; align-items: flex-start !important; }
    .chart-header > div { width: 100% !important; }

    /* 범례 */
    .js-plotly-plot .plotly .legend { display: none !important; }

    /* 푸터 */
    .dash-footer { padding: 10px 16px !important; }
}

@media (max-width: 480px) {
    .dash-header h1 { font-size: 14px !important; }
    .splom-graph { height: 400px !important; }
    .year-chart  { height: 240px !important; }
}
</style>
</head>
<body>
{%app_entry%}
<footer>
{%config%}
{%scripts%}
{%renderer%}
</footer>
</body>
</html>'''

# ─────────────────────────────────────────────────────────────────────────────
#  6. 헬퍼
# ─────────────────────────────────────────────────────────────────────────────
def _kpi(label, value, accent):
    return html.Div(style={
        "backgroundColor":"white","borderRadius":"10px","padding":"16px 20px",
        "boxShadow":"0 2px 8px rgba(0,0,0,0.07)","borderLeft":f"4px solid {accent}",
        "flex":"1","minWidth":"155px",
    }, children=[
        html.P(label, style={"margin":0,"fontSize":"11px","color":"#888",
                              "textTransform":"uppercase","letterSpacing":"0.6px"}),
        html.P(value, style={"margin":"6px 0 0","fontSize":"20px",
                              "fontWeight":"700","color":accent}),
    ])


def _filter_col(title, icon, checklist_id, all_vals, col_key, outer_border=True):
    """필터 컬럼 컴포넌트"""
    color_hint = COLOR_MAPS_GLOBAL.get(col_key, {}) if len(LOADED) > 0 else {}

    def _dot(val):
        c = color_hint.get(val, "#ccc")
        return html.Span(style={
            "width":"9px","height":"9px","borderRadius":"50%",
            "backgroundColor":c,"display":"inline-block","marginRight":"6px",
            "flexShrink":"0",
        })

    options = [
        {"label": html.Span(style={"display":"flex","alignItems":"center"}, children=[
            _dot(v), html.Span(v, style={"fontSize":"13px","color":"#333"}),
        ]), "value": v}
        for v in all_vals
    ] if all_vals else []

    outer_style = {"flex":"1","minWidth":"160px"}
    if outer_border:
        outer_style.update({"paddingLeft":"20px","borderLeft":"1px dashed #e0e0e0"})

    return html.Div(style=outer_style, children=[
        html.Div(style={"display":"flex","justifyContent":"space-between",
                        "alignItems":"center","marginBottom":"8px"}, children=[
            html.Label(f"{icon}  {title}", style=LABEL),
            html.Button("전체 선택", id=f"select-all-{checklist_id}", n_clicks=0,
                        style={"background":"none","border":"none","color":"#2a5298",
                               "cursor":"pointer","fontSize":"11px","padding":"0",
                               "fontWeight":"600","textDecoration":"underline"}),
        ]),
        dcc.Checklist(
            id=checklist_id,
            options=options,
            value=all_vals[:],
            inputStyle=_CHKBOX_INPUT,
            labelStyle=_CHKBOX_LABEL,
        ),
    ])


# 전역 색상맵 (모든 제품의 색상정보 통합)
COLOR_MAPS_GLOBAL = {}
for pkey, pdata in LOADED.items():
    for col, cmap in pdata["color_maps"].items():
        if col not in COLOR_MAPS_GLOBAL:
            COLOR_MAPS_GLOBAL[col] = {}
        COLOR_MAPS_GLOBAL[col].update(cmap)

# ─────────────────────────────────────────────────────────────────────────────
#  7. 레이아웃
# ─────────────────────────────────────────────────────────────────────────────
if len(LOADED) == 0:
    # API 연결 실패
    app.layout = html.Div(
        style={"fontFamily":"'Segoe UI','Noto Sans KR',sans-serif",
               "backgroundColor":"#f0f2f5","minHeight":"100vh",
               "display":"flex","alignItems":"center","justifyContent":"center"},
        children=[
            html.Div(style={
                "backgroundColor":"white","borderRadius":"16px","padding":"48px 56px",
                "boxShadow":"0 4px 24px rgba(0,0,0,0.12)",
                "maxWidth":"640px","textAlign":"center",
            }, children=[
                html.Div("⚠️", style={"fontSize":"56px","marginBottom":"16px"}),
                html.H2("Energy Star API 연결 실패",
                        style={"color":"#c0392b","fontWeight":"700",
                               "fontSize":"22px","margin":"0 0 12px"}),
                html.P("모든 제품군의 데이터를 불러오지 못했습니다. 아래를 확인하고 앱을 다시 실행해 주세요.",
                       style={"color":"#555","fontSize":"14px","margin":"0 0 24px","lineHeight":"1.7"}),
                html.Div(style={
                    "backgroundColor":"#eef3fc","borderRadius":"8px",
                    "padding":"16px 20px","textAlign":"left"}, children=[
                    html.P("해결 방법", style={"fontWeight":"700","color":"#1a3a6b",
                                               "fontSize":"12px","margin":"0 0 10px",
                                               "textTransform":"uppercase"}),
                    html.Ul(style={"margin":0,"paddingLeft":"18px",
                                   "fontSize":"13px","color":"#444","lineHeight":"2"}, children=[
                        html.Li("인터넷 연결 상태를 확인해 주세요."),
                        html.Li("requests 라이브러리 설치: pip install requests"),
                        html.Li("VPN 또는 프록시 환경이라면 해제 후 재시도"),
                    ]),
                ]),
            ]),
        ]
    )

else:
    # 정상 대시보드
    year_marks = {y: {"label": str(y), "style": {"fontSize":"11px","color":"#666"}}
                  for y in range(YEAR_MIN, YEAR_MAX + 1)}

    total_products = sum(len(LOADED[pkey]["df"]) for pkey in LOADED)
    total_brands = len(set().union(*[set(LOADED[pkey]["brands"]) for pkey in LOADED]))

    app.layout = html.Div(
        style={"fontFamily":"'Segoe UI','Noto Sans KR',sans-serif",
               "backgroundColor":"#f0f2f5","minHeight":"100vh"},
        children=[

            # ── Store / Download ─────────────────────────────────────────
            *[dcc.Store(id=f"{pkey}-active-brands-store", data=LOADED[pkey]["top5"])
              for pkey in LOADED],
            dcc.Store(id="esc-setup-store", data=False),
            *[dcc.Download(id=f"{pkey}-dl-raw") for pkey in LOADED],
            *[dcc.Download(id=f"{pkey}-dl-splom") for pkey in LOADED],
            *[dcc.Download(id=f"{pkey}-dl-year") for pkey in LOADED],
            dcc.Download(id="dl-header-raw"),

            # ── 헤더 ────────────────────────────────────────────────────
            html.Div(className="dash-header", style={
                "background":"linear-gradient(135deg,#1a3a6b 0%,#2a5298 100%)",
                "padding":"22px 40px","color":"white",
                "boxShadow":"0 3px 10px rgba(0,0,0,0.25)",
                "display":"flex","justifyContent":"space-between","alignItems":"center",
            }, children=[
                html.Div([
                    html.H1("🔋  에너지 라벨 분석 대시보드",
                            style={"margin":0,"fontSize":"22px","fontWeight":"700"}),
                    html.P(f"ENERGY STAR® API  ·  총 {total_products:,}개 제품  ·  {len(LOADED)}개 제품군",
                           style={"margin":"6px 0 0","opacity":0.8,"fontSize":"13px"}),
                ]),
                html.Button(
                    "⬇  Energy Star Raw 데이터 전체 (CSV)",
                    id="header-export-raw-btn", n_clicks=0,
                    style={**BTN_BLUE,
                           "backgroundColor":"rgba(255,255,255,0.2)",
                           "border":"1px solid rgba(255,255,255,0.5)"},
                    title="현재 활성 탭 제품군의 원본 데이터 전체 (필터 무관)",
                ),
            ]),

            # ── 탭 ──────────────────────────────────────────────────────
            dcc.Tabs(
                id="main-tabs",
                value=list(LOADED.keys())[0] if LOADED else "dishwasher",
                style={"marginBottom": 0},
                children=[
                    dcc.Tab(
                        label=PRODUCTS[pkey]["label"],
                        value=pkey,
                        style={
                            "padding": "16px 36px",
                            "fontSize": "15px",
                            "fontWeight": "600",
                            "color": "#666",
                            "backgroundColor": "#e8ecf1",
                            "borderTop": "3px solid transparent",
                            "letterSpacing": "0.3px",
                        },
                        selected_style={
                            "padding": "16px 36px",
                            "fontSize": "15px",
                            "fontWeight": "700",
                            "color": "#1a3a6b",
                            "backgroundColor": "#ffffff",
                            "borderTop": "3px solid #2a5298",
                        },
                        children=[
                            html.Div(id=f"{pkey}-tab-content", className="tab-content",
                                     style={"padding":"24px 40px"})
                        ]
                    )
                    for pkey in LOADED
                ]
            ),

            # ── 푸터 ──────────────────────────────────────────────────────
            html.Div(className="dash-footer", style={
                "padding":"14px 40px","borderTop":"1px solid #e0e0e0",
                "backgroundColor":"white","textAlign":"center",
            }, children=[
                html.Span(
                    "데이터 출처: ENERGY STAR® API  ·  Built with Plotly Dash",
                    style={"color":"#aaa","fontSize":"12px"},
                ),
            ]),
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
#  8. 콜백 팩토리
# ─────────────────────────────────────────────────────────────────────────────
def _apply_filters(df, pdata, pcfg, y0, y1, color_col, active_brands,
                   filter_values_dict):
    """필터 마스크 생성 — 브랜드 필터는 color_col과 무관하게 항상 적용"""
    mask = (df["Release Year"] >= y0) & (df["Release Year"] <= y1)

    # 브랜드 필터 항상 적용 (색상 기준과 무관)
    if active_brands:
        mask &= df["Brand Name"].isin(active_brands)

    for f in pcfg["filters"]:
        col = f["col"]
        if col in df.columns:
            vals = filter_values_dict.get(col)
            if vals is not None:
                mask &= df[col].isin(vals)

    return mask


def _register_callbacks(app, pkey, pdata, pcfg):
    """제품별 콜백 등록"""
    df = pdata["df"]
    brands = pdata["brands"]
    top5 = pdata["top5"]
    numeric_cols = pdata["numeric_cols"]
    default_numeric = pdata["default_numeric"]
    color_cols = pdata["color_cols"]
    color_maps = pdata["color_maps"]
    all_filters = pdata["all_filters"]

    # ── '전체 선택' 버튼 ─────────────────────────────────────────────
    for f in pcfg["filters"]:
        col = f["col"]
        checklist_id = f"{pkey}-{col.lower().replace(' ', '-')}-filter"
        select_btn_id = f"select-all-{checklist_id}"

        if col in all_filters:
            _vals = all_filters[col]

            @app.callback(
                Output(checklist_id, "value"),
                Input(select_btn_id, "n_clicks"),
                prevent_initial_call=True,
            )
            def reset_filter_(_, _bound=_vals):
                return _bound[:]

    # ── 브랜드 추가 / 제거 / 전체추가 / 리셋 ──────────────────────────
    @app.callback(
        Output(f"{pkey}-active-brands-store", "data"),
        Output(f"{pkey}-brand-add-dropdown",  "value"),
        Input(f"{pkey}-brand-add-btn", "n_clicks"),
        Input(f"{pkey}-brand-add-all-btn", "n_clicks"),
        Input(f"{pkey}-brand-reset-btn", "n_clicks"),
        Input({"type": f"{pkey}-remove-brand", "index": ALL}, "n_clicks"),
        State(f"{pkey}-brand-add-dropdown", "value"),
        State(f"{pkey}-active-brands-store", "data"),
        prevent_initial_call=True,
    )
    def manage_brands(_add, _add_all, _reset, _remove, to_add, current):
        ctx = callback_context
        if not ctx.triggered:
            return current, None
        tid = ctx.triggered[0]["prop_id"]
        # 전체 추가
        if f"{pkey}-brand-add-all-btn" in tid:
            return brands[:], None
        # 리셋 (Top5)
        if f"{pkey}-brand-reset-btn" in tid:
            return top5[:], None
        # 개별 추가
        if f"{pkey}-brand-add-btn" in tid:
            if to_add and to_add not in current:
                return current + [to_add], None
            return current, None
        # 개별 제거
        try:
            id_dict = json.loads(tid.split(".")[0])
            if id_dict.get("type") == f"{pkey}-remove-brand":
                brand   = id_dict["index"]
                updated = [b for b in current if b != brand]
                return (updated if updated else current), None
        except (json.JSONDecodeError, KeyError):
            pass
        return current, None

    # ── 브랜드 칩 렌더링 ─────────────────────────────────────────────
    @app.callback(
        Output(f"{pkey}-brand-chips",        "children"),
        Output(f"{pkey}-brand-add-dropdown", "options"),
        Output(f"{pkey}-brand-count-label",  "children"),
        Input(f"{pkey}-active-brands-store", "data"),
    )
    def update_brand_ui(active):
        chips = []
        for brand in active:
            chips.append(html.Div(style=CHIP, children=[
                html.Span(brand),
                html.Button("✕",
                            id={"type":f"{pkey}-remove-brand","index":brand}, n_clicks=0,
                            style={"background":"none","border":"none","cursor":"pointer",
                                   "fontSize":"11px","color":"#5a7fc0",
                                   "padding":"0 0 0 2px","lineHeight":"1","fontWeight":"700"}),
            ]))
        remaining = [b for b in brands if b not in active]
        label = f"{len(active)}개 선택 / {len(remaining)}개 추가 가능"
        return chips, [{"label": b, "value": b} for b in remaining], label

    # ── 산점도 행렬 ─────────────────────────────────────────────────
    @app.callback(
        Output(f"{pkey}-splom-graph", "figure"),
        Output(f"{pkey}-chart-title", "children"),
        Input(f"{pkey}-numeric-selector",    "value"),
        Input(f"{pkey}-color-selector",      "value"),
        Input(f"{pkey}-year-slider",         "value"),
        Input(f"{pkey}-active-brands-store", "data"),
        Input(f"{pkey}-marker-size-input",   "value"),
        *[Input(f"{pkey}-{f['col'].lower().replace(' ', '-')}-filter", "value")
          for f in pcfg["filters"]],
    )
    def update_splom(sel_nums, color_col, yr, active_brands, marker_size, *filter_vals):
        if yr is None:
            raise PreventUpdate
        y0, y1 = yr

        filter_values_dict = {}
        for i, f in enumerate(pcfg["filters"]):
            col = f["col"]
            filter_values_dict[col] = filter_vals[i]

        mask = _apply_filters(df, pdata, pcfg, y0, y1, color_col, active_brands,
                             filter_values_dict)
        dff  = df[mask].copy()

        try:
            m_size = max(1.0, min(20.0, float(marker_size or 5)))
        except (TypeError, ValueError):
            m_size = 5.0

        def _empty(msg):
            f = go.Figure()
            f.add_annotation(text=msg, xref="paper", yref="paper", x=.5, y=.5,
                             showarrow=False, font=dict(size=18, color="#888"))
            f.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                            margin=dict(l=0, r=0, t=0, b=0))
            return f

        if not sel_nums or len(sel_nums) < 2:
            return _empty("⚠️  변수를 2개 이상 선택해 주세요."), "산점도 행렬"
        if len(dff) == 0:
            return _empty("⚠️  선택 조건에 해당하는 데이터가 없습니다."), "산점도 행렬 (없음)"

        n_v  = len(sel_nums)
        cmap = color_maps.get(color_col, {})
        lbls = {c: c.replace(" (", "<br>(") for c in sel_nums}
        cat_orders = {color_col: sorted(dff[color_col].dropna().unique().tolist())}

        fig = px.scatter_matrix(
            dff,
            dimensions=sel_nums,
            color=color_col,
            hover_name="Model Number",
            hover_data={
                "Brand Name":    True,
                "Release Year":  True,
            },
            opacity=0.6,
            color_discrete_map=cmap,
            category_orders=cat_orders,
            labels=lbls,
        )
        fig.update_traces(
            marker=dict(size=m_size, line=dict(width=0.4, color="rgba(255,255,255,0.7)")),
            showupperhalf=True,
            diagonal_visible=True,
            selected=dict(marker=dict(size=m_size + 2.5, opacity=1.0)),
            unselected=dict(marker=dict(opacity=0.15)),
        )
        ax = dict(showgrid=True, gridcolor="#ececec", gridwidth=1,
                  zeroline=False, showline=True, linecolor="#ddd", mirror=True,
                  tickfont=dict(size=12))
        layout_axes = {}
        for i in range(n_v):
            k = "" if i == 0 else str(i + 1)
            layout_axes[f"xaxis{k}"] = ax
            layout_axes[f"yaxis{k}"] = ax

        fig.update_layout(
            **layout_axes,
            paper_bgcolor="white", plot_bgcolor="#fafbfc",
            font=dict(family="'Segoe UI','Noto Sans KR',sans-serif", size=12),
            legend=dict(
                title=dict(text=f"<b>{color_col}</b>", font=dict(size=13)),
                orientation="v", x=1.01, y=1, xanchor="left",
                bgcolor="rgba(255,255,255,0.94)",
                bordercolor="#ddd", borderwidth=1, font=dict(size=11),
                itemsizing="constant",
            ),
            margin=dict(l=70, r=180, t=40, b=70),
            hoverlabel=dict(bgcolor="white", bordercolor="#2a5298",
                            font=dict(size=12), align="left"),
            dragmode="select", clickmode="event+select",
        )

        title = (f"산점도 행렬  {n_v}×{n_v}  ·  색상: {color_col}  ·  "
                 f"{y0}~{y1}년  ·  {len(dff):,}개 표시")
        return fig, title

    # ── 연도 × 브랜드 막대 차트 ─────────────────────────────────────
    @app.callback(
        Output(f"{pkey}-year-chart",          "figure"),
        Output(f"{pkey}-year-chart-subtitle", "children"),
        Input(f"{pkey}-year-slider",         "value"),
        Input(f"{pkey}-color-selector",      "value"),
        Input(f"{pkey}-active-brands-store", "data"),
        *[Input(f"{pkey}-{f['col'].lower().replace(' ', '-')}-filter", "value")
          for f in pcfg["filters"]],
    )
    def update_year_chart(yr, color_col, active_brands, *filter_vals):
        if yr is None:
            raise PreventUpdate
        y0, y1 = yr

        filter_values_dict = {}
        for i, f in enumerate(pcfg["filters"]):
            col = f["col"]
            filter_values_dict[col] = filter_vals[i]

        mask = _apply_filters(df, pdata, pcfg, y0, y1, color_col, active_brands,
                             filter_values_dict)
        dff  = df[mask].copy()

        if len(dff) == 0:
            fig = go.Figure()
            fig.add_annotation(text="⚠️  데이터 없음", xref="paper", yref="paper",
                               x=.5, y=.5, showarrow=False, font=dict(size=16, color="#888"))
            fig.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                              margin=dict(l=0, r=0, t=0, b=0))
            return fig, ""

        grp  = dff.groupby(["Release Year", color_col]).size().reset_index(name="제품 수")
        cmap = color_maps.get(color_col, {})
        cat_orders = {color_col: sorted(dff[color_col].dropna().unique().tolist())}

        fig = px.bar(
            grp, x="Release Year", y="제품 수", color=color_col,
            barmode="group",
            color_discrete_map=cmap,
            category_orders=cat_orders,
            labels={"Release Year": "출시 연도", "제품 수": "등록 제품 수 (개)"},
        )
        fig.update_layout(
            paper_bgcolor="white", plot_bgcolor="#fafbfc",
            font=dict(family="'Segoe UI','Noto Sans KR',sans-serif", size=11),
            margin=dict(l=60, r=20, t=20, b=50),
            xaxis=dict(
                tickmode="linear", tick0=y0, dtick=1,
                range=[y0 - 0.5, y1 + 0.5],
                showgrid=False, linecolor="#ddd", showline=True,
            ),
            yaxis=dict(showgrid=True, gridcolor="#ececec", zeroline=False,
                       linecolor="#ddd", showline=True),
            legend=dict(orientation="v", x=1.01, y=1, xanchor="left",
                        bgcolor="rgba(255,255,255,0.9)", bordercolor="#ddd",
                        borderwidth=1, font=dict(size=11), itemsizing="constant"),
            bargap=0.15, bargroupgap=0.05,
            hoverlabel=dict(bgcolor="white", bordercolor="#2a5298",
                            font=dict(size=12), align="left"),
        )
        subtitle = f"{y0}~{y1}년  ·  {len(dff):,}개 제품  ·  {color_col} 기준"
        return fig, subtitle

    # ── Export: Raw 전체 ──────────────────────────────────────────────
    @app.callback(
        Output(f"{pkey}-dl-raw", "data"),
        Input(f"{pkey}-export-raw-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def export_raw(_):
        export_df = pdata["df_raw"]
        return dcc.send_data_frame(export_df.to_csv,
                                   f"energystar_{pkey}_all_raw.csv",
                                   index=False, encoding="utf-8-sig")

    # ── Export: SPLOM ──────────────────────────────────────────────────
    @app.callback(
        Output(f"{pkey}-dl-splom", "data"),
        Input(f"{pkey}-export-splom-btn", "n_clicks"),
        State(f"{pkey}-numeric-selector",    "value"),
        State(f"{pkey}-year-slider",         "value"),
        State(f"{pkey}-color-selector",      "value"),
        State(f"{pkey}-active-brands-store", "data"),
        *[State(f"{pkey}-{f['col'].lower().replace(' ', '-')}-filter", "value")
          for f in pcfg["filters"]],
        prevent_initial_call=True,
    )
    def export_splom(n_clicks, sel_nums, yr, color_col, active_brands, *filter_vals):
        if not n_clicks:
            raise PreventUpdate
        if yr is None:
            raise PreventUpdate
        y0, y1 = yr

        filter_values_dict = {}
        for i, f in enumerate(pcfg["filters"]):
            col = f["col"]
            filter_values_dict[col] = filter_vals[i]

        mask = _apply_filters(df, pdata, pcfg, y0, y1, color_col, active_brands,
                             filter_values_dict)
        meta = [c for c in ["Model Number", "Brand Name", "Release Year"] if c in df.columns]
        cols = meta + [c for c in (sel_nums or []) if c not in meta and c in df.columns]
        dff  = df[mask][cols].copy()
        return dcc.send_data_frame(dff.to_csv, f"{pkey}_splom_{y0}_{y1}.csv",
                                   index=False, encoding="utf-8-sig")

    # ── Export: 연도 집계 ──────────────────────────────────────────────
    @app.callback(
        Output(f"{pkey}-dl-year", "data"),
        Input(f"{pkey}-export-year-btn", "n_clicks"),
        State(f"{pkey}-year-slider",         "value"),
        State(f"{pkey}-color-selector",      "value"),
        State(f"{pkey}-active-brands-store", "data"),
        *[State(f"{pkey}-{f['col'].lower().replace(' ', '-')}-filter", "value")
          for f in pcfg["filters"]],
        prevent_initial_call=True,
    )
    def export_year(n_clicks, yr, color_col, active_brands, *filter_vals):
        if not n_clicks:
            raise PreventUpdate
        if yr is None:
            raise PreventUpdate
        y0, y1 = yr

        filter_values_dict = {}
        for i, f in enumerate(pcfg["filters"]):
            col = f["col"]
            filter_values_dict[col] = filter_vals[i]

        mask = _apply_filters(df, pdata, pcfg, y0, y1, color_col, active_brands,
                             filter_values_dict)
        grp  = df[mask].groupby(["Release Year", color_col]).size().reset_index(name="제품 수")
        return dcc.send_data_frame(grp.to_csv, f"{pkey}_year_brand_{y0}_{y1}.csv",
                                   index=False, encoding="utf-8-sig")

    # ── 탭 콘텐츠 렌더링 ──────────────────────────────────────────────
    @app.callback(
        Output(f"{pkey}-tab-content", "children"),
        Input("main-tabs", "value"),
    )
    def render_tab_content(selected_tab):
        if selected_tab != pkey:
            return None

        # KPI 값 계산
        kpi_items = [_kpi("총 제품 수", f"{len(df):,}개", "#2a5298")]
        for kpi_cfg in pcfg["kpis"]:
            col = kpi_cfg["col"]
            if col in df.columns:
                mean_val = df[col].mean()
                fmt = kpi_cfg["fmt"]
                value = fmt.format(mean_val)
                kpi_items.append(_kpi(kpi_cfg["label"], value, kpi_cfg["color"]))

        # 필터 레이아웃 구성: 필터를 col2/col3에 균등 분배
        _valid_filters = [f for f in pcfg["filters"] if f["col"] in all_filters]
        split_idx = 1 if len(_valid_filters) <= 3 else max(1, len(_valid_filters) // 2)

        filter_col2_children = []
        for f in _valid_filters[:split_idx]:
            col = f["col"]
            if filter_col2_children:
                filter_col2_children.append(
                    html.Hr(style={"border":"none","borderTop":"1px dashed #e8e8e8","margin":"0"})
                )
            filter_col2_children.append(_filter_col(
                f["label"], f["icon"],
                f"{pkey}-{col.lower().replace(' ', '-')}-filter",
                all_filters[col], col, outer_border=False,
            ))

        filter_col3_children = []
        for f in _valid_filters[split_idx:]:
            col = f["col"]
            if filter_col3_children:
                filter_col3_children.append(
                    html.Hr(style={"border":"none","borderTop":"1px dashed #e8e8e8","margin":"0"})
                )
            filter_col3_children.append(_filter_col(
                f["label"], f["icon"],
                f"{pkey}-{col.lower().replace(' ', '-')}-filter",
                all_filters[col], col, outer_border=False,
            ))

        return html.Div([
            # KPI
            html.Div(className="kpi-row", style={"display":"flex","gap":"14px",
                            "marginBottom":"20px","flexWrap":"wrap"}, children=kpi_items),

            # 컨트롤 패널
            html.Div(className="ctrl-panel", style=CARD, children=[
                html.Div(className="ctrl-row", style={"display":"flex","gap":"24px","flexWrap":"wrap",
                                "alignItems":"flex-end","marginBottom":"20px"}, children=[
                    html.Div(style={"flex":"3","minWidth":"340px"}, children=[
                        html.Label("📊  분석 변수 선택 (2개 이상)", style=LABEL),
                        dcc.Dropdown(
                            id=f"{pkey}-numeric-selector",
                            options=[{"label":c,"value":c} for c in numeric_cols],
                            value=default_numeric,
                            multi=True,
                            placeholder="변수를 2개 이상 선택하세요...",
                            style={"fontSize":"13px"},
                        ),
                    ]),
                    html.Div(style={"flex":"1","minWidth":"200px"}, children=[
                        html.Label("🎨  색상 기준 (범주형)", style=LABEL),
                        dcc.Dropdown(
                            id=f"{pkey}-color-selector",
                            options=[{"label":c,"value":c} for c in color_cols],
                            value=color_cols[0] if color_cols else "Brand Name",
                            clearable=False,
                            style={"fontSize":"13px"},
                        ),
                    ]),
                ]),

                html.Div(style={"marginBottom":"20px"}, children=[
                    html.Label("📅  출시 연도 범위 필터", style=LABEL),
                    html.Div(style={"padding":"0 8px"}, children=[
                        dcc.RangeSlider(
                            id=f"{pkey}-year-slider",
                            min=YEAR_MIN, max=YEAR_MAX, step=1,
                            value=[YEAR_MIN, YEAR_MAX],
                            marks=year_marks,
                            tooltip={"placement":"bottom","always_visible":True},
                            allowCross=False,
                        ),
                    ]),
                ]),

                html.Hr(style={"border":"none","borderTop":"1px dashed #e0e0e0",
                               "margin":"4px 0 20px"}),

                html.Div(className="filter-area", style={"display":"flex","gap":"0","flexWrap":"wrap"}, children=[
                    # 브랜드
                    html.Div(style={"flex":"1.2","minWidth":"220px",
                                    "paddingRight":"20px"}, children=[
                        html.Div(style={"display":"flex","justifyContent":"space-between",
                                        "alignItems":"center","marginBottom":"8px"}, children=[
                            html.Label("🏷️  브랜드 필터", style=LABEL),
                            html.Div(style={"display":"flex","gap":"6px","alignItems":"center"}, children=[
                                html.Button("전체 추가",
                                            id=f"{pkey}-brand-add-all-btn", n_clicks=0,
                                            style={"backgroundColor":"#2a5298","color":"white",
                                                   "border":"none","borderRadius":"4px",
                                                   "padding":"3px 10px","fontSize":"11px",
                                                   "fontWeight":"600","cursor":"pointer"}),
                                html.Button("리셋 (Top5)",
                                            id=f"{pkey}-brand-reset-btn", n_clicks=0,
                                            style={"backgroundColor":"#e67e22","color":"white",
                                                   "border":"none","borderRadius":"4px",
                                                   "padding":"3px 10px","fontSize":"11px",
                                                   "fontWeight":"600","cursor":"pointer"}),
                            ]),
                        ]),
                        html.P(id=f"{pkey}-brand-count-label",
                               style={"fontSize":"11px","color":"#888","margin":"0 0 6px"}),
                        html.Div(id=f"{pkey}-brand-chips",
                                 style={"display":"flex","flexWrap":"wrap",
                                        "gap":"6px","marginBottom":"10px","minHeight":"28px"}),
                        html.Div(style={"display":"flex","gap":"6px","alignItems":"center"}, children=[
                            dcc.Dropdown(
                                id=f"{pkey}-brand-add-dropdown",
                                placeholder="브랜드 추가...",
                                clearable=True,
                                style={"flex":"1","fontSize":"12px"},
                            ),
                            html.Button("＋", id=f"{pkey}-brand-add-btn", n_clicks=0,
                                        style={**BTN_BLUE,"padding":"7px 12px","fontSize":"14px"}),
                        ]),
                    ]),

                    # 필터 컬럼 2 (앞쪽 절반)
                    html.Div(style={"flex":"1","minWidth":"160px","paddingLeft":"20px",
                                    "borderLeft":"1px dashed #e0e0e0",
                                    "display":"flex","flexDirection":"column","gap":"16px"}
                             if filter_col2_children else {"display":"none"},
                             children=filter_col2_children),

                    # 필터 컬럼 3 (뒤쪽 절반)
                    html.Div(style={"flex":"1","minWidth":"160px","paddingLeft":"20px",
                                    "borderLeft":"1px dashed #e0e0e0",
                                    "display":"flex","flexDirection":"column","gap":"16px"}
                             if filter_col3_children else {"display":"none"},
                             children=filter_col3_children),
                ]),
            ]),

            # SPLOM
            html.Div(style=CARD, children=[
                html.Div(className="chart-header", style={"display":"flex","justifyContent":"space-between",
                                "alignItems":"center","marginBottom":"16px","gap":"12px"}, children=[
                    html.Div(id=f"{pkey}-chart-title",
                             style={"fontSize":"15px","fontWeight":"600","color":"#2a2a2a","flex":"1"}),
                    html.Div(style={"display":"flex","alignItems":"center","gap":"6px"}, children=[
                        html.Label("포인트 크기:",
                                   style={"fontSize":"12px","color":"#666","whiteSpace":"nowrap"}),
                        dcc.Input(
                            id=f"{pkey}-marker-size-input",
                            type="number", value=10, min=1, max=20, step=0.5,
                            style={"width":"60px","fontSize":"13px","padding":"4px 8px",
                                   "border":"1px solid #ccc","borderRadius":"4px",
                                   "textAlign":"center"},
                        ),
                    ]),
                    html.Button("⬇  데이터 추출 (CSV)", id=f"{pkey}-export-splom-btn",
                                n_clicks=0, style=BTN_GREEN),
                ]),
                dcc.Loading(type="circle", color="#2a5298", children=
                    dcc.Graph(
                        id=f"{pkey}-splom-graph",
                        config={
                            "displayModeBar": True,
                            "scrollZoom": True,
                            "modeBarButtonsToRemove": ["lasso2d"],
                            "toImageButtonOptions": {
                                "format":"png","scale":2,
                                "filename":f"{pkey}_splom",
                            },
                        },
                        className="splom-graph",
                        style={"height":"820px"},
                    )
                ),
                html.P("💡  박스 선택 후 ESC 키 또는 그래프 외부 클릭 시 선택이 초기화됩니다.",
                       style={"fontSize":"12px","color":"#aaa","margin":"10px 0 0","textAlign":"right"}),
            ]),

            # 연도별 등록 제품 수
            html.Div(style=CARD, children=[
                html.Div(style={"display":"flex","justifyContent":"space-between",
                                "alignItems":"center","marginBottom":"16px"}, children=[
                    html.Div([
                        html.Span("📅  연도별 등록 제품 수",
                                  style={"fontSize":"15px","fontWeight":"600","color":"#2a2a2a"}),
                        html.Span(id=f"{pkey}-year-chart-subtitle",
                                  style={"fontSize":"13px","color":"#888","marginLeft":"10px"}),
                    ]),
                    html.Button("⬇  데이터 추출 (CSV)", id=f"{pkey}-export-year-btn",
                                n_clicks=0, style=BTN_GREEN),
                ]),
                dcc.Loading(type="circle", color="#2a5298", children=
                    dcc.Graph(
                        id=f"{pkey}-year-chart",
                        config={
                            "displayModeBar": True,
                            "toImageButtonOptions": {
                                "format":"png","scale":2,
                                "filename":f"{pkey}_year_brand",
                            },
                        },
                        className="year-chart",
                        style={"height":"380px"},
                    )
                ),
            ]),

            # 사용 가이드
            html.Div(style={**CARD,"backgroundColor":"#eef3fc","border":"1px solid #c5d8f5"}, children=[
                html.P("💡  사용 가이드",
                       style={"fontWeight":"700","marginBottom":"8px","color":"#1a3a6b"}),
                html.Ul(style={"margin":0,"paddingLeft":"20px",
                               "fontSize":"13px","color":"#444","lineHeight":"2.1"}, children=[
                    html.Li("분석 변수를 2개 이상 선택하면 N×N 산점도 행렬이 자동 생성됩니다."),
                    html.Li("출시 연도 슬라이더를 조정하면 산점도·막대그래프가 동기화됩니다."),
                    html.Li("브랜드 필터: [＋] 버튼으로 추가, 칩의 [✕]로 개별 제거합니다."),
                    html.Li("각 필터: 체크박스로 원하는 값만 선택합니다. '전체 선택'으로 초기화할 수 있습니다."),
                    html.Li("색상 기준을 Brand Name으로 설정하면 브랜드별 색상 레전드가 표시됩니다."),
                    html.Li("포인트 크기: 산점도 헤더의 숫자 입력란에서 조정합니다."),
                    html.Li("박스 선택 후 ESC 키 또는 그래프 외부 클릭으로 선택 초기화."),
                    html.Li("[⬇ 데이터 추출] 버튼으로 각 차트의 필터된 데이터를 CSV로 저장합니다."),
                ]),
            ]),

        ])


# ─────────────────────────────────────────────────────────────────────────────
#  9. 콜백 등록
# ─────────────────────────────────────────────────────────────────────────────
if len(LOADED) > 0:
    for pkey, pdata in LOADED.items():
        pcfg = PRODUCTS[pkey]
        _register_callbacks(app, pkey, pdata, pcfg)

    # ── 헤더 Raw export (활성 탭 제품군 원본) ────────────────────────
    @app.callback(
        Output("dl-header-raw", "data"),
        Input("header-export-raw-btn", "n_clicks"),
        State("main-tabs", "value"),
        prevent_initial_call=True,
    )
    def export_header_raw(n_clicks, active_tab):
        if not n_clicks:
            raise PreventUpdate
        if active_tab not in LOADED:
            raise PreventUpdate
        df_raw = LOADED[active_tab]["df_raw"]
        return dcc.send_data_frame(df_raw.to_csv,
                                   f"energystar_{active_tab}_all_raw.csv",
                                   index=False, encoding="utf-8-sig")

    # ── 글로벌 ESC / 외부 클릭 → SPLOM 선택 초기화 ──────────────────
    _splom_ids_js = ", ".join(f'"{pk}-splom-graph"' for pk in LOADED)
    app.clientside_callback(
        f"""
        function(setupDone) {{
            if (setupDone) {{ return window.dash_clientside.no_update; }}
            var splomIds = [{_splom_ids_js}];

            function resetAll() {{
                splomIds.forEach(function(id) {{
                    var gd = document.getElementById(id);
                    if (!gd) return;
                    var plot = gd.querySelector('.js-plotly-plot') || gd;
                    if (!plot || !plot.data || plot.data.length === 0) return;
                    try {{
                        var sp = new Array(plot.data.length).fill(null);
                        Plotly.restyle(plot, {{ selectedpoints: sp }});
                        plot.querySelectorAll('.select-outline').forEach(function(el){{ el.remove(); }});
                        try {{ Plotly.relayout(plot, {{ selections: [] }}); }} catch(e2) {{}}
                        try {{
                            Plotly.relayout(plot, {{ dragmode: 'pan' }});
                            setTimeout(function(){{ Plotly.relayout(plot, {{ dragmode: 'select' }}); }}, 50);
                        }} catch(e3) {{}}
                    }} catch(e) {{ console.warn('resetSplom:', e); }}
                }});
            }}

            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{ e.preventDefault(); resetAll(); }}
            }});
            document.addEventListener('mousedown', function(e) {{
                var inSplom = splomIds.some(function(id) {{
                    var gd = document.getElementById(id);
                    return gd && gd.contains(e.target);
                }});
                if (!inSplom) resetAll();
            }});
            return true;
        }}
        """,
        Output("esc-setup-store", "data"),
        Input("esc-setup-store", "data"),
        prevent_initial_call=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  10. 진입점
# ─────────────────────────────────────────────────────────────────────────────

# gunicorn이 참조하는 WSGI 서버 객체 (Render 배포 필수)
server = app.server

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DASH_DEBUG", "false").lower() == "true"

    print("=" * 62)
    print("  🔋  에너지 라벨 분석 대시보드 v5.0")
    if len(LOADED) > 0:
        print(f"  로딩된 제품군: {list(LOADED.keys())}")
        for pkey in LOADED:
            print(f"    - {PRODUCTS[pkey]['label']}: {len(LOADED[pkey]['df']):,}건")
    else:
        print("  ⚠️  데이터 로딩 실패 — 오류 화면이 표시됩니다.")
    print(f"  URL          : http://127.0.0.1:{port}")
    print("=" * 62)
    app.run(debug=debug, host="0.0.0.0", port=port)
