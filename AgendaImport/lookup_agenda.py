#!/usr/bin/env python3

import sys
from db_table import db_table
from tabulate import tabulate 

#
# Outputs all events and respective event info that contain a given column and column value
# Also ouputs all subsessions with sessions matching the above requirements.
# Run with: ./lookup_agenda.py <COLUMN NAME> <VALUE>
# output looks best when terminal in full width.
#

COLUMN = sys.argv[1]
# make sure value input can contain spaces
VALUE  = " ".join(sys.argv[2:])
# table name consts
EVENT_TABLE_NAME = "agenda"
SPEAKERS_TABLE_NAME = "speakers"
ASSOCIATIVE_TABLE_NAME = "event_speakers"

# event's primary key is row # in excel sheet
EVENT_SCHEMA = {"date" : "text NOT NULL", "time_start" : "text NOT NULL", "time_end" : "text NOT NULL", "session" : "text NOT NULL",
              "title" : "text NOT NULL", "location" : "text", "description" : "text", "speaker" : "text",
               "id" : "Integer PRIMARY KEY"}

# speaker's id = index in list of all speakers
SPEAKERS_SCHEMA = {"id" : "Integer PRIMARY KEY", "name" : "text NOT NULL"}

# use many-to-many table organization between events and speakers since one speaker can have multiple events and one event can have mult. speakers
EVENT_SPEAKERS_SCHEMA = {"event_id" : "Integer", "speaker_id" : "Integer", "PRIMARY KEY" : "(event_id, speaker_id)",
                         "FOREIGN KEY (event_id)" : "REFERENCES agenda(id)", "FOREIGN KEY (speaker_id)" : "REFERENCES speakers(id)"}


# lookup in tables, assuming values have already been parsed in
def lookup():
    # check that correct arg format passed in
    if (len(sys.argv) < 3):
        print("enter args in format ./lookup_agenda.py <column> <value> (linux/mac) or ./import_agenda.py agenda.xls (linux/mac) or python import_agenda.py agenda.xls (windows)")
        return
    # create tables instances
    agenda = db_table(EVENT_TABLE_NAME, EVENT_SCHEMA)
    speakers = db_table(SPEAKERS_TABLE_NAME, SPEAKERS_SCHEMA)
    event_speakers = db_table(ASSOCIATIVE_TABLE_NAME, EVENT_SPEAKERS_SCHEMA)
    
    columns = []
    where = {}
    event_ids_dicts = [] 
    events = []
    # if searching for a specific speaker, find all event ids associated with that speaker
    if COLUMN == "speaker":
        # find speaker_id given name
        columns = ["id"]
        where = {"name" : VALUE}
        speaker_id_list_format = speakers.select(columns, where)
        if speaker_id_list_format:
            speaker_id = (speakers.select(columns, where)[0])["id"]
        else:
            # no speaker found
            print(f"no speaker named {VALUE} found \n")
            agenda.close()
            return
        # look up associated event IDs
        columns = ["event_id"]
        where = {"speaker_id" : speaker_id}
        event_ids_dicts = event_speakers.select(columns, where)
         
    else:
        # for all other column search queries, search for the column value and return event ids
        event_ids_dicts = agenda.select(columns=["id"], where={COLUMN: VALUE})

    # look up subsessions given the event id list
    event_ids = []
    for dict in event_ids_dicts:
        for id in dict.values():
            event_ids.append(id)

    for event_id in event_ids:
        # find event info
        where = {"id" : event_id}
        events += agenda.select(where=where)
        events += subsession_lookup(agenda, event_id)
    # do not display "id" header
    for row in events:
        del row["id"]  
    
    # if events are found, format and print them
    if events:
        # event(s) were found
        print(tabulate(events, headers="keys", tablefmt="simple", maxcolwidths=[10,10,10,10,20,20,50,20]))
    else:
        # no events were found
        print(f"no event with {COLUMN} of {VALUE} found \n")
    agenda.close()
    return

# helper method to search for a session's subsessions
def subsession_lookup(table: db_table, session_id):
    subsessions = []
    where = {"parent_id" : session_id}
    subsessions = table.select(where=where)
    return subsessions



if __name__ == "__main__":
    lookup()