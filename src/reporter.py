import calendar
import io
from pathlib import Path
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


PALETTE = {
    "income": "#2ecc71",
    "expense": "#e74c3c",
    "net_pos": "#3498db",
    "net_neg": "#e67e22",
    "bg": "#f8f9fa",
    "accent": "#2c3e50",
    "categories": [
        "#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
        "#1abc9c", "#e67e22", "#34495e", "#e91e63", "#00bcd4",
    ],
}


def _fig_to_image(fig, width_cm: float = 16) -> RLImage:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    img = RLImage(buf)
    aspect = img.imageHeight / img.imageWidth
    img.drawWidth = width_cm * cm
    img.drawHeight = img.drawWidth * aspect
    return img


def _chart_category_breakdown(by_category: pd.Series) -> RLImage | None:
    if by_category.empty:
        return None

    top = by_category.head(9).copy()
    if len(by_category) > 9:
        top["other"] = by_category.iloc[9:].sum()

    fig, (ax_pie, ax_bar) = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor("white")

    colors_list = PALETTE["categories"][:len(top)]
    wedges, texts, autotexts = ax_pie.pie(
        top.values,
        labels=None,
        autopct="%1.1f%%",
        colors=colors_list,
        startangle=90,
        pctdistance=0.8,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    for at in autotexts:
        at.set_fontsize(8)
    ax_pie.set_title("Expense Distribution", fontsize=13, fontweight="bold", pad=15)
    ax_pie.legend(
        [mpatches.Patch(color=c, label=k.replace("_", " ").title()) for k, c in zip(top.index, colors_list)],
        loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=8,
    )

    bars = ax_bar.barh(
        [k.replace("_", " ").title() for k in top.index[::-1]],
        top.values[::-1],
        color=colors_list[::-1],
        edgecolor="white", linewidth=0.5,
    )
    max_val = max(top.values) if len(top.values) > 0 else 1
    for bar, val in zip(bars, top.values[::-1]):
        ax_bar.text(
            bar.get_width() + max_val * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{val:,.0f}", va="center", ha="left", fontsize=8,
        )
    ax_bar.set_title("Amount by Category", fontsize=13, fontweight="bold")
    ax_bar.spines[["top", "right"]].set_visible(False)
    ax_bar.set_xlabel("Amount (€)", fontsize=9)

    fig.tight_layout(pad=2)
    return _fig_to_image(fig, 16)


def _chart_monthly_trend(trend: pd.DataFrame, currency: str) -> RLImage | None:
    if trend.empty:
        return None

    labels = [str(p) for p in trend.index]
    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 4.5))
    fig.patch.set_facecolor("white")

    ax.bar([i - width / 2 for i in x], trend["income"], width, label="Income",
           color=PALETTE["income"], alpha=0.85, edgecolor="white")
    ax.bar([i + width / 2 for i in x], trend["expenses"], width, label="Expenses",
           color=PALETTE["expense"], alpha=0.85, edgecolor="white")
    ax.plot(list(x), trend["net"], color=PALETTE["net_pos"], marker="o",
            linewidth=2, markersize=5, label="Net", zorder=5)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_title("Monthly Income vs Expenses (last 12 months)", fontsize=13, fontweight="bold")
    ax.set_ylabel(f"Amount ({currency})", fontsize=9)
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _fig_to_image(fig, 16)


def generate_pdf(
    summary: dict,
    by_category: pd.Series,
    trend: pd.DataFrame,
    top_exp: pd.DataFrame,
    year: int,
    month: int,
    config: dict,
    output_path: str,
) -> str:
    currency = config.get("currency", "€")
    month_name = calendar.month_name[month]
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"report_{year}_{month:02d}.pdf"

    doc = SimpleDocTemplate(
        str(filepath), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontSize=22, textColor=colors.HexColor(PALETTE["accent"]),
        alignment=TA_CENTER, spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"],
        fontSize=11, textColor=colors.grey,
        alignment=TA_CENTER, spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "ReportSection", parent=styles["Heading2"],
        fontSize=13, textColor=colors.HexColor(PALETTE["accent"]),
        spaceBefore=14, spaceAfter=8, borderPad=4,
    )
    small = ParagraphStyle("ReportSmall", parent=styles["Normal"], fontSize=8)
    normal = styles["Normal"]

    def section(title: str) -> list:
        return [
            HRFlowable(width="100%", thickness=1, color=colors.HexColor(PALETTE["accent"])),
            Paragraph(title, section_style),
        ]

    story = []

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Monthly Financial Report", title_style))
    story.append(Paragraph(f"{month_name} {year}", subtitle_style))
    story.append(Spacer(1, 0.5 * cm))

    kpi_data = [
        [
            Paragraph(f"<b>{currency} {summary['income']:,.2f}</b><br/><font size=8>Total Income</font>", normal),
            Paragraph(f"<b>{currency} {summary['expenses']:,.2f}</b><br/><font size=8>Total Expenses</font>", normal),
            Paragraph(
                f"<b>{currency} {abs(summary['net']):,.2f}</b><br/>"
                f"<font size=8>{'Savings' if summary['net'] >= 0 else 'Deficit'}</font>",
                normal,
            ),
            Paragraph(f"<b>{summary['savings_rate']:.1f}%</b><br/><font size=8>Savings Rate</font>", normal),
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[4.2 * cm] * 4)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#e8f8f0")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#fde8e8")),
        ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#e8f0fd")),
        ("BACKGROUND", (3, 0), (3, 0), colors.HexColor("#fef9e8")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.5 * cm))

    cat_img = _chart_category_breakdown(by_category)
    if cat_img:
        story += section("Expense Breakdown by Category")
        story.append(cat_img)
        story.append(Spacer(1, 0.3 * cm))

    trend_img = _chart_monthly_trend(trend, currency)
    if trend_img:
        story += section("Monthly Trend")
        story.append(trend_img)
        story.append(Spacer(1, 0.3 * cm))

    if not by_category.empty:
        story += section("Category Summary")
        total_exp = by_category.sum()
        cat_table_data = [["Category", "Amount", "% of Expenses"]]
        for cat, amt in by_category.items():
            pct = amt / total_exp * 100 if total_exp > 0 else 0
            cat_table_data.append([
                cat.replace("_", " ").title(),
                f"{currency} {amt:,.2f}",
                f"{pct:.1f}%",
            ])
        cat_table = Table(cat_table_data, colWidths=[8 * cm, 4 * cm, 4 * cm])
        cat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PALETTE["accent"])),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(cat_table)
        story.append(Spacer(1, 0.3 * cm))

    if not top_exp.empty:
        story += section("Top Expenses")
        top_data = [["Date", "Description", "Category", "Amount"]]
        for _, row in top_exp.iterrows():
            top_data.append([
                row["date"].strftime("%d/%m/%Y"),
                str(row["description"])[:45],
                row["category"].replace("_", " ").title(),
                f"{currency} {row['amount']:,.2f}",
            ])
        top_table = Table(top_data, colWidths=[2.5 * cm, 8 * cm, 3.5 * cm, 3 * cm])
        top_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PALETTE["accent"])),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(top_table)

    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph(
        f"Generated on {date.today().strftime('%d %B %Y')} — {summary['n_transactions']} transactions",
        ParagraphStyle("ReportFooter", parent=small, alignment=TA_CENTER, textColor=colors.grey),
    ))

    doc.build(story)
    return str(filepath)
