# AuraTable

AuraTable is an interactive dining experience developed using Python Arcade. Players guide Mira through taking an order, preparing ingredients, cooking, plating, and serving a meal to Sol.

## Requirements

- Python 3.12
- Arcade 3.3.3

## Installation and Launch

Extract the project ZIP and open a terminal in the folder containing `main.py`.

Install the dependency:

```bash
python -m pip install -r requirements.txt
```

Start the game:

```bash
python main.py
```

Keep the `images/` and `audio/` folders alongside the Python files. Preserve their filenames and folder structure.

## Gameplay and Controls

### Title Screen

- Click **Start** to begin.
- Mira walks towards the restaurant before the first scene.
- Click **Exit** to close the game.

### Scene 1: Taking an Order

- Follow the on-screen movement and interaction instructions.
- Choose either the **Herbal Bowl** or **Spicy Bowl**.
- Continue to ingredient preparation.

### Scene 2: Preparation

- Drag an ingredient to the sink and hold it there until washing finishes.
- Move the washed ingredient to the cutting board.
- Press **Space** or click the board when the timing indicator is in the green zone.
- Prepare all required ingredients to continue.

### Scene 3: Cooking

- Click the ingredient icons to add them to the pan.
- Use **Left/Right arrows** to adjust the heat.
- Keep the heat between **45% and 65%** for ideal cooking.
- Press **S** or move the mouse in circles near the pan to stir.
- Watch the heat warning and stirring freshness meters.
- Once cooking reaches **100%**, press **Enter** to finish.

Food burns if:

- Heat remains at **75% or higher for 3 continuous seconds**.
- Fully cooked food remains at **45% heat or higher for 5 continuous seconds**.

Burning opens the **Failed** screen. Press **R** to retry cooking.

### Scene 4: Plating and Serving

- Drag the cooked food and garnish onto the plate.
- Spills appear after both have been placed.
- Drag the cloth over the spills to clean them.
- Press **Enter** to carry the dish.
- Move using **arrow keys or WASD**.
- Press **E** near Sol to serve.

### Results

- View the final score.
- Click **Back to Home** to return to the title screen.
- Click **Exit** to close the game.

Press **M** during gameplay to toggle music and sound effects.

## Scoring

The final quality score combines:

| Component | Maximum contribution |
|---|---:|
| Order choice | 20 |
| Preparation | 40 |
| Cooking | 30 |
| Plating and cleanliness | 10 |

Cooking is first scored out of **40**, then converted to a maximum contribution of **30**:

- Heat control: up to **30 cooking points**.
- Stirring freshness maintained during cooking: up to **10 cooking points**.

The Spicy Bowl can reach **100 overall points**. The Herbal Bowl can reach **95**, because the order-choice scoring gives Sol a preference for the Spicy Bowl.

Retrying a stage resets its score and the scores of later stages.

## Features

- Animated title screen with rain.
- Character idle, walking, chopping, and stirring animations.
- Four interactive dining scenes.
- Drag-and-drop preparation and plating.
- Timed chopping interaction.
- Heat control and cooking progress.
- Heat warning countdown and overheating failure.
- Stirring freshness meter.
- Spill-cleaning interaction.
- Particle effects, including washing splashes, steam, sparks, glow, and confetti.
- Animated scene transitions.
- Background music and interaction sounds.
- Final quality scoring.

## Project Files

| File or folder | Purpose |
|---|---|
| `main.py` | Game entry point |
| `title_view.py` | Title screen |
| `welcome_view.py` | Ordering scene |
| `prep_view.py` | Preparation scene |
| `cook_view.py` | Cooking scene |
| `serve_view.py` | Plating, serving, and results |
| `transition_view.py` | Scene transitions |
| `game_support.py` | Shared scoring and asset path handling |
| `audio_manager.py` | Music and sound playback |
| `images/` | Visual assets |
| `audio/` | Music and sound effects |
| `requirements.txt` | Python dependency |

## Audio Files

The game uses these files inside `audio/`:

- `background.wav`
- `wash.wav`
- `chop.wav`
- `sizzle.wav`
- `stir.wav`
- `success.wav`

Audio playback is optional. Missing audio files or unavailable sound devices should not prevent the game from running.