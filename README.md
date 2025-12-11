# Weekly Planner

A minimal and elegant weekly calendar and to-do organizer built with Python and Qt.  
Drag tasks and events onto a calendar, organize your week, zoom in and out, change colors, import events from `.ics` files (Google Calendar, Outlook), and enjoy a modern dark/light interface.

---

## Features

- **Weekly calendar (Monday–Sunday)** grid for events
- **Day-specific to-do lists** beneath the calendar
- **Drag and drop** to schedule tasks
- **Vertical zoom** (see more or fewer hours, with scroll)
- **Light/dark mode toggle**
- **Color themes** for events
- **Confetti animation** when you complete a task
- **Import events from .ics files** (Google/Outlook/Apple Calendar compatible)
- **Responsive design**

---

## How to Get Started

### 1. **Clone the repository**
```bash
git clone https://github.com/yourusername/weekly-planner.git
cd weekly-planner
```

### 2. **Install the requirements**

Make sure you have Python 3.8+ installed.  
Then install dependencies:

```bash
pip install -r requirements.txt
```

### 3. **Start the app**

```bash
python weeklyplanner.py
```

---

## How to Use

- **Add a to-do:** Type in the day’s "Add to-do..." box and click `+` (or press Enter).
- **Mark as complete:** Check the box; the text fades and you see some celebratory confetti!
- **Schedule a to-do/event:** Drag the "handle" icon to the calendar. You can move and resize event blocks.
- **Zoom in/out:** Use the `＋` and `－` buttons in the top bar to change hour grid spacing. Scroll to view more hours if needed.
- **Switch light/dark mode:** Click the sun/moon icon.
- **Change event color:** Double-click an event on the calendar and select a color.
- **Delete to-do:** Click the `×` on any to-do item.
- **Import calendar events:** Click the `Import .ics` button and select any `.ics` file exported from Google Calendar, Outlook, or Apple Calendar. Only events in the current week will be shown.
- **Move window:** Drag anywhere in the window background.
- **Close/minimize:** Use the red/yellow buttons in the top-left corner.

- `Note` If you exit out of the window, all tasks and calendar events will be erased, keep the app minimized on the dock to maintain task persistence.

---

## Unit Tests

To run unit tests, set `run_tests = False` to `True` in line `1564` of `weeklyplanner.py`
Unit test results will be displayed in the terminal.  

---

## Tips

- **.ics import:** To get an `.ics` file from Google Calendar or Outlook, export your calendar via their settings. Only events for the week you're viewing will appear after import.
- An example `.ics` file is included in this repository under the name `calendar.ics`
- **Set your own icon:** Place your own `appicon.png` in the root folder for a custom dock/taskbar icon.
- **Font issues:** On some systems, you can edit the font in code from `"Arial"` to better match your desktop environment.

---

## Troubleshooting

- If you see missing icon or font warnings, ensure you've got `appicon.png` and the fonts are available on your OS.
- For issues with SVG icons, make sure to install the PySide6 SVG extras.
- If you get permission errors importing calendars, check your `.ics` file path and format.

---

## License

MIT License

---

## Credits

- Built atop [PySide6](https://pypi.org/project/PySide6/) and [ics.py](https://pypi.org/project/ics/).
- Calendar UI inspired by modern desktop planners.

---

## Contributing

Pull requests and suggestions welcome! Open an issue for feature ideas or bugs.

---

Enjoy planning your week!
