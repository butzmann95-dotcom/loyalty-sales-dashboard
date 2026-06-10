# AGENT.md — Refresh diario del Loyalty Sales Dashboard

Este documento es la fuente de verdad para el agente que refresca el dashboard.
Repo: `butzmann95-dotcom/loyalty-sales-dashboard` · Carpeta local: `~/Documents/loyalty-sales-dashboard`
Publicación: GitHub Pages sirve `docs/` (el repo es PÚBLICO — **nunca** commitear `data/data.json` ni `.env`; solo se publica `docs/data.enc.json` cifrado).

## Flujo del refresh (cada mañana ~7:30 AM)

### 1. Jalar datos vía conectores MCP

**HubSpot** (`search_crm_objects`):
- `calls` con `hs_timestamp GTE <hoy>` → `kpis.calls_today` (usar el campo `total`)
- `calls` con `hs_timestamp GTE <hoy - 7 días>` → `kpis.calls_7d`
- `emails` con `hs_timestamp GTE <hoy>` → `kpis.emails_today`
- `emails` con `hs_timestamp GTE <hoy - 7 días>` → `kpis.emails_7d`
- `deals` con `dealstage NOT_IN [closedwon, closedlost, 110553132, 110553133]`,
  properties: `dealname, dealstage, pipeline, amount, closedate, hubspot_owner_id, hs_lastmodifieddate`,
  limit 200, sort `hs_lastmodifieddate DESC`. El `total` → `kpis.open_deals_count`.
  - NOTA: NO usar `hs_is_closed` como filtro — está mal poblado en este portal (regresa closedwon).
- Companies del watchlist (IDs fijos abajo): refrescar `num_associated_deals` y `hs_lastmodifieddate`.

**Apollo** (`apollo_emailer_campaigns_search`, 4 páginas de 25):
- Quedarse con campañas `active: true` y `unique_delivered > 0`.
- Campos numéricos pueden venir como "loading" → tratarlos como 0.

### 2. Reconstruir `data/data.json`

Mantener el MISMO esquema que el archivo actual (leerlo primero). Reglas:
- Mapeos de stages y owners: ver tablas abajo.
- `pipeline.stages`: agregación count/value de los deals abiertos por stage (orden de STAGE_ORDER).
- `pipeline.top_deals`: top 15 por monto. `pipeline.recent_deals`: top 10 por `hs_lastmodifieddate`.
- `watchlist`: conservar los existentes; si una company del watchlist tiene deal abierto nuevo, actualizar la nota.
- `history`: APPEND un snapshot del día `{date, calls_7d, emails_7d, open_deals_value, apollo_replied_total}`.
  Conservar máximo 60 entradas (recortar las más viejas). No duplicar si ya existe la fecha de hoy.
- `generated_at`: timestamp actual con zona -06:00.

### 3. Cifrar y publicar

```bash
cd ~/Documents/loyalty-sales-dashboard
source .env   # define DASH_KEY (la clave de cifrado; NUNCA imprimirla ni commitearla)
node scripts/encrypt.mjs "$DASH_KEY"
git add docs/data.enc.json
git commit -m "refresh: $(date +%Y-%m-%d)"
git push
```

### 4. Verificación
- `git push` exitoso y `docs/data.enc.json` cambió.
- Opcional: `curl -s https://butzmann95-dotcom.github.io/loyalty-sales-dashboard/data.enc.json | head -c 100` debe regresar JSON con `"v":1`.

## Tablas de referencia

### Stages (deals)
| ID | Label | Pipeline |
|---|---|---|
| qualifiedtobuy | Quote requested | Sales |
| presentationscheduled | Meeting scheduled | Sales |
| 48891008 | Waiting for feedback | Sales |
| decisionmakerboughtin | Negotiating rates | Sales |
| contractsent | Onboarding | Sales |
| 45093906 | Waiting for first load | Sales |
| closedwon / closedlost | Closed | Sales |
| 110553127 | Appointment scheduled (AM) | Account Mgmt |
| 110553128 | New lane quote (AM) | Account Mgmt |
| 110553129 | Waiting for feedback (AM) | Account Mgmt |
| 110553130 | Negotiating rates (AM) | Account Mgmt |
| 110553131 | Waiting for first load (AM) | Account Mgmt |
| 110553132 / 110553133 | Closed (AM) | Account Mgmt |

STAGE_ORDER: qualifiedtobuy, presentationscheduled, 48891008, decisionmakerboughtin, contractsent, 45093906, 110553127, 110553128, 110553129, 110553130, 110553131

### Owners principales
83730145 Erik Dominguez · 89752064 Zaid Rangel · 91885937 Hugo Rubio · 294202410 Luis Carlos Ramos · 300514391 Manuel Lizcano · 437743508 Rick Aquino · 732691591 Julian Vargas · 81468524 Israel Sanchez · 80111865 Areli Mendoza · 310772050 Jaime Garza

### Watchlist (company IDs en HubSpot, portal 23318586)
- Daikin Applied → 12129198265
- HEB → 10465750870
- Vesuvius México → 15247298740

URL de company: `https://app.hubspot.com/contacts/23318586/record/0-2/{id}`
URL de deal: `https://app.hubspot.com/contacts/23318586/record/0-3/{id}`
