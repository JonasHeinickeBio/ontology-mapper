# GUI Advanced Features Documentation

## Overview

The BioPortal Ontology Alignment GUI has been enhanced with advanced features to improve usability, visualization, and workflow efficiency. This document describes all the new features and how to use them.

## Table of Contents

1. [Advanced Search Filters](#advanced-search-filters)
2. [Result Visualization](#result-visualization)
3. [Mapping Validation](#mapping-validation)
4. [Dark Mode](#dark-mode)
5. [Keyboard Shortcuts](#keyboard-shortcuts)
6. [Search History](#search-history)
7. [Enhanced UI Elements](#enhanced-ui-elements)
8. [Progress Indicators](#progress-indicators)

---

## Advanced Search Filters

### Confidence Score Filter
- **Location:** Configuration Tab → Search Options & Filters
- **Description:** Set a minimum confidence threshold (0.0 to 1.0) for filtering search results
- **Usage:** Drag the slider to adjust the minimum confidence score. Results below this threshold will be filtered out.
- **Benefit:** Get higher quality, more relevant results by filtering low-confidence matches

### Search Scope Options
- **Search in Synonyms:** Include synonym matching in searches
- **Search in Descriptions:** Include description text in searches
- **Benefit:** More comprehensive search coverage or more focused results

### Ontology Selection
- **Browse Ontologies Button:** Opens an interactive dialog to select specific ontologies
- **Features:**
  - Multi-select checkboxes for 14+ major ontologies
  - Select All / Clear All buttons
  - Search across MONDO, HP, NCIT, DOID, CHEBI, GO, and more
- **Usage:** Click "Browse Ontologies" to open the selection dialog, choose your ontologies, and click Apply

### Maximum Results
- **Description:** Control the number of results returned per search (1-20)
- **Benefit:** Balance between comprehensive results and processing time

---

## Result Visualization

### Mapping Statistics Chart
- **Location:** Results Tab → Mapping Statistics panel
- **Description:** Visual bar chart showing distribution of mappings across ontologies
- **Features:**
  - Color-coded bars for each ontology
  - Count labels on each bar
  - Automatic scaling
  - Shows top 10 ontologies by mapping count
- **Benefit:** Quick visual understanding of which ontologies are most represented in your mappings

### Color-Coded Results
- **Source Indicators:**
  - 🌐 = BioPortal source
  - 🔬 = OLS source
- **Visual Feedback:** Immediate identification of data sources

---

## Mapping Validation

### Automatic Validation
- **Location:** Results Tab → Validation & Quality Checks panel
- **Runs:** Automatically before generating output ontology
- **Checks:**

#### 1. Duplicate Detection
- Identifies when multiple concepts map to the same external URI
- **Warning Format:** Lists all concepts that share the same mapping
- **Action:** Review if multiple concepts should truly map to the same term

#### 2. Excessive Mappings
- Flags concepts with more than 5 mappings
- **Warning Format:** Shows concept name and mapping count
- **Action:** Review if all mappings are necessary and appropriate

#### 3. Low Confidence Warnings
- Identifies mappings with confidence scores below 0.5
- **Warning Format:** Shows concept → mapping pairs with confidence scores
- **Action:** Review and potentially remove low-confidence mappings

### Validation Results
- **Green ✅:** No issues detected
- **Yellow ⚠️:** Issues detected with detailed descriptions
- **Logged:** All validation results are logged to the processing log

---

## Dark Mode

### Activation
- **Toggle:** Configuration Tab → Advanced Features → 🌙 Dark Mode checkbox
- **Keyboard Shortcut:** Ctrl+D

### Theme Details
- **Dark Background:** #2b2b2b
- **Light Text:** #ffffff
- **Accent:** #404040
- **Log/Text Widgets:** #1e1e1e background

### Persistence
- Theme persists during the session
- Resets to light mode on restart

### Benefits
- Reduced eye strain during long sessions
- Better for low-light environments
- Modern, professional appearance

---

## Keyboard Shortcuts

### Available Shortcuts

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+S` | Start Processing | Begin ontology processing or query |
| `Ctrl+O` | Open File Browser | Browse for TTL files |
| `Ctrl+H` | Show Help | Display help window |
| `Ctrl+D` | Toggle Dark Mode | Switch between light and dark themes |
| `F1` | Show Help | Alternative help shortcut |
| `Esc` | Stop Processing | Stop current processing operation |

### Benefits
- Faster workflow
- Reduced mouse usage
- Power user efficiency
- Standard keyboard conventions

---

## Search History

### Features
- **Location:** Configuration Tab → Advanced Features → Recent Searches
- **Capacity:** Stores last 10 searches
- **Dropdown:** Quick access to previous queries
- **Auto-Population:** Single word queries automatically added to history

### Usage
1. Perform searches normally
2. Click the "Recent Searches" dropdown to see history
3. Select a previous search to reload it
4. Click "Clear History" to remove all entries

### Benefits
- Quick re-running of common searches
- No need to retype frequently used queries
- Compare results across time

---

## Enhanced UI Elements

### Tooltips
All action buttons now have helpful tooltips that appear on hover:
- **Start Processing:** "Start processing ontology or single word query (Ctrl+S)"
- **Load Example:** "Load an example ontology file for testing"
- **List Ontologies:** "Show list of available ontologies"
- **Help:** "Show help and keyboard shortcuts (F1)"

### Icon-Enhanced Buttons
- ▶ Start Processing
- 📁 Load Example
- 📋 List Ontologies
- ❓ Help
- 🌙 Dark Mode

### Improved Labels
- Color-coded status messages
- Emoji indicators for different sources
- Clear section headers with icons

---

## Progress Indicators

### Main Progress Bar
- **Location:** Processing Tab → Progress panel
- **Type:** Determinate (shows percentage)
- **Shows:** Overall progress through concepts
- **Updates:** Real-time as each concept is processed

### Network Activity Indicator
- **Location:** Processing Tab → Below main progress bar
- **Type:** Indeterminate (animated)
- **Shows:** Active API queries
- **Message:** "🌐 Querying BioPortal and OLS APIs..."
- **Auto-Hide:** Disappears when API call completes

### Detailed Progress Label
- **Shows:** Current concept being processed
- **Format:** "Processing concept X/Y: [concept name]"
- **Updates:** Real-time

### Status Bar
- **Location:** Bottom of main window
- **Shows:** Current operation status
- **Updates:** Context-aware messages

---

## Usage Examples

### Example 1: Using Advanced Filters for High-Quality Results
```
1. Open GUI
2. Set "Min Confidence Score" to 0.7
3. Enable "Search in Synonyms"
4. Click "Browse Ontologies"
5. Select MONDO, HP, and NCIT
6. Enter your query
7. Start processing
```

### Example 2: Quick Re-run with History
```
1. Perform initial search for "diabetes"
2. Do some other searches
3. Click "Recent Searches" dropdown
4. Select "diabetes" from history
5. Instantly reloaded - click Start
```

### Example 3: Reviewing Validation Issues
```
1. Complete processing
2. Switch to Results tab
3. Check "Validation & Quality Checks" panel
4. Review any warnings
5. Adjust selections if needed
6. Re-process if necessary
```

### Example 4: Dark Mode for Night Work
```
1. Press Ctrl+D or check Dark Mode checkbox
2. Theme switches instantly
3. Continue working comfortably
4. Press Ctrl+D again to return to light mode
```

---

## Accessibility Features

### Keyboard Navigation
- Full keyboard support for all operations
- Tab order properly configured
- Escape key for emergency stop

### Visual Indicators
- Color-coded status messages
- Icons for visual recognition
- Progress feedback for all operations
- Tooltips for guidance

### Screen Reader Support
- Proper label associations
- Status updates announced
- Error messages clearly labeled

---

## Performance Considerations

### Large Result Sets
- Progress indicators prevent UI freezing
- Network operations shown separately
- Cancel operation available at any time

### Validation Performance
- Fast O(n) duplicate detection
- Efficient statistical calculations
- Non-blocking UI updates

### Visualization Performance
- Canvas-based rendering for speed
- Automatic scaling for large datasets
- Top 10 limit prevents overcrowding

---

## Troubleshooting

### Dark Mode Issues
- **Problem:** Theme doesn't apply fully
- **Solution:** Restart application, some widgets may need reinitialization

### Keyboard Shortcuts Not Working
- **Problem:** Shortcuts not responding
- **Solution:** Ensure GUI window has focus, not a dialog

### Validation Warnings
- **Problem:** Many warnings shown
- **Solution:** This is normal - review each warning and decide if action needed

### Statistics Chart Not Showing
- **Problem:** Blank chart panel
- **Solution:** Ensure processing completed successfully and Results tab is selected

---

## Future Enhancements

Planned features for future releases:
- Export customization dialog
- Batch processing visualization
- More chart types (pie, line)
- Theme persistence across sessions
- Custom theme colors
- Additional validation rules
- Performance profiling
- Undo/redo functionality

---

## Support

For questions or issues with new features:
1. Press F1 or Ctrl+H for in-app help
2. Check the processing log for detailed information
3. Review validation panel for specific issues
4. Consult README.md for general usage

---

## Version History

### v2.0 - Advanced Features Release
- Added advanced search filters
- Added result visualization
- Added mapping validation
- Added dark mode
- Added keyboard shortcuts
- Added search history
- Added tooltips
- Added progress indicators
- Enhanced UI elements
