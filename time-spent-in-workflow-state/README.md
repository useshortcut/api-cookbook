# Time Spent in Workflow States

This script analyzes the amount of wall-clock time each Shortcut story spent in different workflow states by examining the story's history data.

## What it does

For each story ID provided, the script:

1. **Fetches Story History**: Uses the Shortcut Story History API endpoint to get all historical changes
2. **Parses Workflow Changes**: Extracts workflow state transitions with timestamps
3. **Maps State IDs to Names**: Fetches workflow definitions to convert state IDs to readable names
4. **Calculates Time**: Computes the wall-clock time spent in each workflow state
5. **Exports Results**: Generates a CSV file with detailed breakdown and displays a summary

## Key Features

- **Comprehensive Analysis**: Tracks time in all workflow states, including partial time if a story is still in progress
- **Done State Filtering**: By default excludes "done" type states to focus on active work; optional flag to include them
- **Workflow-Ordered Results**: States are displayed in the order they appear in the workflow, not alphabetically
- **Multiple Story Support**: Analyze multiple stories in a single run via command-line arguments or CSV file input
- **Flexible CSV Input**: Accepts single-column or multi-column CSV files with automatic header detection
- **Error Handling**: Gracefully handles missing stories, API errors, and malformed data
- **CSV Export**: Results are exported to CSV for further analysis
- **Detailed Reporting**: Shows percentages and totals for each story

## Prerequisites

1. **Python 3.x** with the `requests` library installed
2. **Shortcut API Token** - Set as an environment variable named `SHORTCUT_API_TOKEN`
   - Get your token from: https://app.shortcut.com/settings/account/api-tokens
   - Set it as an environment variable: `export SHORTCUT_API_TOKEN="your_token_here"`

## Usage

### Basic Usage

**Option 1: Provide story IDs as command-line arguments**
```bash
python time-spent-in-workflow-state.py [story_id1] [story_id2] [story_id3] ...
```

**Option 2: Provide story IDs via CSV file**
```bash
python time-spent-in-workflow-state.py --input-csv INPUT_FILE.csv
```

**Note:** You must use either command-line arguments OR `--input-csv`, but not both.

### CSV Input Format

When using `--input-csv`, the script supports flexible CSV formats:

#### Single Column CSV
If your CSV has only one column, that column will be used for story IDs:

```csv
304797
304798
304799
```

Or with a header:
```csv
Story ID
304797
304798
304799
```

#### Multiple Column CSV
If your CSV has multiple columns, it must have a header row with a column named `storyid` or `story_id` (case-insensitive):

```csv
story_id,name,status
304797,Fix authentication bug,Completed
304798,Add new feature,In Development
304799,Update documentation,Ready for Review
```

Or:
```csv
StoryID,Title,Owner
304797,Fix authentication bug,John Doe
304798,Add new feature,Jane Smith
```

### Examples

```bash
# Analyze a single story
python time-spent-in-workflow-state.py 12345

# Analyze multiple stories
python time-spent-in-workflow-state.py 12345 67890 11111

# Analyze stories from a CSV file
python time-spent-in-workflow-state.py --input-csv stories.csv

# Analyze with custom output CSV filename
python time-spent-in-workflow-state.py 12345 67890 --csv my_analysis.csv

# Include time spent in "done" type workflow states (excluded by default)
python time-spent-in-workflow-state.py 12345 --include-done-states

# Combine CSV input with other options
python time-spent-in-workflow-state.py --input-csv stories.csv --include-done-states --csv output.csv

# Show detailed results for each story (verbose mode)
python time-spent-in-workflow-state.py 12345 67890 --verbose
```

## Output

### Console Output

**Default output** shows:
- Progress messages for each story being analyzed
- Summary count of stories processed (successful vs. failed)
- CSV export location

**Verbose output** (with `--verbose` or `-v` flag) additionally shows:
- Detailed breakdown for each story including:
  - Story name and type
  - Current workflow state
  - Time spent in each state (hours and percentages)
  - Total time tracked

### CSV Export

A CSV file is automatically generated in the current directory with columns:
- **StoryID**: The Shortcut story identifier
- **StoryName**: The title of the story
- **StoryType**: Type of story (Feature, Bug, Chore, etc.)
- **CurrentState**: The story's current workflow state
- **State**: Individual workflow state name
- **HoursSpent**: Time spent in that particular state

## How Time Calculation Works

1. **Historical Analysis**: The script examines the story's complete history to find workflow state changes
2. **Chronological Ordering**: All state changes are sorted by timestamp
3. **Duration Calculation**: Time between consecutive state changes is calculated
4. **Current State Handling**: For stories still in progress, time from the last state change to now is included
5. **Aggregation**: If a story returns to a previous state, the times are summed together
6. **Done State Filtering**: By default, workflow states with type "done" are excluded from analysis to focus on active work time. Use `--include-done-states` to include them.

## API Endpoints Used

The script makes **read-only** API calls to these Shortcut endpoints:

- `GET /api/v3/stories/{story_id}/history` - Fetches story history
- `GET /api/v3/stories/{story_id}` - Gets current story details  
- `GET /api/v3/workflows` - Retrieves workflow state definitions

## Error Handling

The script handles various error scenarios:

- **Invalid Story IDs**: Reports stories that don't exist
- **API Authentication Issues**: Clear error messages for token problems
- **Network Issues**: Graceful handling of connectivity problems
- **Malformed Data**: Fallbacks for unexpected API response formats
- **Missing Environment Variables**: Clear setup instructions

## Limitations

- **API Rate Limits**: For large numbers of stories, you may hit Shortcut's rate limits
- **Historical Data**: Only analyzes data available in Shortcut's history (some very old changes might not be available)
- **Timezone Handling**: All times are calculated in UTC
- **Workflow Changes**: Only tracks workflow state changes, not other types of story modifications

## Example Output

### Default Output

```
Analyzing story 12345...
Analyzing story 67890...

Processed 2 stories (2 successful, 0 failed)
Results exported to: time-spent-in-workflow-state_20231216_162345.csv
```

### Verbose Output (--verbose flag)

```
Analyzing story 12345...
Analyzing story 67890...

================================================================================
WORKFLOW TIME ANALYSIS SUMMARY
================================================================================
Successfully analyzed: 2 stories
Failed to analyze: 0 stories

Detailed Results:
--------------------------------------------------------------------------------

Story 12345: Implement user authentication
Type: feature | Current State: Done
Workflow changes: 4
Time in states:
  - Ready for Development: 72.50 hours (50.0%)
  - In Development: 48.25 hours (33.3%)
  - Ready for Testing: 24.25 hours (16.7%)
Total time tracked: 145.00 hours
(Note: "Done" state excluded by default. Use --include-done-states to include it.)

Story 67890: Fix login bug
Type: bug | Current State: In Development
Workflow changes: 2
Time in states:
  - Ready for Development: 12.25 hours (33.9%)
  - In Development: 23.85 hours (66.1%)
Total time tracked: 36.10 hours

Results exported to: time-spent-in-workflow-state_20231216_162345.csv
```

## Troubleshooting

1. **"SHORTCUT_API_TOKEN environment variable is required"**
   - Make sure you've set your API token: `export SHORTCUT_API_TOKEN="your_token"`

2. **"Story XXXXX not found"**
   - Verify the story ID exists and you have access to it

3. **"Error fetching workflow states"**
   - Check your API token permissions and network connectivity

4. **Empty results**
   - The story might not have any workflow state changes in its history
   - Very new stories might not have enough history data

5. **"Cannot specify both story IDs as arguments and --input-csv"**
   - You must use either command-line story IDs OR --input-csv, not both
   - Remove one of the input methods

6. **"Could not find 'storyid' or 'story_id' column in CSV header"**
   - For multi-column CSVs, ensure your header row includes a column named `storyid` or `story_id` (case-insensitive)
   - Alternatively, use a single-column CSV with just the story IDs

7. **"CSV file is empty" or "No story IDs found in CSV file"**
   - Check that your CSV file contains data
   - Ensure story ID values are not all empty or whitespace

## Contributing

This script is part of the Shortcut API Cookbook. Feel free to submit issues or pull requests to improve it!
