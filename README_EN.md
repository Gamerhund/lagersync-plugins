# 🧩 LagerSync Plugin Marketplace

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Gamerhund_lagersync-plugins&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Gamerhund_lagersync-plugins)
[![Plugins](https://img.shields.io/badge/Plugins-5%20Available-blue.svg)](plugins/)

Official plugin marketplace for LagerSync. Extend your inventory management system with verified plugins and community-created extensions – installable directly from the dashboard. | [Deutsche Version](README.md)

---

## 📦 Available Plugins

| Plugin | Description | Type |
|----------|-------------|------|
| [**ki-assistent**](plugins/ki-assistent/) | AI chat with Ollama/OpenAI integration. Can query inventory levels and perform stock changes. | ✅ Verified |
| [**low_stock_notifications**](plugins/low_stock_notifications/) | Notifications via Telegram, Discord, Webhook, or Email. | ✅ Verified |
| [**price_updater**](plugins/price_updater/) | Automatically updates EK prices based on configured URLs. Supports web scraping for various retailers. | 👤 Community |
| [**pro-design**](plugins/pro-design/) | Professional design options and themes for your inventory management system. | ✅ Verified |
| [**sso**](plugins/sso/) | Single sign-on via OpenID Connect with configurable username claim, nonce, logout, and scope, plus improved security. Works with any OIDC provider. | ✅ Verified |

---

## 🚀 Installation

1. Open your LagerSync dashboard
2. Click **🧩 Marketplace** in the top navigation
3. Find a plugin and click **"⬇ Install"**
4. After installation: Settings → Plugins → activate the plugin → "Reload plugins" → reload the page (Ctrl+R)

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
| [PLUGINS.md](docs/PLUGINS.md) | Developers – complete human-readable documentation |
| [PLUGINS_KI.md](docs/PLUGINS_KI.md) | AI-assisted development – optimized for AI agents |
| [EXAMPLES.md](docs/EXAMPLES.md) | Four complete example plugins to learn from |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | How a plugin technically plugs into the system |
| [SECURITY.md](docs/SECURITY.md) | Security model & how to report vulnerabilities |
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
   - `plugin.json` must include the required fields `name`, `version`, `author`, `description`, `verified`, `enabled`, and `permissions`.
   - For new plugins: `verified: false`; `enabled: false` is recommended.
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

---

## ☕ Support the project

If this plugin marketplace or LagerSync is useful to you, your support helps me develop new features, fix bugs, and maintain the project long-term.

- ☕ Ko-fi: [https://ko-fi.com/gamerhund](https://ko-fi.com/gamerhund)
- ₿ Bitcoin: `bc1qha4h4vvykgcvzdgc5auueqhq0lf4glstrs0cy`

Thank you for your support! 💚
