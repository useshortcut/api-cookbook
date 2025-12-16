#!/usr/bin/env python3
"""
Shortcut Story Workflow Time Analysis

This script analyzes the amount of wall-clock time each story spent in different workflow states
by fetching and parsing story history data from the Shortcut API.

Usage:
    python workflow_time_analysis.py story_id1 story_id2 story_id3 ...
    
Requirements:
    - Set SHORTCUT_API_TOKEN environment variable
    - Python 3.x with requests library

Example:
    python workflow_time_analysis.py 12345 67890 11111
"""

import os
import sys
import requests
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import argparse
import csv


class ShortcutWorkflowAnalyzer:
    """Analyzes time spent by stories in different workflow states."""
    
    def __init__(self, include_done_states: bool = False):
        """Initialize the analyzer with API configuration.

        Args:
            include_done_states: Whether to include time spent in "done" type states (default: False)
        """
        self.api_token = os.getenv('SHORTCUT_API_TOKEN')
        if not self.api_token:
            raise ValueError("SHORTCUT_API_TOKEN environment variable is required")

        self.api_base_url = 'https://api.app.shortcut.com/api/v3'
        self.headers = {
            'Shortcut-Token': self.api_token,
            'Content-Type': 'application/json'
        }
        self.include_done_states = include_done_states
    
    def fetch_story_history(self, story_id: str) -> Dict[str, Any]:
        """
        Fetch the complete history for a given story.
        
        Args:
            story_id: The ID of the story to analyze
            
        Returns:
            Dictionary containing the story history data
            
        Raises:
            requests.exceptions.RequestException: If the API call fails
        """
        url = f"{self.api_base_url}/stories/{story_id}/history"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching history for story {story_id}: {e}")
            if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                print(f"Story {story_id} not found. Please check the story ID.")
            raise
    
    def fetch_story_details(self, story_id: str) -> Dict[str, Any]:
        """
        Fetch basic story details to get current state.
        
        Args:
            story_id: The ID of the story
            
        Returns:
            Dictionary containing story details
        """
        url = f"{self.api_base_url}/stories/{story_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching story details for {story_id}: {e}")
            raise
    
    def parse_workflow_changes(self, history_data: List[Dict[str, Any]], story_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse the history data to extract workflow state changes with timestamps.

        Args:
            history_data: The history data from the API
            story_details: Current story details

        Returns:
            List of workflow state changes with timestamps
        """
        workflow_changes = []

        # Process history events
        for event in history_data:
            if 'actions' in event:
                for action in event['actions']:
                    # Look for story updates with workflow state changes
                    if action.get('entity_type') == 'story':
                        # Check for create action (initial state)
                        if action.get('action') == 'create' and 'workflow_state_id' in action:
                            workflow_changes.append({
                                'timestamp': event.get('changed_at'),
                                'from_state_id': None,
                                'to_state_id': action.get('workflow_state_id'),
                                'changed_by': event.get('member_id'),
                                'is_initial': True
                            })

                        # Check for update action with workflow state changes
                        if action.get('action') == 'update' and 'changes' in action:
                            changes = action.get('changes', {})
                            if 'workflow_state_id' in changes:
                                wf_change = changes['workflow_state_id']
                                workflow_changes.append({
                                    'timestamp': event.get('changed_at'),
                                    'from_state_id': wf_change.get('old'),
                                    'to_state_id': wf_change.get('new'),
                                    'changed_by': event.get('member_id'),
                                    'is_initial': False
                                })

        # Sort by timestamp to ensure chronological order
        workflow_changes.sort(key=lambda x: x['timestamp'])

        # Add current state if story is still active and different from last known state
        if workflow_changes and story_details.get('workflow_state_id'):
            # Check if the last change matches current state
            last_change = workflow_changes[-1]
            if last_change['to_state_id'] != story_details['workflow_state_id']:
                # Add implicit change to current state
                workflow_changes.append({
                    'timestamp': story_details.get('updated_at'),
                    'from_state_id': last_change['to_state_id'],
                    'to_state_id': story_details['workflow_state_id'],
                    'changed_by': None,
                    'is_initial': False
                })

        return workflow_changes
    
    def fetch_workflow_states(self) -> tuple[Dict[int, str], Dict[int, int], Dict[int, str]]:
        """
        Fetch all workflow states to map IDs to names, order, and types.

        Returns:
            Tuple of (state_map, state_order, state_types) where:
            - state_map: Dictionary mapping state IDs to state names
            - state_order: Dictionary mapping state IDs to their order position within their workflow
            - state_types: Dictionary mapping state IDs to their type (backlog, unstarted, started, done)
        """
        url = f"{self.api_base_url}/workflows"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            workflows = response.json()

            state_map = {}
            state_order = {}
            state_types = {}

            for workflow in workflows:
                for position, state in enumerate(workflow.get('states', [])):
                    state_id = state['id']
                    state_map[state_id] = state['name']
                    state_order[state_id] = position
                    state_types[state_id] = state.get('type', 'unknown')

            return state_map, state_order, state_types
        except requests.exceptions.RequestException as e:
            print(f"Error fetching workflow states: {e}")
            return {}, {}, {}
    
    def calculate_time_in_states(self, workflow_changes: List[Dict[str, Any]], state_map: Dict[int, str],
                                 state_types: Dict[int, str], include_done_states: bool = False) -> Dict[int, float]:
        """
        Calculate the time spent in each workflow state.

        Args:
            workflow_changes: List of workflow state changes
            state_map: Mapping of state IDs to names
            state_types: Mapping of state IDs to types
            include_done_states: Whether to include time spent in "done" type states (default: False)

        Returns:
            Dictionary mapping state IDs to time spent (in hours)
        """
        time_in_states = {}

        if not workflow_changes:
            return time_in_states

        for i in range(len(workflow_changes)):
            current_change = workflow_changes[i]
            to_state_id = current_change['to_state_id']

            # Skip "done" type states unless explicitly included
            if not include_done_states and state_types.get(to_state_id) == 'done':
                continue

            # Parse the current timestamp
            current_time = self._parse_timestamp(current_change['timestamp'])

            # Calculate time spent in this state
            if i < len(workflow_changes) - 1:
                # Not the last change, use next change timestamp
                next_change = workflow_changes[i + 1]
                next_time = self._parse_timestamp(next_change['timestamp'])
                time_spent = (next_time - current_time).total_seconds() / 3600  # Convert to hours
            else:
                # Last change - if story is complete, calculate to now
                # Otherwise, this represents current state
                now = datetime.now(timezone.utc)
                time_spent = (now - current_time).total_seconds() / 3600

            # Add to total time for this state
            if to_state_id in time_in_states:
                time_in_states[to_state_id] += time_spent
            else:
                time_in_states[to_state_id] = time_spent

        return time_in_states
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse a timestamp string into a datetime object.
        
        Args:
            timestamp_str: ISO format timestamp string
            
        Returns:
            datetime object
        """
        if not timestamp_str:
            return datetime.now(timezone.utc)
        
        # Handle different timestamp formats
        try:
            # Try parsing with timezone info
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Fallback to basic parsing
                return datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
            except ValueError:
                # Last resort
                return datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    
    def analyze_story(self, story_id: str) -> Dict[str, Any]:
        """
        Analyze a single story's time spent in workflow states.
        
        Args:
            story_id: The ID of the story to analyze
            
        Returns:
            Dictionary containing the analysis results
        """
        try:
            print(f"Analyzing story {story_id}...")
            
            # Fetch data
            history_data = self.fetch_story_history(story_id)
            story_details = self.fetch_story_details(story_id)
            
            # Get workflow state mapping, order, and types
            state_map, state_order, state_types = self.fetch_workflow_states()

            # Parse workflow changes
            workflow_changes = self.parse_workflow_changes(history_data, story_details)

            # Calculate time in states
            time_in_states = self.calculate_time_in_states(workflow_changes, state_map, state_types, self.include_done_states)

            return {
                'story_id': story_id,
                'story_name': story_details.get('name', 'Unknown'),
                'story_type': story_details.get('story_type', 'Unknown'),
                'current_state': state_map.get(story_details.get('workflow_state_id'), 'Unknown'),
                'time_in_states': time_in_states,
                'state_map': state_map,
                'state_order': state_order,
                'total_changes': len(workflow_changes),
                'analysis_successful': True
            }
            
        except Exception as e:
            print(f"Error analyzing story {story_id}: {e}")
            return {
                'story_id': story_id,
                'error': str(e),
                'analysis_successful': False
            }
    
    def analyze_stories(self, story_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple stories.
        
        Args:
            story_ids: List of story IDs to analyze
            
        Returns:
            List of analysis results
        """
        results = []
        
        for story_id in story_ids:
            result = self.analyze_story(story_id)
            results.append(result)
        
        return results
    
    def export_to_csv(self, results: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Export analysis results to CSV file.
        
        Args:
            results: Analysis results
            filename: Output filename (optional)
            
        Returns:
            Path to the created CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'time-spent-in-workflow-state_{timestamp}.csv'

        # Create CSV in current directory
        csv_path = filename
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['StoryID', 'StoryName', 'StoryType', 'CurrentState', 'State', 'HoursSpent']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                if result.get('analysis_successful'):
                    story_id = result['story_id']
                    story_name = result['story_name']
                    story_type = result['story_type']
                    current_state = result['current_state']
                    state_map = result.get('state_map', {})
                    state_order = result.get('state_order', {})

                    # Sort state IDs by their workflow order
                    sorted_state_ids = sorted(result['time_in_states'].keys(),
                                            key=lambda sid: state_order.get(sid, 999))

                    for state_id in sorted_state_ids:
                        hours = result['time_in_states'][state_id]
                        state_name = state_map.get(state_id, f"Unknown State ({state_id})")
                        writer.writerow({
                            'StoryID': story_id,
                            'StoryName': story_name,
                            'StoryType': story_type,
                            'CurrentState': current_state,
                            'State': state_name,
                            'HoursSpent': round(hours, 2)
                        })
                else:
                    writer.writerow({
                        'StoryID': result['story_id'],
                        'StoryName': 'ERROR',
                        'StoryType': 'ERROR',
                        'CurrentState': 'ERROR',
                        'State': 'ERROR',
                        'HoursSpent': f"Error: {result.get('error', 'Unknown error')}"
                    })
        
        return csv_path
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """
        Print a summary of the analysis results.
        
        Args:
            results: Analysis results
        """
        print("\n" + "="*80)
        print("WORKFLOW TIME ANALYSIS SUMMARY")
        print("="*80)
        
        successful = [r for r in results if r.get('analysis_successful')]
        failed = [r for r in results if not r.get('analysis_successful')]
        
        print(f"Successfully analyzed: {len(successful)} stories")
        print(f"Failed to analyze: {len(failed)} stories")
        
        if failed:
            print("\nFailed stories:")
            for result in failed:
                print(f"  - Story {result['story_id']}: {result.get('error', 'Unknown error')}")
        
        print("\nDetailed Results:")
        print("-" * 80)
        
        for result in successful:
            print(f"\nStory {result['story_id']}: {result['story_name']}")
            print(f"Type: {result['story_type']} | Current State: {result['current_state']}")
            print(f"Workflow changes: {result['total_changes']}")
            
            if result['time_in_states']:
                print("Time in states:")
                total_hours = sum(result['time_in_states'].values())

                # Sort states by workflow order
                state_map = result.get('state_map', {})
                state_order = result.get('state_order', {})

                # Sort state IDs by their workflow order
                sorted_state_ids = sorted(result['time_in_states'].keys(),
                                        key=lambda sid: state_order.get(sid, 999))

                for state_id in sorted_state_ids:
                    hours = result['time_in_states'][state_id]
                    state_name = state_map.get(state_id, f"Unknown State ({state_id})")
                    percentage = (hours / total_hours * 100) if total_hours > 0 else 0
                    print(f"  - {state_name}: {hours:.2f} hours ({percentage:.1f}%)")
                print(f"Total time tracked: {total_hours:.2f} hours")
            else:
                print("No workflow state changes found.")


def read_story_ids_from_csv(csv_file_path: str) -> List[str]:
    """
    Read story IDs from a CSV file.

    Args:
        csv_file_path: Path to the CSV file

    Returns:
        List of story IDs as strings

    Raises:
        ValueError: If the CSV format is invalid or story ID column cannot be found
    """
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

            if not rows:
                raise ValueError("CSV file is empty")

            # Filter out empty rows
            rows = [row for row in rows if row and any(cell.strip() for cell in row)]

            if not rows:
                raise ValueError("CSV file contains no data")

            # Determine if there's a header by checking if first row looks like column names
            # For single column, check if the value is numeric (likely data) or text (likely header)
            # For multiple columns, check if we can find 'storyid' or 'story_id'
            first_row = rows[0]
            has_header = False
            column_index = 0

            if len(first_row) == 1:
                # Single column - check if first value looks like a header or is numeric
                first_value = first_row[0].strip().lower()
                # Consider it a header if it contains common header words and is not purely numeric
                if not first_value.isdigit() and any(word in first_value for word in ['story', 'id', 'number', 'ticket']):
                    has_header = True
                    data_rows = rows[1:]
                else:
                    data_rows = rows
                column_index = 0
            else:
                # Multiple columns - look for 'storyid' or 'story_id' in first row
                header_lower = [col.strip().lower() for col in first_row]
                column_index = None
                for idx, col_name in enumerate(header_lower):
                    if col_name in ['storyid', 'story_id']:
                        column_index = idx
                        has_header = True
                        break

                if column_index is None:
                    raise ValueError(
                        f"Could not find 'storyid' or 'story_id' column in CSV header. "
                        f"Found columns: {', '.join(first_row)}. "
                        f"Please ensure your CSV has a header row with a column named 'storyid' or 'story_id'."
                    )

                data_rows = rows[1:]

            # Extract story IDs
            story_ids = []
            for row in data_rows:
                if row and len(row) > column_index:
                    story_id = str(row[column_index]).strip()
                    if story_id:  # Skip empty values
                        story_ids.append(story_id)

            if not story_ids:
                raise ValueError("No story IDs found in CSV file")

            return story_ids

    except FileNotFoundError:
        raise ValueError(f"CSV file not found: {csv_file_path}")
    except csv.Error as e:
        raise ValueError(f"Error reading CSV file: {e}")


def main():
    """Main function to run the workflow time analysis."""
    parser = argparse.ArgumentParser(
        description='Analyze time spent by Shortcut stories in workflow states',
        epilog='Example: python time-spent-in-workflow-state.py 12345 67890 11111'
    )
    parser.add_argument('story_ids', nargs='*', help='Story IDs to analyze')
    parser.add_argument('--input-csv', metavar='FILE',
                       help='CSV file containing story IDs. If single column, that column is used; '
                            'if multiple columns, expects "storyid" or "story_id" column (case-insensitive)')
    parser.add_argument('--csv', help='Output CSV filename (optional)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed results for each story (default: show summary only)')
    parser.add_argument('--include-done-states', action='store_true',
                       help='Include time spent in "done" type workflow states (default: excluded)')

    args = parser.parse_args()

    # Validate input: either story_ids or --input-csv, but not both
    if args.input_csv and args.story_ids:
        parser.error("Cannot specify both story IDs as arguments and --input-csv. Use one or the other.")

    if not args.input_csv and not args.story_ids:
        parser.error("Must specify either story IDs as arguments or --input-csv")

    try:
        # Get story IDs from either command line or CSV file
        if args.input_csv:
            story_ids = read_story_ids_from_csv(args.input_csv)
        else:
            story_ids = args.story_ids

        analyzer = ShortcutWorkflowAnalyzer(include_done_states=args.include_done_states)
        results = analyzer.analyze_stories(story_ids)

        # Show detailed output if verbose flag is set
        if args.verbose:
            analyzer.print_summary(results)
        else:
            # Show brief summary by default
            successful = [r for r in results if r.get('analysis_successful')]
            failed = [r for r in results if not r.get('analysis_successful')]
            print(f"\nProcessed {len(results)} stories ({len(successful)} successful, {len(failed)} failed)")

        # Export to CSV
        csv_file = analyzer.export_to_csv(results, args.csv)
        print(f"Results exported to: {csv_file}")
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Make sure to set the SHORTCUT_API_TOKEN environment variable.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
