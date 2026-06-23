# 🧩 LagerSync Plugin Marketplace

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Gamerhund_lagersync-plugins&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Gamerhund_lagersync-plugins)
[![Plugins](https://img.shields.io/badge/Plugins-3%20Available-blue.svg)](plugins/)
| [Deutsche Version](README.md)
Official plugin marketplace for LagerSync. Extend your inventory management system with verified plugins and community-created extensions – installable directly from the dashboard.

---

## 📦 Available Plugins

| Plugin | Description | Type |
|----------|-------------|------|
| [**ki-assistent**](plugins/ki-assistent/) | AI assistant with Ollama and OpenAI integration. Can query inventory levels and perform stock changes. | ✅ Verified |
| [**low_stock_notifications**](plugins/low_stock_notifications/) | Receive notifications via Telegram, Discord, Webhook, or Email when stock levels fall below the configured minimum quantity. | ✅ Verified |
| [**pro-design**](plugins/pro-design/) | Professional themes and advanced design customization options for your inventory management system. | ✅ Verified |

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
| [PLUGINS_KI.md](PLUGINS_KI.md) | AI-assisted development ("Vibe Coding") – optimized for AI agents |

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