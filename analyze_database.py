"""Profile data/campus_customs.db and write an interactive overview to output/database_overview.html.

Run:  .venv\\Scripts\\python.exe analyze_database.py
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "data" / "campus_customs.db"
OUT_PATH = APP_DIR / "output" / "database_overview.html"

SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
CATEGORY_ORDER = ["Crewnecks", "Hoodies", "T-shirts", "Quarter-zips", "Jackets & fleece", "Long-sleeve & mockneck"]


def category(garment_type: str) -> str:
    """Collapse the 22 free-text garment_type labels into shop categories."""
    g = garment_type.lower()
    if "t-shirt" in g:
        return "T-shirts"
    if "quarter-zip" in g:
        return "Quarter-zips"
    if "jacket" in g:
        return "Jackets & fleece"
    if "hood" in g:
        return "Hoodies"
    if "crew" in g:
        return "Crewnecks"
    return "Long-sleeve & mockneck"


def color_family(color: str) -> str:
    c = color.lower()
    if c in ("navy", "navy blue"):
        return "navy"
    if "gray" in c or "charcoal" in c:
        return "gray"
    if c in ("cream", "ivory"):
        return "cream"
    if c in ("light blue", "royal blue"):
        return "blue"
    return c


def mask_name(name: str) -> str:
    """Initials only, e.g. 'Ada Lovelace' -> 'A. L.' (the report is public)."""
    return " ".join(f"{part[0]}." for part in name.split() if part) or "—"


def mask_email(email: str) -> str:
    """Keep the public report free of real addresses."""
    local, _, domain = email.partition("@")
    return f"{local[0]}***@{domain}"


def profile(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(
        "SELECT product_id, name, garment_type, colors, price FROM catalogue"
    ).fetchall()
    cat_of = {}
    by_cat = defaultdict(lambda: {"count": 0, "prices": set(), "labels": set()})
    colors = Counter()
    raw_colors = set()
    for pid, _name, gtype, colors_json, price in rows:
        cat = category(gtype)
        cat_of[pid] = cat
        by_cat[cat]["count"] += 1
        by_cat[cat]["prices"].add(price)
        by_cat[cat]["labels"].add(gtype)
        for col in json.loads(colors_json):
            raw_colors.add(col.lower())
            colors[color_family(col)] += 1

    categories = [
        {
            "name": c,
            "count": by_cat[c]["count"],
            "prices": sorted(by_cat[c]["prices"]),
            "labels": len(by_cat[c]["labels"]),
        }
        for c in CATEGORY_ORDER
    ]
    prices = [
        {"price": p, "count": n}
        for p, n in conn.execute("SELECT price, COUNT(*) FROM catalogue GROUP BY price ORDER BY price")
    ]

    inv = conn.execute("SELECT product_id, size, quantity FROM inventory").fetchall()
    qty_counts = Counter(q for _, _, q in inv)
    units_by_size = Counter()
    heat = defaultdict(lambda: [0, 0])  # (category, size) -> [out_of_stock, total]
    oos_by_product = Counter()
    for pid, size, qty in inv:
        units_by_size[size] += qty
        cell = heat[(cat_of[pid], size)]
        cell[1] += 1
        if qty == 0:
            cell[0] += 1
            oos_by_product[pid] += 1
    names = dict(conn.execute("SELECT product_id, name FROM catalogue"))
    most_sold_out = [
        {"name": names[pid], "category": cat_of[pid], "sizes_out": n}
        for pid, n in oos_by_product.most_common()
        if n >= 3
    ]

    users = []
    for uid, name, email, created, _first, _last in conn.execute(
        "SELECT id, name, email, created_at, first_name, last_name FROM users ORDER BY id"
    ):
        msgs = dict(
            conn.execute("SELECT role, COUNT(*) FROM chat_messages WHERE user_id = ? GROUP BY role", (uid,))
        )
        users.append(
            {
                "id": uid,
                "name": mask_name(name),
                "email": mask_email(email),
                "created": created,
                "user_msgs": msgs.get("user", 0),
                "assistant_msgs": msgs.get("assistant", 0),
            }
        )

    return {
        "summary": {
            "products": len(rows),
            "garment_labels": len({r[2] for r in rows}),
            "price_points": len(prices),
            "min_price": min(p["price"] for p in prices),
            "max_price": max(p["price"] for p in prices),
            "raw_colors": len(raw_colors),
            "inventory_rows": len(inv),
            "units": sum(q for _, _, q in inv),
            "out_of_stock_rows": qty_counts[0],
            "fully_sold_out": sum(1 for pid in names if oos_by_product[pid] == len(SIZES)),
            "users": len(users),
            "messages": conn.execute("SELECT COUNT(*) FROM chat_messages").fetchone()[0],
            "messages_with_products": conn.execute(
                "SELECT COUNT(*) FROM chat_messages WHERE products_json IS NOT NULL"
            ).fetchone()[0],
        },
        "categories": categories,
        "prices": prices,
        "colors": [{"name": c, "count": n} for c, n in colors.most_common(10)],
        "quantities": [{"qty": q, "count": qty_counts[q]} for q in sorted(qty_counts)],
        "units_by_size": [{"size": s, "units": units_by_size[s]} for s in SIZES],
        "heatmap": {
            "sizes": SIZES,
            "rows": [
                {
                    "category": c,
                    "cells": [
                        {"size": s, "out": heat[(c, s)][0], "total": heat[(c, s)][1]} for s in SIZES
                    ],
                }
                for c in CATEGORY_ORDER
            ],
        },
        "most_sold_out": most_sold_out,
        "users": users,
    }


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Campus Customs database overview</title>
<style>
.viz-root {
  color-scheme: light;
  --page: #f4f8fd; --surface-1: #fcfcfb; --brand: #0d366b; --brand-2: #1c5cab;
  --text-primary: #0b0b0b; --text-secondary: #52514e; --text-muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --series-1: #2a78d6; --series-2: #eb6834; --critical: #d03b3b;
  --seq-0: #f0efec; --seq-1: #cde2fb; --seq-2: #9ec5f4; --seq-3: #6da7ec; --seq-4: #3987e5; --seq-5: #256abf; --seq-6: #184f95; --seq-7: #0d366b;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .viz-root {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19; --brand: #86b6ef; --brand-2: #5598e7;
    --text-primary: #ffffff; --text-secondary: #c3c2b7; --text-muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --series-1: #3987e5; --series-2: #d95926; --critical: #d03b3b;
    --seq-0: #383835; --seq-1: #104281; --seq-2: #184f95; --seq-3: #256abf; --seq-4: #2a78d6; --seq-5: #5598e7; --seq-6: #86b6ef; --seq-7: #cde2fb;
  }
}
* { box-sizing: border-box; }
body { margin: 0; }
.viz-root { background: var(--page); color: var(--text-primary); font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; min-height: 100vh; }
header { background: linear-gradient(120deg, #0d366b, #1c5cab); color: #fff; padding: 32px 40px 28px; }
header h1 { margin: 0 0 4px; font-size: 26px; font-weight: 650; }
header p { margin: 0; color: #cde2fb; max-width: 760px; }
main { max-width: 1180px; margin: 0 auto; padding: 24px 24px 64px; }
section { margin-top: 28px; }
h2 { font-size: 19px; margin: 0 0 4px; color: var(--brand); }
.lede { margin: 0 0 14px; color: var(--text-secondary); max-width: 820px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-bottom: 14px; }
.tile, .card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; }
.tile { padding: 14px 16px; }
.tile .v { font-size: 26px; font-weight: 650; }
.tile .l { color: var(--text-secondary); font-size: 13px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(440px, 1fr)); gap: 14px; }
.card { padding: 16px 18px 12px; }
.card h3 { margin: 0; font-size: 15px; }
.card .sub { margin: 2px 0 10px; color: var(--text-secondary); font-size: 13px; }
svg { display: block; width: 100%; height: auto; overflow: visible; }
svg text { fill: var(--text-secondary); font-size: 12px; }
svg .val { fill: var(--text-primary); font-weight: 600; }
svg .tick { fill: var(--text-muted); font-size: 11px; font-variant-numeric: tabular-nums; }
.mark { cursor: default; outline: none; }
.mark:hover, .mark:focus { opacity: .82; }
.legend { display: flex; gap: 16px; flex-wrap: wrap; font-size: 12px; color: var(--text-secondary); margin: 4px 0 6px; }
.legend span::before { content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; background: var(--c); }
.ramp { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-secondary); margin-top: 6px; }
.ramp i { display: inline-block; width: 22px; height: 10px; }
details { margin-top: 8px; font-size: 13px; }
summary { cursor: pointer; color: var(--brand-2); }
table { border-collapse: collapse; width: 100%; margin-top: 6px; font-size: 13px; }
th, td { text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--grid); }
th { color: var(--text-secondary); font-weight: 600; }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
.schema { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
.schema .card h3 { color: var(--brand); font-family: ui-monospace, Consolas, monospace; font-size: 14px; }
.schema ul { margin: 6px 0 0; padding-left: 18px; font-family: ui-monospace, Consolas, monospace; font-size: 12px; color: var(--text-secondary); }
.schema .key { color: var(--brand-2); font-weight: 700; }
.links { margin: 10px 0 0; color: var(--text-secondary); font-size: 13px; }
.note { font-size: 12px; color: var(--text-muted); margin-top: 6px; }
#tip { position: fixed; pointer-events: none; z-index: 10; background: var(--surface-1); color: var(--text-primary); border: 1px solid var(--border); border-radius: 8px; padding: 7px 10px; font-size: 12px; box-shadow: 0 4px 16px rgba(0,0,0,.14); display: none; max-width: 260px; }
#tip b { display: block; margin-bottom: 2px; }
</style>
</head>
<body>
<div class="viz-root">
<header>
  <h1>Campus Customs database overview</h1>
  <p>What is inside <code>data/campus_customs.db</code>: the product catalogue, stock by size, and shopper accounts, generated by <code>analyze_database.py</code>.</p>
</header>
<main>
  <section>
    <h2>How the tables connect</h2>
    <p class="lede">Four tables. <code>product_id</code> links a catalogue item to its six size rows in inventory; <code>user_id</code> links each chat message to the shopper who sent or received it.</p>
    <div class="schema" id="schema"></div>
  </section>

  <section>
    <h2>Catalogue</h2>
    <p class="lede">One row per product. Prices are set by garment type, so every product in a category costs the same (with a few $45 exceptions). The raw <code>garment_type</code> text is inconsistent, so the charts group it into six shop categories.</p>
    <div class="tiles" id="cat-tiles"></div>
    <div class="grid">
      <div class="card"><h3>Products by category</h3><p class="sub">Count of catalogue items, grouped from the raw garment labels</p><div id="c-cat"></div><details><summary>Table view</summary><div id="t-cat"></div></details></div>
      <div class="card"><h3>Products at each price</h3><p class="sub">Only seven price points across the whole catalogue</p><div id="c-price"></div><details><summary>Table view</summary><div id="t-price"></div></details></div>
      <div class="card"><h3>Most common colors</h3><p class="sub">Products listing each color (similar shades grouped, e.g. "navy" + "navy blue")</p><div id="c-color"></div><details><summary>Table view</summary><div id="t-color"></div></details></div>
    </div>
  </section>

  <section>
    <h2>Inventory</h2>
    <p class="lede">Six rows per product, one per size (XS to XXL). Quantities take only eight values from 0 to 25, and about a quarter of all size rows are sold out, so the chatbot must check the size before promising stock.</p>
    <div class="tiles" id="inv-tiles"></div>
    <div class="grid">
      <div class="card"><h3>Size rows by stock level</h3><p class="sub">How many product-size rows hold each quantity</p><div id="c-qty"></div><details><summary>Table view</summary><div id="t-qty"></div></details></div>
      <div class="card"><h3>Units in stock by size</h3><p class="sub">Total units across all products</p><div id="c-size"></div><details><summary>Table view</summary><div id="t-size"></div></details></div>
      <div class="card"><h3>Where sizes are sold out</h3><p class="sub">Share of product-size rows with 0 units, by category and size</p><div id="c-heat"></div><div class="ramp" id="ramp"></div><details><summary>Table view</summary><div id="t-heat"></div></details></div>
      <div class="card"><h3>Products with the most sold-out sizes</h3><p class="sub">3 or more of 6 sizes at 0 units</p><div id="t-soldout"></div></div>
    </div>
  </section>

  <section>
    <h2>Users</h2>
    <p class="lede">Shopper accounts created on the site. Passwords are stored only as hashes. Chat history is saved per user, so returning shoppers can pick up a conversation. Names and emails are masked in this report.</p>
    <div class="tiles" id="user-tiles"></div>
    <div class="grid">
      <div class="card"><h3>Accounts</h3><p class="sub">Every row in <code>users</code> (password hashes omitted)</p><div id="t-users"></div></div>
      <div class="card"><h3>Chat messages per user</h3><p class="sub">Messages saved in <code>chat_messages</code>, by who wrote them</p><div class="legend"><span style="--c:var(--series-1)">Shopper</span><span style="--c:var(--series-2)">Assistant</span></div><div id="c-chat"></div><details><summary>Table view</summary><div id="t-chat"></div></details></div>
    </div>
  </section>
</main>
<div id="tip" role="tooltip"></div>
</div>
<script>
const D = __DATA__;
const NS = "http://www.w3.org/2000/svg";
const fmt = n => n.toLocaleString("en-US");
const money = n => "$" + n.toFixed(0);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

function el(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}
function text(parent, x, y, str, attrs = {}) { const t = el("text", {x, y, ...attrs}, parent); t.textContent = str; return t; }

// Bar with 4px rounded data end, square at the baseline.
function barPath(x, y, w, h, horizontal) {
  const r = Math.min(4, horizontal ? w / 2 : h / 2, horizontal ? h / 2 : w / 2);
  if (horizontal) return `M${x},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h - r}Q${x + w},${y + h} ${x + w - r},${y + h}H${x}Z`;
  return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`;
}

const tip = document.getElementById("tip");
function attachTip(node, html) {
  node.classList.add("mark");
  node.setAttribute("tabindex", "0");
  const show = ev => {
    tip.innerHTML = html; tip.style.display = "block";
    const r = ev && ev.clientX !== undefined ? {x: ev.clientX, y: ev.clientY} : (b => ({x: b.right, y: b.top}))(node.getBoundingClientRect());
    const w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = Math.min(r.x + 14, innerWidth - w - 8) + "px";
    tip.style.top = Math.max(8, r.y - h - 10) + "px";
  };
  node.addEventListener("mousemove", show);
  node.addEventListener("focus", () => show());
  node.addEventListener("mouseleave", () => tip.style.display = "none");
  node.addEventListener("blur", () => tip.style.display = "none");
}

function niceMax(v) { const p = Math.pow(10, Math.floor(Math.log10(v))); for (const m of [1, 2, 5, 10]) if (m * p >= v) return m * p; }
// Whole-number gridlines: 4 steps when they divide evenly, else 5.
const divs = max => max % 4 === 0 ? 4 : 5;

function hbar(id, rows, {label, value, tipHtml, color = () => "var(--series-1)", labelW = 170}) {
  const W = 520, rowH = 30, barH = 18, H = rows.length * rowH + 24, plotW = W - labelW - 40;
  const max = niceMax(Math.max(...rows.map(value)));
  const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, role: "img"}, document.getElementById(id));
  for (let i = 0, n = divs(max); i <= n; i++) {
    const x = labelW + plotW * i / n;
    el("line", {x1: x, x2: x, y1: 0, y2: rows.length * rowH, stroke: "var(--grid)", "stroke-width": 1}, svg);
    text(svg, x, rows.length * rowH + 16, fmt(max * i / n), {class: "tick", "text-anchor": "middle"});
  }
  el("line", {x1: labelW, x2: labelW, y1: 0, y2: rows.length * rowH, stroke: "var(--axis)"}, svg);
  rows.forEach((r, i) => {
    const y = i * rowH + (rowH - barH) / 2, w = plotW * value(r) / max;
    text(svg, labelW - 10, y + barH / 2 + 4, label(r), {"text-anchor": "end"});
    const g = el("g", {}, svg);
    el("rect", {x: labelW, y: i * rowH, width: plotW + 40, height: rowH, fill: "transparent"}, g);
    el("path", {d: barPath(labelW, y, Math.max(w, 1), barH, true), fill: color(r)}, g);
    text(g, labelW + w + 6, y + barH / 2 + 4, fmt(value(r)), {class: "val"});
    attachTip(g, tipHtml(r));
  });
}

function vbar(id, rows, {label, value, tipHtml, color = () => "var(--series-1)", direct = () => false, anchor = "middle"}) {
  const W = 520, H = 230, padL = 40, padB = 28, padT = 16, plotH = H - padB - padT, plotW = W - padL - 8;
  const max = niceMax(Math.max(...rows.map(value)));
  const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, role: "img"}, document.getElementById(id));
  for (let i = 0, n = divs(max); i <= n; i++) {
    const y = padT + plotH - plotH * i / n;
    el("line", {x1: padL, x2: W - 8, y1: y, y2: y, stroke: i ? "var(--grid)" : "var(--axis)"}, svg);
    text(svg, padL - 8, y + 4, fmt(max * i / n), {class: "tick", "text-anchor": "end"});
  }
  const slot = plotW / rows.length, bw = Math.min(46, slot - 2);
  rows.forEach((r, i) => {
    const x = padL + i * slot + (slot - bw) / 2, h = plotH * value(r) / max, y = padT + plotH - h;
    const g = el("g", {}, svg);
    el("rect", {x: padL + i * slot, y: padT, width: slot, height: plotH, fill: "transparent"}, g);
    el("path", {d: barPath(x, y, bw, Math.max(h, 1), false), fill: color(r)}, g);
    if (direct(r)) text(g, anchor === "start" ? x : x + bw / 2, y - 6, direct(r), {class: "val", "text-anchor": anchor});
    text(svg, x + bw / 2, H - 8, label(r), {"text-anchor": "middle"});
    attachTip(g, tipHtml(r));
  });
}

function stackedH(id, rows, series, {label, labelW = 130}) {
  const W = 520, rowH = 34, barH = 20, H = rows.length * rowH + 24, plotW = W - labelW - 40;
  const max = niceMax(Math.max(...rows.map(r => series.reduce((s, k) => s + r[k.key], 0))) || 1);
  const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, role: "img"}, document.getElementById(id));
  for (let i = 0, n = divs(max); i <= n; i++) {
    const x = labelW + plotW * i / n;
    el("line", {x1: x, x2: x, y1: 0, y2: rows.length * rowH, stroke: "var(--grid)"}, svg);
    text(svg, x, rows.length * rowH + 16, fmt(max * i / n), {class: "tick", "text-anchor": "middle"});
  }
  el("line", {x1: labelW, x2: labelW, y1: 0, y2: rows.length * rowH, stroke: "var(--axis)"}, svg);
  rows.forEach((r, i) => {
    const y = i * rowH + (rowH - barH) / 2;
    text(svg, labelW - 10, y + barH / 2 + 4, label(r), {"text-anchor": "end"});
    let x = labelW;
    const total = series.reduce((s, k) => s + r[k.key], 0);
    series.forEach((k, j) => {
      const w = plotW * r[k.key] / max;
      if (!w) return;
      const g = el("g", {}, svg);
      const last = j === series.length - 1 || series.slice(j + 1).every(n => !r[n.key]);
      const gap = last ? 0 : 2;
      el(last ? "path" : "rect", last ? {d: barPath(x, y, w, barH, true), fill: k.color} : {x, y, width: Math.max(w - gap, 0), height: barH, fill: k.color}, g);
      attachTip(g, `<b>${esc(label(r))}</b>${k.name}: ${r[k.key]} messages`);
      x += w;
    });
    if (total) text(svg, x + 6, y + barH / 2 + 4, fmt(total), {class: "val"});
    else text(svg, labelW + 6, y + barH / 2 + 4, "no messages yet", {class: "tick"});
  });
}

function heatmap(id, hm) {
  const W = 520, labelW = 170, top = 22, cellH = 30, n = hm.sizes.length, cellW = (W - labelW) / n, H = top + hm.rows.length * cellH;
  const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, role: "img"}, document.getElementById(id));
  const steps = ["--seq-0", "--seq-1", "--seq-2", "--seq-3", "--seq-4", "--seq-5", "--seq-6", "--seq-7"];
  const fill = share => `var(${steps[share === 0 ? 0 : Math.min(7, 1 + Math.floor(share * 7 / 0.5))]})`;
  hm.sizes.forEach((s, j) => text(svg, labelW + j * cellW + cellW / 2, 14, s, {"text-anchor": "middle"}));
  hm.rows.forEach((row, i) => {
    const y = top + i * cellH;
    text(svg, labelW - 10, y + cellH / 2 + 4, row.category, {"text-anchor": "end"});
    row.cells.forEach((c, j) => {
      const share = c.out / c.total;
      const g = el("g", {}, svg);
      el("rect", {x: labelW + j * cellW + 1, y: y + 1, width: cellW - 2, height: cellH - 2, rx: 4, fill: fill(share)}, g);
      attachTip(g, `<b>${esc(row.category)} · ${c.size}</b>${c.out} of ${c.total} products sold out (${Math.round(share * 100)}%)`);
    });
  });
  const ramp = document.getElementById("ramp");
  ramp.innerHTML = "0% " + steps.map(s => `<i style="background:var(${s})"></i>`).join("") + " 50%+ sold out";
}

function table(id, cols, rows) {
  const head = cols.map(c => `<th class="${c.n ? "n" : ""}">${c.h}</th>`).join("");
  const body = rows.map(r => "<tr>" + cols.map(c => `<td class="${c.n ? "n" : ""}">${esc(c.v(r))}</td>`).join("") + "</tr>").join("");
  document.getElementById(id).innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}
function tiles(id, items) {
  document.getElementById(id).innerHTML = items.map(([v, l]) => `<div class="tile"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
}

// Schema cards
const SCHEMA = [
  ["catalogue", ["product_id", "name", "garment_type", "description", "colors", "search_tags", "image_file_path", "price"], ["product_id"], `${D.summary.products} rows`],
  ["inventory", ["id", "product_id → catalogue", "size", "quantity"], ["id"], `${fmt(D.summary.inventory_rows)} rows`],
  ["users", ["id", "name", "first_name", "last_name", "email", "password_hash", "created_at"], ["id"], `${D.summary.users} rows`],
  ["chat_messages", ["id", "user_id → users", "role", "content", "products_json", "created_at"], ["id"], `${D.summary.messages} rows`],
];
document.getElementById("schema").innerHTML = SCHEMA.map(([t, f, k, n]) =>
  `<div class="card"><h3>${t}</h3><div class="sub">${n}</div><ul>${f.map(x => `<li class="${k.includes(x) ? "key" : ""}">${esc(x)}</li>`).join("")}</ul></div>`).join("");

const S = D.summary;
tiles("cat-tiles", [[S.products, "products"], [`${money(S.min_price)}–${money(S.max_price)}`, "price range"], [S.price_points, "distinct prices"], [S.garment_labels, "raw garment_type labels"], [S.raw_colors, "distinct color names"]]);
hbar("c-cat", D.categories, {label: r => r.name, value: r => r.count,
  tipHtml: r => `<b>${esc(r.name)}</b>${r.count} products · ${r.prices.map(money).join(", ")}<br>${r.labels} raw garment_type label${r.labels > 1 ? "s" : ""}`});
table("t-cat", [{h: "Category", v: r => r.name}, {h: "Products", n: 1, v: r => r.count}, {h: "Price(s)", v: r => r.prices.map(money).join(", ")}, {h: "Raw labels", n: 1, v: r => r.labels}], D.categories);
vbar("c-price", D.prices, {label: r => money(r.price), value: r => r.count, direct: r => r.count,
  tipHtml: r => `<b>${money(r.price)}</b>${r.count} products`});
table("t-price", [{h: "Price", v: r => money(r.price)}, {h: "Products", n: 1, v: r => r.count}], D.prices);
hbar("c-color", D.colors, {label: r => r.name, value: r => r.count, labelW: 110,
  tipHtml: r => `<b>${esc(r.name)}</b>appears on ${r.count} products`});
table("t-color", [{h: "Color", v: r => r.name}, {h: "Products", n: 1, v: r => r.count}], D.colors);

const oosPct = Math.round(100 * S.out_of_stock_rows / S.inventory_rows);
tiles("inv-tiles", [[fmt(S.inventory_rows), "size rows (102 × 6 sizes)"], [fmt(S.units), "units in stock"], [`${S.out_of_stock_rows} (${oosPct}%)`, "size rows sold out"], [S.fully_sold_out, "products sold out in every size"]]);
vbar("c-qty", D.quantities, {label: r => r.qty, value: r => r.count,
  color: r => r.qty === 0 ? "var(--critical)" : "var(--series-1)",
  direct: r => r.qty === 0 ? `⚠ Sold out · ${r.count}` : false, anchor: "start",
  tipHtml: r => `<b>${r.qty} units</b>${r.count} product-size rows${r.qty === 0 ? " (sold out)" : ""}`});
table("t-qty", [{h: "Quantity", n: 1, v: r => r.qty}, {h: "Size rows", n: 1, v: r => r.count}], D.quantities);
vbar("c-size", D.units_by_size, {label: r => r.size, value: r => r.units,
  tipHtml: r => `<b>Size ${r.size}</b>${fmt(r.units)} units in stock`});
table("t-size", [{h: "Size", v: r => r.size}, {h: "Units", n: 1, v: r => fmt(r.units)}], D.units_by_size);
heatmap("c-heat", D.heatmap);
table("t-heat", [{h: "Category", v: r => r.category}, ...D.heatmap.sizes.map((s, j) => ({h: s, n: 1, v: r => `${r.cells[j].out}/${r.cells[j].total}`}))], D.heatmap.rows);
table("t-soldout", [{h: "Product", v: r => r.name}, {h: "Category", v: r => r.category}, {h: "Sizes out", n: 1, v: r => `${r.sizes_out} of 6`}], D.most_sold_out);

tiles("user-tiles", [[S.users, "accounts"], [S.messages, "chat messages saved"], [S.messages_with_products, "assistant replies with product cards"]]);
table("t-users", [{h: "ID", n: 1, v: r => r.id}, {h: "Name", v: r => r.name}, {h: "Email", v: r => r.email}, {h: "Created", v: r => r.created}, {h: "Messages", n: 1, v: r => r.user_msgs + r.assistant_msgs}], D.users);
stackedH("c-chat", D.users, [{key: "user_msgs", name: "Shopper", color: "var(--series-1)"}, {key: "assistant_msgs", name: "Assistant", color: "var(--series-2)"}], {label: r => r.name});
table("t-chat", [{h: "User", v: r => r.name}, {h: "Shopper", n: 1, v: r => r.user_msgs}, {h: "Assistant", n: 1, v: r => r.assistant_msgs}], D.users);
</script>
</body>
</html>
"""


def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        data = profile(conn)
    finally:
        conn.close()
    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(TEMPLATE.replace("__DATA__", json.dumps(data)), encoding="utf-8")
    s = data["summary"]
    print(f"catalogue: {s['products']} products, {s['price_points']} prices, {s['garment_labels']} garment labels")
    print(f"inventory: {s['inventory_rows']} rows, {s['units']} units, {s['out_of_stock_rows']} sold-out size rows")
    print(f"users: {s['users']} accounts, {s['messages']} chat messages")
    print(f"Wrote {OUT_PATH.relative_to(APP_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
