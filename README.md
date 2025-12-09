# The Backroom Parlor

**Project Identity:** "The Backroom Parlor" is a high-fidelity, automated Discord Battle Bot designed to gamify NFT communities. It transforms static digital assets (NFTs) into active combatants in a spectator sport, complete with an integrated economy, betting system, and generative AI storytelling.

## 1. What It Is (The Concept)
Imagine a digital "Fight Club" hosted entirely within a Discord server. Users don't just hold their NFTs; they enter them into tournaments where they battle for supremacy. Other community members gather to watch the chaos, placing bets with real (or simulated) crypto tokens on who will survive.
It is not just a text game; it is a multimedia experience. Every match is narrated by an AI commentator and visualized by an AI artist in real-time, ensuring no two battles are ever the same.

## 2. What It Does (Key Features)
* **🏆 Automated Tournaments:** The system manages full single-elimination brackets (8, 16, or 32 players). It handles seeding, match progression, and elimination automatically.
* **🎲 The Betting Floor:** A fully functional betting engine allows spectators to wager tokens on specific fighters. It calculates odds, tracks pools, and distributes payouts to winners automatically after every match.
* **🤖 AI-Driven Narrative:** 
    * **Primary:** **NVIDIA Narrator (Llama 3.1 405B)**. We switched from Gemini due to aggressive rate limiting and stability issues. Llama 3.1 provides robust, creative, and uncensored storytelling.
    * **Fallback:** A local template-based narrator ensures the show goes on even if the API fails.
* **🎨 Generative Visuals:** 
    * **Primary:** **Supermachine (Flux/NextGen)**. Chosen for its ability to generate high-quality, "edgy," and uncensored art that fits the underground battle theme.
    * **Fallback:** **Pollinations.ai**. Used when Supermachine times out or hits rate limits.
    * **Note:** NVIDIA Image Gen is deprecated for battle scenes due to strict safety filters that blocked combat imagery.
* **💰 Token Economy:** Integrated with the Solana blockchain, it can verify NFT ownership for entry and handle SPL token transactions for betting payouts.

## 3. How It Works (The Architecture)
The project is built on a robust Python backend that orchestrates three distinct layers:

### Layer 1: The Core Engine (Python & SQLite)
* **Brain:** Built with `discord.py`, this listens for commands and manages the game state.
* **Memory:** A SQLite database (managed via SQLAlchemy) tracks every user, wallet, tournament, match, bet, and transaction.
* **Logic:** The "Fairness Engine" calculates win probabilities based on NFT metadata (Rarity/Rank) and RNG.

### Layer 2: The Creative Suite (AI Integration)
* **The Narrator (NVIDIA Llama 3):** The engine sends fighter data and the current "Theme" to NVIDIA's API. It returns a script: an Intro, Action sequences, and a Winner declaration.
* **The Artist (Supermachine):** 
    * **Infrastructure:** Uses an asynchronous Webhook architecture. The bot sends a request to Supermachine, which processes the image and POSTs the result back to a local `aiohttp` server running on the bot (exposed via `localtunnel`).
    * **Flow:** Images are generated **sequentially** (Scene 1 -> Scene 2 -> Scene 3) to prevent API timeouts and ensure high quality.

### Layer 3: The Blockchain Bridge (Solana)
* **Gatekeeper:** Checks user wallets to ensure they actually own the NFT they are trying to fight with.

## 4. Setup & Installation

### Prerequisites
* Python 3.10+
* Discord Bot Token
* NVIDIA API Key (for Text/Vision)
* Supermachine API Key (for Images)
* `localtunnel` (for Webhooks)

### Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r python_backend/requirements.txt
   ```
3. Configure environment variables in `python_backend/.env`.
4. Start the Webhook Tunnel:
   ```bash
   npx localtunnel --port 3000 --subdomain your-subdomain
   ```
5. Run the bot:
   ```bash
   cd python_backend
   python main.py
   ```

## 5. Lessons Learned & "The Pivot"
During development, we encountered several critical bottlenecks that shaped the current architecture:

*   **Gemini Rate Limits:** The free tier of Gemini proved unreliable for rapid-fire battle narration, often returning 429 errors. **Solution:** Switched to NVIDIA's Llama 3.1 hosted API.
*   **NVIDIA Safety Filters:** While fast, NVIDIA's image generation (SDXL/Flux) has strict safety filters that flagged "combat" and "fighting" prompts, resulting in black images. **Solution:** Pivoted to Supermachine (Flux/NextGen) which allows for the necessary creative freedom.
*   **Synchronous vs. Asynchronous:** Generating 3 high-quality images simultaneously caused timeouts. **Solution:** Implemented a sequential generation pipeline and a webhook listener to handle long-running generation tasks asynchronously.

## 6. Project Structure
```
python_backend/
├── main.py                 # Application entry point & Webhook Server
├── .env                    # API Keys
├── database/
│   ├── models.py           # SQLAlchemy Schema
│   └── db_manager.py       # Connection handling
├── commands/
│   ├── battle.py           # The core fight logic & loop
│   ├── flex.py             # User registration
│   └── betting.py          # Betting UI commands
├── integrations/
│   ├── nvidia_narrator.py      # Text generation (Llama 3)
│   ├── supermachine.py         # Image generation (Webhook based)
│   ├── nvidia_vision.py        # Avatar analysis
│   └── local_narrator.py       # Fallback text
├── engine/
│   ├── fairness.py         # Win/Loss math
│   └── betting.py          # Payout math
└── config/
    └── settings.py         # Global configuration
```
