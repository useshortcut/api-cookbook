These retrieve the average lead and cycle time for the specified Epic or Milestone and create a CSV in your Downloads folder.

To get the average lead and cycle time for an Epic, use epic_metrics.py.
Adjust the values on line 48 and 49 to reflect the name of the csv and the ID of the Epic
    new_document_name = 'Epic_lead_cycle'
    epic_id = '38900'
    
To get the average lead and cycle time for a Milestone, use milestone_metrics.py.
Adjust the values on line 49 and 50 to reflect the name of the csv and the ID of the Milestone    
    new_document_name = 'Milestone_lead_cycle'
    milestone_id = '38900'