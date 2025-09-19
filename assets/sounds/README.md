# Sounds Structure

Put audio files here. Supported formats: .wav (preferred), .ogg, .mp3.

Folders:
- ui/: UI clicks, open/close, select, error
- spells/elements/: single element taps (fire, water, stone)
- spells/combos/: cast sounds for combined spells (e.g., fire_fire.wav)
- player/: footsteps, hurt, heal, level-up
- enemies/: enemy-specific SFX (growl, hit, die)
- ambient/: rain, wind, fireplace, town ambience
- music/: background music tracks (looped)

Naming conventions:
- Lowercase, hyphen-separated.
- Elements: fire.wav, water.wav, stone.wav
- Combos: fire_fire.wav, water_water.wav, water_stone.wav, etc.
- UI: click.wav, confirm.wav, cancel.wav, error.wav

Recommended sample rate: 44.1 kHz, 16-bit PCM for .wav.

Looping tips:
- Provide seamless loop points; keep short fades for UI.

