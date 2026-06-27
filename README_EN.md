# 🧩 LagerSync Plugin Marketplace

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Gamerhund_lagersync-plugins&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Gamerhund_lagersync-plugins)
[![Plugins](https://img.shields.io/badge/Plugins-4%20Available-blue.svg)](plugins/)

Official plugin marketplace for LagerSync. Extend your inventory management system with verified plugins and community-created extensions – installable directly from the dashboard. | [Deutsche Version](README.md)

---

## 📦 Available Plugins

| Plugin | Description | Type |
|----------|-------------|------|
| [**ki-assistent**](plugins/ki-assistent/) | AI chat with Ollama/OpenAI integration. Can query inventory levels and perform stock changes. | ✅ Verified |
| [**low_stock_notifications**](plugins/low_stock_notifications/) | Notifications via Telegram, Discord, Webhook, or Email. | ✅ Verified |
| [**pro-design**](plugins/pro-design/) | Professional design options and themes for your inventory management system. | ✅ Verified |
| [**sso**](plugins/sso/) | Single sign-on via OpenID Connect with configurable username claim, nonce, logout, and scope, plus improved security. Works with any OIDC provider. | ✅ Verified |

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
| [docs/PLUGINS.md](docs/PLUGINS.md) | Developers – complete human-readable documentation |
| [docs/PLUGINS_KI.md](docs/PLUGINS_KI.md) | AI-assisted development – optimized for AI agents |
| [docs/EXAMPLES.md](docs/EXAMPLES.md) | Four complete example plugins to learn from |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How a plugin technically plugs into the system |
| [docs/SECURITY.md](docs/SECURITY.md) | Security model & how to report vulnerabilities |
| [FAQ.md](FAQ.md) | Frequently asked questions & troubleshooting |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to submit a pull request |

### Tip for AI-Assisted Development

Provide `docs/PLUGINS_KI.md` to an AI assistant such as ChatGPT or Claude and describe what your plugin should do. The AI can generate pull-request-ready code that follows the LagerSync plugin specification and passes automated tests.

---

## 📤 Publish a Plugin

The full process, including branch naming, required checks, and review criteria, is in [CONTRIBUTING.md](CONTRIBUTING.md). Short version:

1. Fork this repository
2. Create a new folder inside `plugins/` for your plugin
3. Add your files (`plugin.json`, optionally `backend.py` and `frontend.js`)
4. Create a Pull Request with a short description
5. After review and successful testing, your plugin will be added to the marketplace

---

## 🤝 Contributing

Contributions are welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before getting started – it covers branch names, required tests, and review criteria. For bug reports, questions, and feature requests, use the GitHub Issues section, or check the [FAQ.md](FAQ.md) for common questions.

---

## 📄 License

This project is licensed under the MIT License.

[MIT](LICENSE) © 2026 Jonas (Gamerhund)
