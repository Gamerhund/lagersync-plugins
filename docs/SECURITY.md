# 🔒 Security

Dieses Dokument beschreibt das Sicherheitsmodell des LagerSync Plugin-Marketplace und wie du eine Schwachstelle meldest.

---

## Schwachstelle melden

**Bitte keine öffentlichen GitHub Issues für Sicherheitslücken.**

Nutze stattdessen [GitHub Security Advisories](https://github.com/Gamerhund/lagersync-plugins/security/advisories/new) für dieses Repository (Tab **Security → Report a vulnerability**). Das meldet die Lücke privat an den Maintainer, bevor sie öffentlich sichtbar wird.

Bitte gib an:
- Betroffenes Plugin (Ordnername) oder ob es das Marketplace-Repo selbst betrifft
- Schritte zum Reproduzieren
- Mögliche Auswirkung (z.B. Cross-Tenant-Zugriff, RCE, Datenleck)

Wir bemühen uns, innerhalb einiger Tage zu antworten. Ein Fix-Zeitrahmen hängt von Schweregrad und Komplexität ab.

---

## Geltungsbereich

Dieses Dokument behandelt das **Marketplace-Repository** (`lagersync-plugins`) und die hier veröffentlichten Plugins. Schwachstellen in der LagerSync-Hauptanwendung selbst (Plugin-Loader, `plugin_security.py`, Datenbank-Layer) gehören in das Hauptrepository von LagerSync.

---

## Schutzschichten im Plugin-System

Plugins laufen mit eingeschränkten Rechten innerhalb der Hauptanwendung. Mehrere Schichten sollen verhindern, dass ein fehlerhaftes oder böswilliges Plugin Schaden anrichtet:

### 1. Permissions System

Plugins müssen **explizit** Berechtigungen in `plugin.json` anfordern. Ohne die passende Permission werden API-Aufrufe blockiert. Die vollständige Liste der Permissions steht in [PLUGINS.md](PLUGINS.md#plugin-sicherheit).

**Default-Permissions für neue Plugins:**
```json
["db.read", "inventory.read", "api.public"]
```

Je weniger Permissions ein Plugin anfordert, desto schneller geht die Review – siehe [CONTRIBUTING.md](../CONTRIBUTING.md).

### 2. Code-Scanner (statische Analyse beim Laden)

Beim Laden – und automatisch bei jedem Pull Request über `tests/test_plugin_code_scan.py` – werden `backend.py` und `frontend.js` auf gefährliche Muster gescannt:

| Muster | Schweregrad | Grund |
|---|---|---|
| `os.system()` | hoch | Befehlsausführung |
| `subprocess.*` | hoch | Prozessausführung |
| `eval()` / `exec()` | hoch | Beliebige Code-Ausführung |
| `__import__()` | hoch | Dynamischer Import zur Laufzeit |
| `socket.*` | mittel | Direkter Netzwerkzugriff (nutze `system.network` + `PluginAPI.fetch()`) |
| `pickle` | mittel | Unsichere Deserialisierung (RCE-Risiko) |
| `shutil.rmtree` | mittel | Rekursives Löschen |
| `open('../...')` | mittel | Pfad-Traversal |

High-severity-Muster blockieren das Plugin vollständig. Medium-severity-Muster erzeugen eine Warnung.

### 3. Ed25519-Signaturen

Offiziell verifizierte Plugins werden vom Maintainer kryptografisch signiert (`plugin.sig`, Ed25519). Das bestätigt, dass der ausgelieferte Code tatsächlich vom geprüften Stand stammt und nicht nachträglich verändert wurde.

```bash
# Private Key generieren (einmalig, nur für den Maintainer)
python -c "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; \
import base64; key = Ed25519PrivateKey.generate(); \
print('Private:', base64.b64encode(key.private_bytes_raw()).decode()); \
print('Public:', base64.b64encode(key.public_key().public_bytes_raw()).decode())"
```

Neue Plugins setzen `"verified": false` und liefern (noch) keine `plugin.sig` – das `verified`-Feld und die Signatur werden ausschließlich vom Maintainer nach persönlicher Prüfung gesetzt (durchgesetzt von `tests/test_plugin_verified.py`).

**Wichtig für Doku-Pflege:** Die Signatur wird über den exakten Inhalt von `plugin.json` berechnet. Jede nachträgliche Änderung an `plugin.json` eines bereits verifizierten Plugins (auch nur am `description`-Feld) invalidiert dessen Signatur, bis der Maintainer mit dem privaten Key neu signiert.

### 4. Audit-Logs

Alle Plugin-Aktionen werden protokolliert: Laden/Entladen, API-Aufrufe, Datenbank-Zugriffe, Konfigurationsänderungen.

```
GET /api/plugins/{plugin_id}/audit
```

### 5. Rate Limiting

API-Aufrufe sind pro Permission begrenzt, damit ein fehlerhaftes Plugin nicht die ganze Instanz lahmlegt:

| Aktion | Limit |
|--------|-------|
| Default | 100 / 60s |
| `db.read` | 50 / 60s |
| `db.write` | 20 / 60s |
| `api.public` | 100 / 60s |
| `api.admin` | 30 / 60s |

```
GET /api/plugins/{plugin_id}/rate-limits
```

### 6. Automatisierte Code-Qualität (CI)

Jeder Pull Request läuft zusätzlich durch CodeQL (Python & JavaScript) und SonarCloud Quality Gates, bevor er gemerged werden kann – siehe [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Was diese Schichten **nicht** abdecken

> ⚠️ Der Scanner erkennt bekannte gefährliche *Muster*, keine *Absicht*. Ein Plugin kann z.B. unproblematischen Code enthalten, der trotzdem Daten an einen externen Dienst sendet (mit `system.network`-Permission ganz legitim), oder subtile Logikfehler haben, die kein Scanner erkennt.
>
> **Installiere grundsätzlich nur Plugins, deren Quellcode du gelesen und verstanden hast** – besonders bei noch nicht persönlich verifizierten Plugins (`"verified": false`).

---

## Tenant-Isolation

Bei Multi-Tenant-Setups ist die korrekte Filterung nach `tenant_id` Aufgabe des Plugin-Codes – sie wird nicht automatisch vom System erzwungen. Siehe die Multi-Tenant-Regeln in [PLUGINS.md](PLUGINS.md#-multi-tenant-best-practices) bzw. [PLUGINS_KI.md](PLUGINS_KI.md#-multi-tenant--ki-regeln) für die korrekte Implementierung.
