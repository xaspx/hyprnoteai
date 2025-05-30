
# 💊 MCPill – Pumpfun  MCP Server

**MCPill** is a Model Context Protocol (MCP) server for interacting with the [Pump.fun](https://pump.fun) platform on **Solana**. This server enables **AI assistants** to autonomously **create**, **buy**, and **sell** tokens — unleashing fully automated crypto experiences powered by artificial intelligence.

> MCPill bridges the gap between AI autonomy and onchain memecoin deployment.

---


<p align="center">
  <img src="https://raw.githack.com/xaspx/mcpill/main/scripts/mcpill.PNG" width="250" height="250" alt="MCPill Demo"> <br>
  <a href="https://x.com/mcpilldev" target="_blank"><img src="https://img.shields.io/static/v1?label=Follow%20us%20on&message=X&color=black&logo=x" alt="X"></a><br><br>
  <b>CA: DCXKhzKuxDD91xLcNmTHbTioE4VXtpzq72347Bb3pump</b>
</p>

---

## 🧠 What Can It Do?

The MCPill server acts as a backend bridge that enables language models (like Claude or GPT) to:
- Launch new tokens on Pump.fun
- Purchase and sell tokens
- Query token metadata
- Manage accounts and balances

Think of it as **the Solana engine for AI-driven crypto interactions**.

---

## 🎬 Demo Video

Watch how it works:  

https://github.com/user-attachments/assets/2854a2f1-8ce4-4767-a1c9-fb555d7cce00

---

## 🚀 Usage

To use this server with Claude or another MCP-compatible assistant, add this configuration to your MCP client:

If you're on **MacOS** and using **Claude Desktop**, edit this file:  
`~/Library/Application\ Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pumpfun": {
      "command": "node",
      "args": ["/Users/YOUR_USERNAME/Desktop/mcpill/build/index.js"],
      "env": {
        "HELIUS_RPC_URL": "https://your-helius-rpc-url.com"
      }
    }
  }
}
```

👉 Replace the path and `HELIUS_RPC_URL` with your actual setup details.

---

## ⚙️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/xaspx/mcpill.git
   cd mcpill
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up `.env`**:
   ```env
   HELIUS_RPC_URL=https://your-helius-rpc-url.com
   PRIVATE_KEY=your-base58-encoded-private-key
   ```

4. **Convert your key**:
   ```bash
   node convert-key.js
   ```

5. **Build the server**:
   ```bash
   npm run build
   ```

6. **Run the MCPill server**:
   ```bash
   node build/index.js
   ```

---

## 🔧 Components

### Available Tools

- `get-token-info`: Fetch token metadata
- `create-token`: Mint new token on Pump.fun
- `buy-token`: Buy token with adjustable slippage
- `sell-token`: Sell token by amount or total
- `list-accounts`: List keypairs
- `get-account-balance`: Check balances

Each of these tools is accessible from your AI assistant or CLI.

---

## 👤 Account Management

Keypairs are stored as JSON files in the `.keys/` folder. The server:
- Uses `.env` for loading a default private key
- Saves new mint keypairs as `mint-<symbol>.json`
- Supports multiple named accounts

Ensure your wallet has SOL before launching or trading tokens.

---

## 🛠 Standalone Scripts

You can also run core functionality directly from the terminal:

```bash
node build/get-token-info.js <token_address>
node build/create-token.js <name> <symbol> <description> <initial_buy_amount> [account_name] [image_url]
node build/buy-token.js <token_address> <buy_amount> [account_name] [slippage]
node build/sell-token.js <token_address> <sell_amount> [account_name] [slippage]
node build/list-accounts.js
node build/get-token-balance.js <account_name> [token_address]
```

---

## ⚠️ Notes

- Keypairs are **unencrypted**. Secure `.keys/` if you're in production.
- Pump.fun transactions require SOL — keep wallets funded.
- Slippage default is 1% (100 basis points). Customize as needed.
- Images must be **local paths** when minting new tokens.

---

## 🧱 Project Structure

| File | Purpose |
|------|---------|
| `src/index.ts` | Entry point for the MCPill server |
| `src/create-token.ts` | Token minting logic |
| `src/buy-token.ts` | Buying logic |
| `src/sell-token.ts` | Selling logic |
| `src/get-token-info.ts` | Token metadata |
| `src/get-token-balance.ts` | SOL/token balance lookup |
| `src/list-accounts.ts` | List accounts |
| `src/utils.ts` | Shared utilities |
| `convert-key.js` | Private key to keypair JSON tool |

---

## 📘 License

MIT – Feel free to fork and customize MCPill for your own agent stacks or AI token launch tools.

---

### 🧬 Powered by $MCPILL

This repo is built for agents who take the green pill.  
Let your AI mint the next viral coin.
