import pygame

from constants import PANEL, PANEL_EDGE, TEXT, MUTED, GOOD, BAD, GOLD, ACCENT, CANVAS
from models.auction_result import AuctionRoundResult
from ui.render.draw import draw_panel, draw_text


def _profit_color(value: float) -> tuple[int, int, int]:
    if value > 1e-6:
        return GOOD
    if value < -1e-6:
        return BAD
    return MUTED


def render_auction_summary_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    summary: AuctionRoundResult,
    fonts: dict[str, pygame.font.Font],
    draw_thumbnail,
):
    draw_panel(surface, rect)
    pygame.draw.rect(surface, (*ACCENT, 35), rect, border_radius=14)

    header_y = rect.y + 12
    draw_text(surface, f"{summary.team_name} Team — Round Summary", rect.x + 14, header_y, fonts["title"], summary.team_color)
    draw_text(
        surface,
        f"Sold {summary.sold_count}/{summary.total_count} lots",
        rect.x + 14,
        header_y + 26,
        fonts["small"],
        MUTED,
    )

    _render_totals(surface, rect, summary, fonts)
    _render_items(surface, rect, summary, fonts, draw_thumbnail)
    _render_callouts(surface, rect, summary, fonts)


def _render_totals(surface, rect, summary: AuctionRoundResult, fonts):
    totals_rect = pygame.Rect(rect.x + 12, rect.y + 56, rect.width - 24, 74)
    pygame.draw.rect(surface, PANEL, totals_rect, border_radius=10)
    pygame.draw.rect(surface, PANEL_EDGE, totals_rect, width=2, border_radius=10)

    cols = [
        ("Total spent", summary.spent_total, MUTED),
        ("Total sold", summary.sold_total, GOLD),
        ("Total profit", summary.profit_total, _profit_color(summary.profit_total)),
        ("ROI", summary.roi * 100, ACCENT),
    ]
    col_w = totals_rect.width // len(cols)
    for idx, (label, value, col) in enumerate(cols):
        x = totals_rect.x + idx * col_w + 12
        draw_text(surface, label, x, totals_rect.y + 8, fonts["small"], MUTED)
        suffix = "%" if label == "ROI" else ""
        formatted = f"{value:+.0f}{suffix}" if label == "Total profit" else f"{value:,.0f}{suffix}"
        draw_text(surface, formatted, x, totals_rect.y + 30, fonts["title"], col)


def _render_items(surface, rect, summary: AuctionRoundResult, fonts, draw_thumbnail):
    list_top = rect.y + 138
    list_height = rect.height - 220
    row_h = 78
    max_rows = list_height // row_h
    visible = summary.lots[:max_rows]

    y = list_top
    for lot in visible:
        row_rect = pygame.Rect(rect.x + 12, y, rect.width - 24, row_h - 8)
        pygame.draw.rect(surface, CANVAS, row_rect, border_radius=10)
        pygame.draw.rect(surface, PANEL_EDGE, row_rect, width=1, border_radius=10)
        pygame.draw.rect(surface, (*ACCENT, 18), row_rect, border_radius=10)

        thumb_rect = pygame.Rect(row_rect.x + 10, row_rect.y + 10, 64, 64)
        draw_thumbnail(surface, thumb_rect, lot)

        text_x = thumb_rect.right + 10
        draw_text(surface, lot.name[:28], text_x, row_rect.y + 6, fonts["body"], TEXT)
        meta = f"Paid ${lot.paid:.0f}  |  Appraised ${lot.appraised:.0f}  |  Sold ${lot.sold:.0f}"
        draw_text(surface, meta, text_x, row_rect.y + 30, fonts["small"], MUTED)
        draw_text(surface, f"Category: {lot.category}", text_x, row_rect.y + 48, fonts["small"], MUTED)

        profit = lot.profit
        prof_col = _profit_color(profit)
        draw_text(surface, f"{profit:+.0f}", row_rect.right - 60, row_rect.y + 6, fonts["body"], prof_col)
        y += row_h


def _render_callouts(surface, rect, summary: AuctionRoundResult, fonts):
    callout_rect = pygame.Rect(rect.x + 12, rect.bottom - 70, rect.width - 24, 56)
    pygame.draw.rect(surface, PANEL, callout_rect, border_radius=12)
    pygame.draw.rect(surface, PANEL_EDGE, callout_rect, width=2, border_radius=12)

    best = summary.best_lot
    worst = summary.worst_lot

    if best:
        draw_text(surface, "Best lot", callout_rect.x + 12, callout_rect.y + 8, fonts["small"], GOLD)
        draw_text(surface, f"{best.name} ({best.profit:+.0f})", callout_rect.x + 12, callout_rect.y + 28, fonts["body"], _profit_color(best.profit))

    if worst:
        draw_text(surface, "Biggest disappointment", callout_rect.centerx + 12, callout_rect.y + 8, fonts["small"], MUTED)
        draw_text(surface, f"{worst.name} ({worst.profit:+.0f})", callout_rect.centerx + 12, callout_rect.y + 28, fonts["body"], _profit_color(worst.profit))
