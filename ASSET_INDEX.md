# AuraTable Environment, Effects, and Interaction Pack

All artwork uses one colourful 2D pixel-art style designed for a 1280 × 720 Python Arcade project. Backgrounds contain large static scenery; smaller gameplay objects remain separate transparent PNG sprites.

## Backgrounds

| File | Intended use |
| --- | --- |
| `images/backgrounds/title_screen.png` | Title and main-menu overlay |
| `images/backgrounds/scene_1_welcome_room.png` | Guest welcome and meal selection |
| `images/backgrounds/scene_2_prep_kitchen.png` | Ingredient washing and chopping |
| `images/backgrounds/scene_3_living_stove.png` | Cooking and heat-control interactions |
| `images/backgrounds/scene_4_plating_service.png` | Plating, garnish, and table service |
| `images/backgrounds/results_screen.png` | Score, crystal, and replay overlay |

## Effects

`water_droplet.png`, `vegetable_fragment.png`, `steam_puff.png`, `smoke_puff.png`, `oil_spark.png`, `golden_glow_particle.png`, and `confetti_particle.png` are transparent sprites. `effects_sprite_sheet.png` retains the combined source sheet.

## Interactive objects

The separate prop sprites are: faucet, ingredient basket, cutting board, knife, frying pan, stirring spoon, empty plate, empty serving bowl, teal cloth, candle, recipe card, and stove heat knob. The combined source is `images/objects/interactive/interactive_props_sprite_sheet.png`.

## Interface sprites

The interface set contains herbal and spicy meal cards, an E-key interaction prompt, continue, replay, and exit buttons. The combined source is `images/ui/interactive_ui_sprite_sheet.png`.

## Arcade integration notes

- Load backgrounds at native 1280 × 720 or scale them to the window size.
- Use nearest-neighbour filtering when scaling sprites to preserve hard pixel edges.
- Spawn multiple small copies of an effect sprite for particles; vary scale, velocity, lifetime, alpha, and rotation in code.
- Keep title text, scores, instructions, and button labels in Arcade so they remain crisp and easy to update.
