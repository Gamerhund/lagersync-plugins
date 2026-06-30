# 🔒 Security

## Eine Lücke gefunden?

Bitte kein öffentliches Issue dafür. Nutz [GitHub Security Advisories](https://github.com/Gamerhund/lagersync-plugins/security/advisories/new) (Tab Security → Report a vulnerability) – das geht erstmal nur an mich, bevor irgendwas öffentlich sichtbar wird.

Hilfreich dabei: welches Plugin (oder ob's das Marketplace-Repo selbst betrifft), wie man's reproduziert, und was im schlimmsten Fall passieren könnte. Ich antworte normalerweise innerhalb ein paar Tage, wie schnell ein Fix kommt hängt vom Schweregrad ab.

Für Lücken in der LagerSync-Hauptanwendung selbst (Plugin-Loader, `plugin_security.py`, DB-Layer) bist du hier falsch – das gehört ins Haupt-Repo, dieses hier ist nur der Plugin-Marketplace.

## Wie das Plugin-System abgesichert ist

Plugins laufen nicht mit vollen Rechten in der Hauptanwendung – mehrere Schichten sollen verhindern, dass ein kaputtes oder böswilliges Plugin Schaden anrichtet.

**Permissions.** Ein Plugin bekommt nur Zugriff auf das, was es in `plugin.json` explizit anfordert – alles andere wird blockiert. Die komplette Liste steht in [PLUGINS.md](PLUGINS.md#-plugin-sicherheit). Neue Plugins starten meist mit etwas wie:
```json
["db.read", "inventory.read", "api.public"]
```
und je weniger davon, desto schneller geht auch die Review.

**Code-Scanner.** Beim Laden – und bei jedem PR über `test_plugin_code_scan.py` – wird `backend.py`/`frontend.js` nach gefährlichen Mustern durchsucht:

| Muster | Stufe | Warum |
|---|---|---|
| `os.system()` | hoch | Befehlsausführung |
| `subprocess.*` | hoch | Prozessausführung |
| `eval()` / `exec()` | hoch | beliebiger Code |
| `__import__()` | hoch | dynamischer Import |
| `socket.*` | mittel | Netzwerk direkt statt über `system.network` + `PluginAPI.fetch()` |
| `pickle` | mittel | unsichere Deserialisierung |
| `shutil.rmtree` | mittel | rekursives Löschen |
| `open('../...')` | mittel | Pfad-Traversal |

Hohe Stufe blockiert das Plugin beim Laden (Runtime-Loader). Mittlere Muster werden vom Produktionsscanner ebenfalls als problematisch eingestuft und sollten vermieden werden; die Tests in diesem Repository prüfen sie aktuell als Fehler.

**Signaturen.** Plugins, die ich persönlich geprüft habe, signiere ich mit Ed25519 (`plugin.sig`). Die Signatur bestätigt die Integrität: exakt diese Dateien wurden seit der Signierung nicht verändert. Das "ich habe es geprüft" ergibt sich daraus, dass ich signiere.

```bash
# Private Key generieren (einmalig, nur ich brauch das)
# WICHTIG: Der private Schlüssel wird niemals veröffentlicht und verbleibt ausschließlich beim Maintainer.
# LagerSync enthält lediglich den öffentlichen Schlüssel zur Signaturprüfung.
python -c "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; \
import base64; key = Ed25519PrivateKey.generate(); \
print('Private:', base64.b64encode(key.private_bytes_raw()).decode()); \
print('Public:', base64.b64encode(key.public_key().public_bytes_raw()).decode())"
```

Ein Detail, das beim Doku-Schreiben gerne übersehen wird: Die Signatur hängt am exakten Inhalt von `plugin.json`. Schon eine Änderung am `description`-Feld eines bereits signierten Plugins macht die Signatur ungültig, bis neu signiert wird – also Vorsicht beim Nachbessern an alten, verifizierten Plugins.

**Audit-Logs.** Laden/Entladen, API-Calls, DB-Zugriffe, Config-Änderungen – wichtige Aktionen werden protokolliert, abrufbar über `GET /api/plugins/{plugin_id}/audit`.

**Rate Limiting**, pro Permission, damit ein einziges kaputtes Plugin nicht die ganze Instanz in die Knie zwingt:

| Aktion | Limit |
|--------|-------|
| Default | 100 / 60s |
| `db.read` | 50 / 60s |
| `db.write` | 20 / 60s |
| `api.public` | 100 / 60s |
| `api.admin` | 30 / 60s |

**CI.** CodeQL (Python + JS) und SonarCloud laufen bei jedem PR mit, siehe [CONTRIBUTING.md](../CONTRIBUTING.md).

## Was davon nicht abgedeckt ist

Der Scanner erkennt Muster, keine Absicht. Ein Plugin kann mit `system.network`-Permission ganz legitim Daten irgendwohin schicken – und auch unauffälligen Code mit einem fiesen Logikfehler erkennt kein Scanner. Heißt im Klartext: Installier nur Plugins, deren Code du tatsächlich gelesen hast, vor allem solange `"verified": false` steht.

## Tenant-Isolation

Die korrekte Filterung nach `tenant_id` ist Aufgabe des Plugin-Codes – das System erzwingt das nicht automatisch. Wie man's richtig macht: [PLUGINS.md](PLUGINS.md#-multi-tenant-best-practices) bzw. [PLUGINS_KI.md](PLUGINS_KI.md#-multi-tenant--ki-regeln).
