# 📊 Missing Migrants: Advanced Analytics Dashboard

A cutting-edge visualization dashboard featuring 8 advanced interactive charts powered by Plotly and Dash.

## 🎯 Features

### 1. **🗺️ Animated Time Map**
- Watch migration crisis hotspots evolve year by year
- Interactive time slider to scrub through history
- Bubble size indicates severity

### 2. **🔀 Sankey Flow Diagram**
- Visualize migration journey: Origin → Incident Location → Cause of Death
- See which routes lead to which outcomes
- Flow thickness indicates death toll

### 3. **📈 Stacked Area Chart**
- Causes of death composition over time
- See trend changes (e.g., drowning vs violence)
- Hover for exact values

### 4. **🌍 Choropleth Heat Map**
- World map colored by total deaths per country
- Quick geographic comparison
- Click and zoom capabilities

### 5. **☀️ Sunburst Hierarchy**
- Interactive drill-down: Region → Country → Route
- Click segments to zoom in
- Perfect for exploring data structure

### 6. **🔥 Seasonality Heatmap**
- Calendar view: Month vs Year
- Spot dangerous seasons at a glance
- Color intensity = death toll

### 7. **📦 Box Plot: Incident Severity**
- Distribution of deaths per incident by region
- Shows median, quartiles, and outliers
- Identify deadliest routes

### 8. **🫧 Bubble Chart: COD × Region**
- 2D comparison grid
- Bubble size = total deaths
- See which causes dominate which regions

---

## 🚀 Installation & Setup

### Prerequisites
```bash
# Python 3.8+ required
python3 --version
```

### Install Dependencies
```bash
pip install dash plotly pandas numpy dash-bootstrap-components
```

Or using the requirements file:
```bash
pip install -r requirements.txt
```

---

## ▶️ How to Run

### Method 1: Default Port (8051)
```bash
python3 app_advanced.py
```

Then open your browser to:
```
http://localhost:8051
```

### Method 2: Custom Port
Edit line 792 in `app_advanced.py`:
```python
app.run_server(debug=True, port=YOUR_PORT)
```

---

## 📂 Data Source

The app uses: `MM_Dummies_CleanRefactored_Jan16.csv`

**Dataset contains:**
- 21,344 incidents (2014-2026)
- 80,152 total dead/missing migrants
- 152 countries
- 32 migration routes

---

## 🎨 Design Choices

### Theme: **CYBORG (Dark)**
- Professional dark theme for data-heavy visualizations
- High contrast for readability
- Color scheme: Plasma + YlOrRd (heatmaps)

### Color Palette
- Highlight: `#0099C6` (cyan)
- Deaths: `#ff4444` (red)
- Background: `#1a1a1a` (dark gray)

---

## 🎮 Interactive Features

### Filters (Top of Dashboard)
- **Year**: Filter by specific year or view all
- **Region**: Focus on specific regions
- **Migration Route**: Narrow down to specific routes

### Chart Interactions
- **Hover**: See detailed tooltips
- **Click**: Select data points
- **Zoom**: Scroll to zoom on maps
- **Pan**: Drag to move around
- **Reset**: Double-click to reset view
- **Download**: Use camera icon to save charts

---

## 🔧 Customization

### Change Data File
Edit line 75 in `app_advanced.py`:
```python
MM = load_data("YOUR_FILE.csv")
```

### Adjust Chart Heights
Modify `style={'height': '500px'}` in layout section

### Change Color Schemes
Update these variables:
```python
COLOR_SCHEME = px.colors.sequential.Plasma  # Chart colors
COLOR_CONTINUOUS = 'YlOrRd'  # Heatmap colors
HIGHLIGHT_COLOR = '#0099C6'  # Accent color
```

Available Plotly color scales:
- `Viridis`, `Plasma`, `Inferno`, `Magma`
- `YlOrRd`, `YlGnBu`, `RdYlGn`
- `Blues`, `Reds`, `Greens`

---

## 📊 Performance Notes

- **Loading Time**: ~2-3 seconds for 21K records
- **Filter Response**: Near-instant (client-side storage)
- **Animation**: Smooth on modern browsers
- **Memory Usage**: ~200MB RAM

### Optimization Tips
1. Close unused browser tabs
2. Use Chrome/Firefox for best performance
3. Reduce animation frame count for slower machines

---

## 🐛 Troubleshooting

### Charts not loading?
- Check browser console (F12) for errors
- Ensure all data columns exist in CSV
- Verify data types (dates, numbers)

### Port already in use?
```bash
# Find and kill process using port 8051
lsof -ti:8051 | xargs kill -9
```

### Missing data message?
- Check filter combinations aren't too restrictive
- Verify CSV file path is correct

---

## 📈 Comparison: Basic vs Advanced

| Feature | Basic App | Advanced App |
|---------|-----------|--------------|
| Charts | 11 | 8 (more sophisticated) |
| Animation | No | Yes (time slider) |
| Hierarchy | Limited | Full drill-down |
| Flow Analysis | No | Yes (Sankey) |
| Heatmaps | No | Yes (2D) |
| Theme | Light (Flatly) | Dark (Cyborg) |

---

## 🎓 Learning Resources

**Plotly Documentation:**
- https://plotly.com/python/
- https://dash.plotly.com/

**Color Scales:**
- https://plotly.com/python/builtin-colorscales/

**Dash Bootstrap:**
- https://dash-bootstrap-components.opensource.faculty.ai/

---

## 📝 TODO / Future Enhancements

- [ ] Add time-range slider (select custom date ranges)
- [ ] Implement linked brushing (select on one chart → filters all)
- [ ] Add "Compare Years" mode (side-by-side)
- [ ] Top 10 statistics cards
- [ ] Download filtered data button
- [ ] User-customizable color schemes
- [ ] Responsive mobile layout
- [ ] Multi-language support

---

## 🙏 Credits

**Data Source:** International Organization for Migration (IOM)
**Framework:** Plotly Dash
**Theme:** Dash Bootstrap Components (Cyborg)

---

## 📄 License

This visualization tool is for educational and humanitarian awareness purposes.
Data is public domain from IOM Missing Migrants Project.

---

**Questions? Issues? Suggestions?**
Open an issue or submit a pull request!

🌟 **Star this repo if you find it useful!** 🌟
