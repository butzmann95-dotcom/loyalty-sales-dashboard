#!/usr/bin/env python3
# Consolidación inicial (v1) del data.json del dashboard a partir de los
# resultados ya descargados de HubSpot y Apollo en esta sesión.
# El refresh diario lo hace el agente siguiendo AGENT.md (no este script).
import json, sys, os
from collections import defaultdict

TR = os.path.expanduser("~/.claude/projects/-Users-manuellizcanobutzmann/81c417bb-48a2-494f-979a-29b0b079145d/tool-results")
OUT = os.path.expanduser("~/Documents/loyalty-sales-dashboard/data/data.json")

STAGE_LABELS = {
    "qualifiedtobuy": "Quote requested",
    "48891008": "Waiting for feedback",
    "presentationscheduled": "Meeting scheduled",
    "decisionmakerboughtin": "Negotiating rates",
    "contractsent": "Onboarding",
    "45093906": "Waiting for first load",
    "closedwon": "Closed won",
    "closedlost": "Closed lost",
    "110553127": "Appointment scheduled (AM)",
    "110553128": "New lane quote (AM)",
    "110553129": "Waiting for feedback (AM)",
    "110553130": "Negotiating rates (AM)",
    "110553131": "Waiting for first load (AM)",
    "110553132": "Closed won (AM)",
    "110553133": "Closed lost (AM)",
}
STAGE_ORDER = ["qualifiedtobuy", "presentationscheduled", "48891008", "decisionmakerboughtin",
               "contractsent", "45093906", "110553127", "110553128", "110553129", "110553130", "110553131"]
CLOSED = {"closedwon", "closedlost", "110553132", "110553133"}

OWNERS = {
    "83730145": "Erik Dominguez", "89752064": "Zaid Rangel", "91885937": "Hugo Rubio",
    "294202410": "Luis Carlos Ramos", "300514391": "Manuel Lizcano", "437743508": "Rick Aquino",
    "732691591": "Julian Vargas", "80111865": "Areli Mendoza", "81468524": "Israel Sanchez",
    "89704392": "Maria Jose Cardenas", "294203800": "David Romero", "294203970": "Isaac Canales",
    "310772050": "Jaime Garza", "316309538": "Ingrid Jimenez", "85540578": "Valeria Moreno",
    "87416202": "Martin Guzman", "87450965": "Wasim Fernandez", "92598917": "Nicolas Espinosa",
    "258809638": "Carlos Robayo", "279894621": "Sean Laidacker", "288737959": "Diana Ramos",
}

# --- Deals abiertos (filtrados por stage NOT IN closed) ---
deals_raw = json.load(open(f"{TR}/mcp-102c2e85-31b9-4e34-81ea-88bd9d7c3b0e-search_crm_objects-1781124610195.txt"))
open_total = deals_raw.get("total")
open_deals = []
for r in deals_raw["results"]:
    p = r["properties"]
    if p.get("dealstage") in CLOSED:
        continue
    open_deals.append({
        "id": r["id"],
        "name": p.get("dealname", ""),
        "stage": p.get("dealstage", ""),
        "stage_label": STAGE_LABELS.get(p.get("dealstage", ""), p.get("dealstage", "")),
        "amount": float(p.get("amount") or 0),
        "owner": OWNERS.get(p.get("hubspot_owner_id", ""), "—"),
        "close_date": (p.get("closedate") or "")[:10],
        "last_modified": (p.get("hs_lastmodifieddate") or "")[:10],
        "url": f"https://app.hubspot.com/contacts/23318586/record/0-3/{r['id']}",
    })

stages = defaultdict(lambda: {"count": 0, "value": 0.0})
for d in open_deals:
    stages[d["stage"]]["count"] += 1
    stages[d["stage"]]["value"] += d["amount"]
stage_rows = [{"id": s, "label": STAGE_LABELS.get(s, s), **stages[s]} for s in STAGE_ORDER if s in stages]

top_deals = sorted(open_deals, key=lambda d: -d["amount"])[:15]
recent_deals = sorted(open_deals, key=lambda d: d["last_modified"], reverse=True)[:10]

# --- Campañas Apollo (páginas 1-3 desde archivos, página 4 embebida: todas inactivas) ---
camp_files = [
    f"{TR}/mcp-105a6a82-0f04-43cf-90bf-8a259b43bfc6-apollo_emailer_campaigns_search-1781124447066.txt",
    f"{TR}/mcp-105a6a82-0f04-43cf-90bf-8a259b43bfc6-apollo_emailer_campaigns_search-1781124536337.txt",
    f"{TR}/mcp-105a6a82-0f04-43cf-90bf-8a259b43bfc6-apollo_emailer_campaigns_search-1781124538323.txt",
]
PAGE4 = [
    {"name": "Rick_Furniture/HomeDeco_US_East", "active": False, "unique_delivered": 323, "unique_opened": 78, "unique_replied": 0, "unique_clicked": 16, "unique_bounced": 58},
    {"name": "NEW Sequence US CAN// General", "active": False, "unique_delivered": 117, "unique_opened": 15, "unique_replied": 0, "unique_clicked": 0, "unique_bounced": 8},
    {"name": "Campaign US Automotive ENG", "active": False, "unique_delivered": 328, "unique_opened": 91, "unique_replied": 6, "unique_clicked": 20, "unique_bounced": 23},
    {"name": "Prospecting Mexico", "active": False, "unique_delivered": 734, "unique_opened": 164, "unique_replied": 15, "unique_clicked": 37, "unique_bounced": 91},
    {"name": "Prospecting USA/CAN", "active": False, "unique_delivered": 1918, "unique_opened": 513, "unique_replied": 23, "unique_clicked": 225, "unique_bounced": 145},
]
campaigns = []
for f in camp_files:
    raw = open(f).read()
    data = json.loads(raw[raw.find("{"):])
    campaigns += data.get("emailer_campaigns", [])
campaigns += PAGE4

def num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0

def crow(c):
    d = num(c.get("unique_delivered"))
    o = num(c.get("unique_opened"))
    rep = num(c.get("unique_replied"))
    return {
        "name": (c.get("name") or "").strip(),
        "active": bool(c.get("active")),
        "delivered": d, "opened": o, "replied": rep,
        "clicked": num(c.get("unique_clicked")), "bounced": num(c.get("unique_bounced")),
        "open_rate": round(o / d * 100, 1) if d else 0.0,
        "reply_rate": round(rep / d * 100, 1) if d else 0.0,
    }

camp_rows = [crow(c) for c in campaigns]
active = [c for c in camp_rows if c["active"]]
active_with_volume = [c for c in active if c["delivered"] > 0]
tot_del = sum(c["delivered"] for c in camp_rows)
tot_rep = sum(c["replied"] for c in camp_rows)
tot_open = sum(c["opened"] for c in camp_rows)

data = {
    "generated_at": "2026-06-10T15:30:00-06:00",
    "kpis": {
        "calls_today": 51, "calls_7d": 536,
        "emails_today": 104, "emails_7d": 891,
        "open_deals_count": open_total, "open_deals_sample": len(open_deals),
        "open_deals_value": round(sum(d["amount"] for d in open_deals)),
        "apollo_active_campaigns": len(active),
        "apollo_delivered_total": tot_del, "apollo_replied_total": tot_rep,
        "apollo_open_rate": round(tot_open / tot_del * 100, 1) if tot_del else 0,
        "apollo_reply_rate": round(tot_rep / tot_del * 100, 1) if tot_del else 0,
    },
    "pipeline": {"stages": stage_rows, "top_deals": top_deals, "recent_deals": recent_deals},
    "watchlist": [
        {"name": "Daikin Applied", "deals": 1, "stage": "Opportunity", "note": "Sin deal abierto — reactivar contacto",
         "url": "https://app.hubspot.com/contacts/23318586/record/0-2/12129198265"},
        {"name": "HEB", "deals": 3, "stage": "Opportunity", "note": "3 deals históricos — sin deal abierto",
         "url": "https://app.hubspot.com/contacts/23318586/record/0-2/10465750870"},
        {"name": "Vesuvius México", "deals": 2, "stage": "Opportunity", "note": "Sin deal abierto — reactivar contacto",
         "url": "https://app.hubspot.com/contacts/23318586/record/0-2/15247298740"},
    ],
    "apollo_campaigns": sorted(active_with_volume, key=lambda c: -c["delivered"]),
    "history": [
        {"date": "2026-06-10", "calls_7d": 536, "emails_7d": 891,
         "open_deals_value": round(sum(d["amount"] for d in open_deals)), "apollo_replied_total": tot_rep}
    ],
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
print("open deals total(HubSpot):", open_total, "| en muestra:", len(open_deals))
print("pipeline value (muestra): $", data["kpis"]["open_deals_value"])
print("campañas activas:", len(active), "| con volumen:", len(active_with_volume))
print("stages:", [(s['label'], s['count']) for s in stage_rows])
print("OK ->", OUT)
