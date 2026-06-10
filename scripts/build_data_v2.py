#!/usr/bin/env python3
# v2: dashboard PERSONAL de Manuel (owner HubSpot 300514391, Apollo user 696929f8ba1034001d66dcf5).
# Consolida datos ya descargados en esta sesión. El refresh diario lo hace el agente vía AGENT.md.
import json, os
from collections import defaultdict

TR = os.path.expanduser("~/.claude/projects/-Users-manuellizcanobutzmann/81c417bb-48a2-494f-979a-29b0b079145d/tool-results")
OUT = os.path.expanduser("~/Documents/loyalty-sales-dashboard/data/data.json")
APOLLO_USER = "696929f8ba1034001d66dcf5"

STAGE_LABELS = {
    "qualifiedtobuy": "Quote requested", "48891008": "Waiting for feedback",
    "presentationscheduled": "Meeting scheduled", "decisionmakerboughtin": "Negotiating rates",
    "contractsent": "Onboarding", "45093906": "Waiting for first load",
    "110553127": "Appointment scheduled (AM)", "110553128": "New lane quote (AM)",
    "110553129": "Waiting for feedback (AM)", "110553130": "Negotiating rates (AM)",
    "110553131": "Waiting for first load (AM)",
}
STAGE_ORDER = ["qualifiedtobuy", "presentationscheduled", "48891008", "decisionmakerboughtin",
               "contractsent", "45093906", "110553127", "110553128", "110553129", "110553130", "110553131"]

# Deals abiertos de Manuel (query de hoy, owner 300514391, total=9)
DEALS = [
    {"id": 59680309169, "name": "Vesuvius - MX/US", "stage": "presentationscheduled", "amount": 0, "close": "2026-06-30", "mod": "2026-06-10"},
    {"id": 60785726534, "name": "Metalsa - Spots", "stage": "contractsent", "amount": 100, "close": "2026-06-30", "mod": "2026-06-09"},
    {"id": 54078616390, "name": "KCC - Nacional", "stage": "contractsent", "amount": 100, "close": "2026-03-31", "mod": "2026-06-08"},
    {"id": 57865592921, "name": "Milwaukee Meeting", "stage": "presentationscheduled", "amount": 0, "close": "2026-04-30", "mod": "2026-06-08"},
    {"id": 57539103303, "name": "HEB", "stage": "qualifiedtobuy", "amount": 0, "close": "2026-04-15", "mod": "2026-06-08"},
    {"id": 35539706403, "name": "Daikin - SLP & US", "stage": "contractsent", "amount": 1, "close": "2026-03-31", "mod": "2026-06-01"},
    {"id": 56175391821, "name": "CB & Nationals - Milwaukee T.", "stage": "presentationscheduled", "amount": 0, "close": "2026-04-30", "mod": "2026-06-01"},
    {"id": 59369945360, "name": "Covia - IL - SLP", "stage": "contractsent", "amount": 100, "close": "2026-04-30", "mod": "2026-06-01"},
    {"id": 46786369576, "name": "Grupo AlEn - Participación Licitación EXPO", "stage": "presentationscheduled", "amount": 10000, "close": "2026-06-30", "mod": "2026-05-31"},
]
open_deals = [{
    "id": d["id"], "name": d["name"], "stage": d["stage"],
    "stage_label": STAGE_LABELS.get(d["stage"], d["stage"]),
    "amount": float(d["amount"]), "owner": "Manuel Lizcano",
    "close_date": d["close"], "last_modified": d["mod"],
    "url": f"https://app.hubspot.com/contacts/23318586/record/0-3/{d['id']}",
} for d in DEALS]

stages = defaultdict(lambda: {"count": 0, "value": 0.0})
for d in open_deals:
    stages[d["stage"]]["count"] += 1
    stages[d["stage"]]["value"] += d["amount"]
stage_rows = [{"id": s, "label": STAGE_LABELS.get(s, s), **stages[s]} for s in STAGE_ORDER if s in stages]

# Campañas Apollo SOLO de Manuel (filtrado por user_id en páginas 1-3; página 4 es de otros usuarios)
camp_files = [
    f"{TR}/mcp-105a6a82-0f04-43cf-90bf-8a259b43bfc6-apollo_emailer_campaigns_search-1781124447066.txt",
    f"{TR}/mcp-105a6a82-0f04-43cf-90bf-8a259b43bfc6-apollo_emailer_campaigns_search-1781124536337.txt",
    f"{TR}/mcp-105a6a82-0f04-43cf-90bf-8a259b43bfc6-apollo_emailer_campaigns_search-1781124538323.txt",
]
def num(v):
    try: return int(v)
    except (TypeError, ValueError): return 0

mine = []
for f in camp_files:
    raw = open(f).read()
    data = json.loads(raw[raw.find("{"):])
    for c in data.get("emailer_campaigns", []):
        if c.get("user_id") == APOLLO_USER:
            d_, o_, r_ = num(c.get("unique_delivered")), num(c.get("unique_opened")), num(c.get("unique_replied"))
            mine.append({
                "name": (c.get("name") or "").strip(), "active": bool(c.get("active")),
                "delivered": d_, "opened": o_, "replied": r_,
                "clicked": num(c.get("unique_clicked")), "bounced": num(c.get("unique_bounced")),
                "open_rate": round(o_ / d_ * 100, 1) if d_ else 0.0,
                "reply_rate": round(r_ / d_ * 100, 1) if d_ else 0.0,
            })

active = [c for c in mine if c["active"]]
tot_del = sum(c["delivered"] for c in mine)
tot_rep = sum(c["replied"] for c in mine)
tot_open = sum(c["opened"] for c in mine)
print("Campañas de Manuel:", [(c["name"], c["active"], c["delivered"]) for c in mine])

pipeline_value = round(sum(d["amount"] for d in open_deals))
data = {
    "generated_at": "2026-06-10T15:55:00-06:00",
    "scope": "Solo actividad de Manuel (manuel@whyloyalty.com)",
    "kpis": {
        "calls_today": 0, "calls_7d": 0,
        "emails_today": 13, "emails_7d": 128,
        "open_deals_count": len(open_deals), "open_deals_sample": len(open_deals),
        "open_deals_value": pipeline_value,
        "apollo_active_campaigns": len(active),
        "apollo_delivered_total": tot_del, "apollo_replied_total": tot_rep,
        "apollo_open_rate": round(tot_open / tot_del * 100, 1) if tot_del else 0,
        "apollo_reply_rate": round(tot_rep / tot_del * 100, 1) if tot_del else 0,
    },
    "pipeline": {
        "stages": stage_rows,
        "top_deals": sorted(open_deals, key=lambda d: -d["amount"]),
        "recent_deals": sorted(open_deals, key=lambda d: d["last_modified"], reverse=True),
    },
    "watchlist": [
        {"name": "Daikin - SLP & US", "deals": 1, "stage": "Onboarding", "note": "Deal abierto en Onboarding — empujar primer load",
         "url": "https://app.hubspot.com/contacts/23318586/record/0-3/35539706403"},
        {"name": "HEB", "deals": 1, "stage": "Quote requested", "note": "Cotización pendiente — cierre objetivo ya venció (15 abr), actualizar",
         "url": "https://app.hubspot.com/contacts/23318586/record/0-3/57539103303"},
        {"name": "Vesuvius - MX/US", "deals": 1, "stage": "Meeting scheduled", "note": "Reunión agendada — confirmar y preparar",
         "url": "https://app.hubspot.com/contacts/23318586/record/0-3/59680309169"},
        {"name": "Grupo AlEn ($10K)", "deals": 1, "stage": "Meeting scheduled", "note": "Licitación EXPO — el deal de mayor monto",
         "url": "https://app.hubspot.com/contacts/23318586/record/0-3/46786369576"},
    ],
    "apollo_campaigns": sorted([c for c in active], key=lambda c: -c["delivered"]),
    "history": [
        {"date": "2026-06-10", "calls_7d": 0, "emails_7d": 128,
         "open_deals_value": pipeline_value, "apollo_replied_total": tot_rep}
    ],
}
json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
print("OK ->", OUT, "| deals:", len(open_deals), "| valor: $", pipeline_value,
      "| campañas activas mías:", len(active))
