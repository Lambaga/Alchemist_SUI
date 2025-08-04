# 🧙‍♂️ Der Alchemist

A Python-based 2D adventure game built with Pygame where you play as an alchemist collecting ingredients and brewing potions.

## 🎮 Game Features

- **Character Control**: Move with arrow keys or WASD
- **Alchemy System**: Collect ingredients (1, 2, 3 keys) and brew potions (Space)
- **Enemy System**: Battle demons and fire worms with AI behavior
- **Map System**: Tiled map integration with collision detection
- **Camera System**: Dynamic camera with zoom controls
- **Audio**: Background music and sound effects

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Lambaga/Alchemist_SUI.git
   cd Alchemist_SUI
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the game:**
   ```bash
   cd src
   python main.py
   ```

## 🎯 Game Controls

| Key | Action |
|-----|--------|
| `←→↑↓` or `WASD` | Move character |
| `1, 2, 3` | Collect ingredients |
| `Space` | Brew potion |
| `Backspace` | Remove last ingredient |
| `+/-` | Zoom in/out |
| `R` | Reset game |
| `M` | Toggle music |
| `F1` | Toggle collision debug |
| `ESC` | Exit game |

## 📁 Project Structure

```
Alchemist/
├── src/           # Source code
│   ├── main.py    # Main game entry point
│   ├── game.py    # Core game logic
│   ├── player.py  # Player character
│   ├── level.py   # Game level management
│   └── ...        # Other game modules
├── assets/        # Game assets
│   ├── Wizard Pack/    # Player sprites
│   ├── Demon Pack/     # Enemy sprites
│   ├── maps/           # Tiled maps
│   └── sounds/         # Audio files
├── docs/          # Documentation
└── scripts/       # Utility scripts
```

## 🛠️ Development

### Alternative Entry Points

The game has multiple entry points for different purposes:

- `main.py` - **Main game version (recommended)**
- `main_simple.py` - Simplified version for testing
- `main_clean.py` - Clean version for development

### Dependencies

- **pygame**: Main game engine
- **pytmx**: Tiled map loading support

### Asset Credits

- Wizard sprites: Custom sprite pack
- Demon sprites: Custom demon pack
- Fire worm sprites: Custom enemy pack
- Maps: Created with Tiled Map Editor

## 🐛 Troubleshooting

### Common Issues

1. **"pygame not found"**: Make sure you've installed dependencies with `pip install -r requirements.txt`

2. **"No module named 'pytmx'"**: Install pytmx with `pip install pytmx`

3. **Black screen or missing graphics**: Check that the `assets/` directory is present and contains the required sprite files

4. **Audio issues**: Ensure your system has audio drivers installed and pygame.mixer is working

### System Requirements

- **OS**: Windows 10+, macOS 10.14+, or Linux
- **Python**: 3.7 or higher
- **RAM**: 512MB minimum
- **Graphics**: Any graphics card with OpenGL support

## 📄 License

This project is for educational and personal use. Asset credits belong to their respective creators.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Contact

Project Link: [https://github.com/Lambaga/Alchemist_SUI](https://github.com/Lambaga/Alchemist_SUI)
