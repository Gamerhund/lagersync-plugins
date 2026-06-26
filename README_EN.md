# 🧩 LagerSync Plugin Marketplace

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Gamerhund_lagersync-plugins&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Gamerhund_lagersync-plugins)
[![Plugins](https://img.shields.io/badge/Plugins-4%20Available-blue.svg)](plugins/)

Official plugin marketplace for LagerSync. Extend your inventory management system with verified plugins and community-created extensions – installable directly from the dashboard. | [Deutsche Version](README.md)

---

## 📦 Available Plugins

| Plugin | Description | Type |
|----------|-------------|------|
| [**ki-assistent**](plugins/ki-assistent/) | KI-Chat mit Ollama/OpenAI-Integration. Kann Lagerbestände abfragen und Bestandsänderungen vornehmen. | ✅ Verified |
| [**low_stock_notifications**](plugins/low_stock_notifications/) | Benachrichtigungen per Telegram, Discord, Webhook oder E-Mail. | ✅ Verified |
| [**pro-design**](plugins/pro-design/) | Professionelle Design-Optionen und Themes für deine Lagerverwaltung. | ✅ Verified |
| [**sso**](plugins/sso/) | Single Sign-On per OpenID Connect mit konfigurierbarem Username-Claim, Nonce, Logout, Scope und verbesserter Sicherheit. Funktioniert mit jedem OIDC-Provider. | ✅ Verified |

---

## 🚀 Installation

1. Open your LagerSync dashboard
2. Navigate to **Settings → 🧩 Plugins**
3. Click **Install Plugin**
4. Select a plugin from the list
5. Click **Install**

---

## 🛠️ Develop Your Own Plugins

Anyone can create plugins – all you need is basic Python or JavaScript knowledge.

### Plugin Structure

```text
plugins/
└── my-plugin/
    ├── plugin.json     ← Required file (name, permissions, metadata, ...)
    ├── plugin.sig      ← Required only for verified plugins
    ├── backend.py      ← Optional: Flask API routes
    └── frontend.js     ← Optional: Browser UI
```

### Documentation

| Documentation | Audience |
|---------------|----------|
| [PLUGINS.md](PLUGINS.md) | Developers – complete human-readable documentation |
| [PLUGINS_KI.md](PLUGINS_KI.md) | AI-assisted development – optimized for AI agents |

### Tip for AI-Assisted Development

Provide `PLUGINS_KI.md` to an AI assistant such as ChatGPT or Claude and describe what your plugin should do. The AI can generate pull-request-ready code that follows the LagerSync plugin specification and passes automated tests.

---

## 📤 Publish a Plugin

1. Fork this repository
2. Create a new folder inside `plugins/` for your plugin
3. Add your files (`plugin.json`, optionally `backend.py` and `frontend.js`)
4. Create a Pull Request with a short description
5. After review and successful testing, your plugin will be added to the marketplace

---

## 🤝 Contributing

Contributions are welcome.

Please read [PLUGINS.md](PLUGINS.md) before getting started. For bug reports, questions, and feature requests, use the GitHub Issues section.

---

## 📄 License

This project is licensed under the MIT License.

[MIT](LICENSE) © 2026 Jonas (Gamerhund)
