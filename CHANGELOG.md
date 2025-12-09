# Changelog

## [1.0.0] - 2025-12-08 (The "Stable" Release)

### 🚀 Major Features
- **Hybrid AI Pipeline:** Successfully integrated a robust multi-provider AI system.
    - **Text:** NVIDIA Llama 3.1 405B (Primary) + Local Fallback.
    - **Images:** Supermachine NextGen (Primary) + Pollinations.ai (Fallback).
- **Sequential Generation:** Implemented a smart queuing system for image generation to prevent API timeouts and rate limits (Scene 1 -> Scene 2 -> Scene 3).
- **Webhook Architecture:** Built a custom `aiohttp` server with `localtunnel` to handle asynchronous image callbacks from Supermachine.
- **NFT Integration:** Added specific dropdown support for major NFT collections (Bored Ape, Stoned Ape Crew, The Growerz, etc.).

### 🛠 Fixes & Improvements
- **Removed Gemini:** Completely stripped out the Google Gemini integration due to unreliable rate limits (429 errors).
- **Fixed Supermachine Auth:** Corrected the authentication logic to use `authToken` instead of `token` and fixed the payload structure for the "NextGen" model.
- **Fixed NVIDIA Safety:** Deprecated NVIDIA Image Gen for battle scenes to avoid "Safety Filter" blocks on combat imagery.
- **Parallel Text:** Text generation for all 3 scenes now happens in parallel for maximum speed, while images remain sequential for stability.

### 📦 Dependencies
- Removed `google-generativeai`.
- Added `aiohttp` (Server/Client).
- Added `localtunnel` (External Tool).

### 📝 Configuration
- **New Env Vars:** `SUPERMACHINE_API_KEY`, `NVIDIA_API_KEY`.
- **Removed Env Vars:** `GEMINI_API_KEY`.

## [1.1.0] - 2025-12-08 (The "Polish" Update)

### 🎨 Visual & Narrative Upgrades
- **ControlNet Integration:** Added "Custom PFP" support. The bot now uses the player's avatar as a reference image (ControlNet) for consistent character generation across battle scenes.
- **Narrator Personas:** Replaced the static narrator with dynamic personalities. Battles are now narrated by random personas like "Gritty Noir Detective," "Hype-Man," or "Nature Documentary Narrator."
- **Style Overhaul:** Updated the global art style prompt to "High-Fidelity Comic Book Art" (replacing the "Scooby Doo" cartoon style).

### 🛡️ Reliability
- **Fallback Validation:** Confirmed and refined the automatic fallback system. If Supermachine times out, the system seamlessly switches to Pollinations.ai to ensure the battle completes.
