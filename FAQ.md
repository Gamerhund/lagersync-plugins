# ❓ FAQ

Fragen, die garantiert nochmal aufkommen. Wenn deine nicht dabei ist: [Issue aufmachen](https://github.com/Gamerhund/lagersync-plugins/issues), und sie landet beim nächsten Mal hier.

### Mein Plugin taucht nicht im Marketplace auf

Drei Klassiker, in der Reihenfolge, in der ich sie selbst am häufigsten verbockt habe:

- Der PR ist noch nicht gemerged. Klingt offensichtlich, aber genau das ist meistens es.
- Der Plugin-Ordner liegt nicht direkt unter `plugins/`. Wer schon mal versehentlich `plugin.json` ins Repo-Root gelegt hat (ja, ist hier schon passiert, [#10](https://github.com/Gamerhund/lagersync-plugins/pull/10)), weiß: das wird einfach nicht geladen.
- `"enabled": false` – dann ist es zwar installiert, aber inaktiv bis du es manuell anschaltest. Das ist Absicht, kein Bug, siehe [PLUGINS.md](docs/PLUGINS.md#pluginjson--pflichtdatei).

### Der PR ist rot, was jetzt

Der Bot kommentiert deinen PR mit einer Aufschlüsselung nach Kategorie – da steht meistens schon, woran's hängt:

- **Struktur** – meist ein fehlendes Feld in `plugin.json` oder die Version ist nicht `X.Y.Z`
- **Verified** – du hast `"verified": true` gesetzt. Das ist mein Job, nicht deiner, lass es auf `false`
- **Permissions** – eine Permission, die es nicht gibt, oder `permissions` ist kein Array
- **Dateien** – `backend.py` hat einen Syntaxfehler oder `frontend.js` ist leer
- **Code-Scanner** – irgendwo steckt `eval()`, `subprocess`, `os.system()` o.ä. drin, siehe [SECURITY.md](docs/SECURITY.md)

CodeQL und SonarCloud laufen daneben unabhängig vom pytest-Lauf – wenn die meckern, steht's im jeweiligen Check, nicht im Bot-Kommentar.

### Warum darf ich `verified` nicht selbst auf `true` setzen

Weil das Feld heißt "ich, Jonas, hab mir den Code persönlich angeschaut" – nicht "die Tests sind grün". Wenn dein frisches Plugin mit `true` ankommt, soll der Test absichtlich rot werden. Lass es auf `false`, ich kümmere mich um den Rest nach Review.

### `frontend.js` macht nichts

Browser-Konsole aufmachen, da steht's meistens. Ein paar Dinge, die gerne übersehen werden:

- `pluginId` und `PluginAPI` gibt's nur im Browser zur Laufzeit. Ein lokales `node frontend.js` wirft deshalb `PluginAPI is not defined` – das ist normal, keine Sorge.
- Leere `frontend.js` lässt der Test nicht durch.

### Welche Permissions gibt's überhaupt

Steht in [PLUGINS.md](docs/PLUGINS.md#-plugin-sicherheit), und `test_plugin_permissions.py` prüft exakt gegen diese Liste. Generell: je weniger du anforderst, desto schneller schau ich mir den PR an.

### Wie teste ich lokal, bevor ich den PR aufmache

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Der JS-Syntax-Check braucht Node lokal installiert – ist keins da, wird er übersprungen statt zu scheitern, genau wie in CI.

### PLUGINS.md vs. PLUGINS_KI.md – was ist der Unterschied

`PLUGINS.md` ist für Menschen, ausführlich. `PLUGINS_KI.md` ist die verdichtete Checkliste für KI-Agenten, die direkt Code schreiben sollen. Wenn die beiden sich widersprechen, gilt `PLUGINS.md` – die KI-Version wird daraus abgeleitet und kann mal hinterherhinken.

### Die README zeigt plötzlich andere Texte, obwohl ich sie nicht angefasst habe

Das war kein Versehen von dir. `update_readme.py` baut die Plugin-Tabelle und den "X verfügbar"-Badge automatisch aus den `plugin.json`-Dateien zusammen, jedes Mal wenn jemand nach `main` pusht. Per Hand in der Tabelle rumeditieren bringt also nichts – das überschreibt der Bot beim nächsten Lauf wieder. Beschreibung ändern willst du in der jeweiligen `plugin.json` (`description` für Deutsch, optional `description_en` für Englisch). **WICHTIG:** Bei bereits signierten Plugins darf `plugin.json` nicht mehr geändert werden, da dies die Signatur ungültig macht.

### Ich brauch Netzwerkzugriff, z.B. für einen Webhook

Nicht über `socket` direkt – das blockiert der Scanner. Permission `system.network` anfordern und `PluginAPI.fetch()` nutzen, oder im Backend mit `requests`. `low_stock_notifications` macht genau das für Telegram/Discord, schau dir das als Vorlage an.

### Ich will ein schon veröffentlichtes Plugin updaten

Neuer PR, Version in `plugin.json` hochzählen (SemVer, siehe [PLUGINS.md](docs/PLUGINS.md#-versionierung--migration)), Code ändern, fertig. Bei DB-Schema-Änderungen vorher kurz die Migrations-Hinweise dort lesen.

### Mein Plugin braucht eine Library, die nicht in `requirements.txt` steht

`requirements.txt` hier im Repo ist nur für die Tests selbst (pytest & co.), nicht für deinen Plugin-Code. Was dein Plugin zur Laufzeit darf, entscheidet die LagerSync-Hauptanwendung, nicht dieses Repo. Im Zweifel: Issue aufmachen und fragen.
