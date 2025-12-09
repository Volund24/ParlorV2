# Project Roadmap & Todo

## 🛑 Priority: User Experience (UX)
- [ ] **Better Loading Indicators:** The current wait time for 3 images (especially with Supermachine) is long. We need:
    - [ ] "Typing" status in Discord while generating.
    - [ ] Progressive updates (e.g., "Generating Scene 1...", "Generating Scene 2...").
    - [ ] Maybe a "mini-game" or "betting window" during the generation phase to keep users engaged.
- [ ] **Timeout Tuning:** Supermachine takes a while. We should tune the timeout threshold. If it takes >45s, maybe we should fail over to Pollinations faster?

## ⚡ Optimization
- [ ] **Pre-generation:** Can we start generating Scene 2's image while Scene 1 is uploading? (Currently strictly sequential).
- [ ] **Caching:** Cache descriptions of known NFTs/PFPs to skip the Vision API step on repeat battles.

## 🎮 Gameplay Features
- [ ] **Betting System:** Allow spectators to bet points/currency on the winner before the result is revealed.
- [ ] **QTE (Quick Time Events):** Allow players to influence the battle outcome with reaction commands during the generation phase.

## 🎨 Art & Style
- [ ] **More Narrator Personas:** Expand the list of narrator voices.
- [ ] **Arena-Specific Styles:** Link the art style prompt to the chosen Arena (e.g., "Pixel Art" for Space Station, "Oil Painting" for Medieval).
