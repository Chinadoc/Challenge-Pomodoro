# Pomodoro Timer

A feature-rich Pomodoro timer application built with Python and CustomTkinter, designed to boost productivity through effective time management.

![Enhanced Pomodoro Timer](screenshots/app-screenshot.png)

## Features

### Core Timer
- Customizable work, short break, and long break durations
- Auto-start breaks and Pomodoros
- Session progress tracking
- Visual and audio notifications
- System tray integration

### Task Management
- Create, edit, and organize tasks
- Track time spent on each task
- Set priorities and due dates
- Categorize tasks with tags
- Mark tasks as completed

### Productivity Analytics
- Detailed session history
- Time tracking and statistics
- Daily, weekly, and monthly reports
- Task completion rates
- Focus and productivity trends

### Customization
- Multiple UI themes (light, dark, system)
- Adjustable font sizes
- Customizable timer display
- Sound effects and notification preferences

### Integration & Sync
- Export/import data (JSON)
- Cloud sync (coming soon)
- Calendar integration (coming soon)

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Tkinter (usually comes with Python)
- pip (Python package manager)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/enhanced-pomodoro-timer.git
   cd enhanced-pomodoro-timer
   ```

2. **Create and activate a virtual environment (recommended)**:
   ```bash
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Basic Usage
```bash
python -m pomodoro_enhanced
```

### Command Line Options
```bash
python -m pomodoro_enhanced [OPTIONS]

Options:
  --theme [light|dark|system]  Set the application theme
  --minimize                   Start minimized to system tray
  --debug                      Enable debug mode
  --help                       Show this message and exit
```

## Configuration

### Application Settings
Access settings through the application interface to configure:
- Timer durations
- Auto-start preferences
- Notification settings
- Theme and appearance
- Data management options

### Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| Space/Enter | Start/Pause timer |
| R | Reset current session |
| N | Skip to next session |
| S | Show/Hide settings |
| T | Show/Hide statistics |
| Q/Esc | Quit application |
| Ctrl+Shift+M | Minimize to system tray |

## Project Structure

```
pomodoro-timer/
├── pomodoro_enhanced/     # Main application package
│   ├── __init__.py        # Package initialization
│   ├── __main__.py        # Application entry point
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   ├── models.py      # Data models
│   │   ├── data_manager.py # Data persistence
│   │   └── timer_service.py # Timer logic
│   └── ui/                # User interface
│       ├── __init__.py
│       ├── main_window.py  # Main application window
│       ├── task_panel.py   # Task management UI
│       ├── stats_panel.py  # Statistics and analytics UI
│       └── settings_panel.py # Settings UI
├── tests/                 # Unit and integration tests
├── assets/                # Images, icons, and other resources
├── docs/                  # Documentation
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the Pomodoro Technique by Francesco Cirillo
- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Icons from [Material Design Icons](https://materialdesignicons.com/)

---

<p align="center">
  Made with and 
</p>
