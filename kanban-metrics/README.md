These retrieve the average lead and cycle time for the specified Epic or Objective and create a CSV in your Downloads folder.
The time for both lead and cycle time is displayed in seconds.

To use these scripts:
Make sure your virtual environment is active.`source cookbook/bin/activate` for Mac and `cookbook\Scripts\activate` for Windows.

**Objective Lead and Cycle time**

To fetch the lead and cycle time for a specific Objective, type `python objective_metrics.py` and press Return/Enter to run the script.

You'll be asked to enter the name for the export file and the ID for the Objective. When the script has finished running, you'll see a message that your file is available in your Downloads folder.

**Epic Lead and Cycle time**

To fetch the lead and cycle time for a specific Epic, type `python epic_metrics.py` and press Return/Enter to run the script.

You'll be asked to enter the name for the export file and the ID for the Epic. When the script has finished running, you'll see a message that your file is available in your Downloads folder.

---

You might consider adjusting these scripts to use a list of Epic or Objective IDs. Other example scripts in this Cookbook loop through Story IDs - those may be good examples for determining how to loop through a list of IDs and make a Get request for each ID in the list.
