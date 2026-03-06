# frontend/components/charts.py
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

# ألوان الهوية البصرية للهلال الأحمر
BRAND_COLORS = ["#CE2E26", "#42924B", "#3B4A82", "#F1B944", "#3A8478", "#FF7C10", "#45CFEF", "#513A87"]
FONT = "Cairo, Tajawal, sans-serif"

_LAYOUT = dict(
    template="plotly_white",
    font=dict(family=FONT, size=12, color="#1A1A2E"),
    margin=dict(l=20, r=20, t=45, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(font=dict(family=FONT, size=11)),
)


def create_bar_chart(data: pd.DataFrame, x: str, y: str, title: str = "",
                     color: str = "#CE2E26", horizontal: bool = False) -> go.Figure:
    """رسم بياني عمودي / أفقي"""
    if horizontal:
        fig = go.Figure(go.Bar(
            y=data[x], x=data[y], orientation="h",
            marker=dict(color=color, line=dict(width=0)),
            text=data[y], textposition="outside",
            textfont=dict(family=FONT, size=11),
        ))
    else:
        fig = go.Figure(go.Bar(
            x=data[x], y=data[y],
            marker=dict(color=color, line=dict(width=0)),
            text=data[y], textposition="outside",
            textfont=dict(family=FONT, size=11),
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(family=FONT, size=14, color="#1A1A2E")),
        height=320,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0", zeroline=False),
        **_LAYOUT,
    )
    return fig


def create_multibar_chart(data: pd.DataFrame, x: str, y_cols: list,
                          labels: list = None, title: str = "") -> go.Figure:
    """رسم بياني بأعمدة متعددة"""
    fig = go.Figure()
    labels = labels or y_cols
    for col, lbl, color in zip(y_cols, labels, BRAND_COLORS):
        fig.add_trace(go.Bar(
            name=lbl, x=data[x], y=data[col],
            marker_color=color,
            text=data[col], textposition="outside",
            textfont=dict(family=FONT, size=10),
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(family=FONT, size=14)),
        barmode="group", height=320,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0"),
        **_LAYOUT,
    )
    return fig


def create_pie_chart(data: pd.DataFrame, names: str, values: str,
                     title: str = "", donut: bool = True) -> go.Figure:
    """رسم بياني دائري / حلقي"""
    fig = go.Figure(go.Pie(
        labels=data[names],
        values=data[values],
        hole=0.45 if donut else 0,
        marker=dict(colors=BRAND_COLORS, line=dict(color="white", width=2)),
        textfont=dict(family=FONT, size=12),
        textinfo="label+percent",
        insidetextorientation="horizontal",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(family=FONT, size=14)),
        height=320,
        **_LAYOUT,
    )
    return fig


def create_line_chart(data: pd.DataFrame, x: str, y_cols,
                      labels: list = None, title: str = "") -> go.Figure:
    """رسم بياني خطي"""
    if isinstance(y_cols, str):
        y_cols = [y_cols]
    labels = labels or y_cols
    fig = go.Figure()
    for col, lbl, color in zip(y_cols, labels, BRAND_COLORS):
        fig.add_trace(go.Scatter(
            x=data[x], y=data[col],
            mode="lines+markers",
            name=lbl,
            line=dict(color=color, width=2.5),
            marker=dict(size=7, color=color,
                        line=dict(color="white", width=1.5)),
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(family=FONT, size=14)),
        height=320,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0", zeroline=False),
        **_LAYOUT,
    )
    return fig


def create_gauge(value: float, title: str = "", max_val: float = 100,
                 thresholds: tuple = (70, 90)) -> go.Figure:
    """مقياس نسبة مئوية"""
    lo, hi = thresholds
    color = "#42924B" if value >= hi else ("#F1B944" if value >= lo else "#CE2E26")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(suffix="%", font=dict(family=FONT, size=28, color=color)),
        title=dict(text=title, font=dict(family=FONT, size=13, color="#1A1A2E")),
        gauge=dict(
            axis=dict(range=[0, max_val], tickwidth=1,
                      tickcolor="#E2E8F0", tickfont=dict(family=FONT, size=10)),
            bar=dict(color=color, thickness=0.3),
            bgcolor="white",
            borderwidth=0,
            steps=[
                dict(range=[0,    lo], color="#FFEBEE"),
                dict(range=[lo,   hi], color="#FFF8E1"),
                dict(range=[hi, max_val], color="#E8F5E9"),
            ],
        ),
    ))
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT))
    return fig


# ✅ دالة عرض الرسم البياني
def display_chart(fig: go.Figure, key: str = None):
    """عرض الرسم البياني في Streamlit"""
    st.plotly_chart(fig, use_container_width=True, key=key)