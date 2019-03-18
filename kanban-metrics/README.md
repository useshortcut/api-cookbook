These retrieve the average lead and cycle time for the specified Epic or Milestone and create a CSV in your Downloads folder.
The time for both lead and cycle time is displayed in seconds.

To use this script, open the script in a text editor. The script file will be in the folder where you downloaded the Cookbook repository.


To get the average lead and cycle time for an Epic, use epic_metrics.py.
Adjust the values on line 48 and 49 to reflect the name of the csv and the ID of the Epic
    `new_document_name = 'Epic_lead_cycle'
    epic_id = '38900'`
    
To get the average lead and cycle time for a Milestone, use milestone_metrics.py.
Adjust the values on line 49 and 50 to reflect the name of the csv and the ID of the Milestone    
    `new_document_name = 'Milestone_lead_cycle'
    milestone_id = '38900'`
    
When you've made your changes save the file.

To run the script, navigate to the folder for the script.
From the main Cookbook folder:
`cd kanban-metrics`

Make sure your virtual environment is active.
For Epics type:
`python epic_metrics.py` and press Return/Enter to run the script. 

For Milestones type:
`python milestone_metrics.py` and press Return/Enter to run the script. 

