#!/usr/bin/env python3

from db_table import db_table
import xlrd
import sys 

#
# Parses column and cell information of an agenda excel sheet into sqlite databases.
# The main table, "agenda" stores event information that is printed in lookup_agenda.py, while 
# the "speaker" and "event_speakers" tables store event speakers' inforation to allow for a 
# many-to-many relationship between the events and speakers.
# Run with: ./import_agenda.py agenda.xls (linux/mac) or python import_agenda.py agenda.xls (windows)
# 

EVENT_TABLE_NAME = "agenda"
SPEAKERS_TABLE_NAME = "speakers"
ASSOCIATIVE_TABLE_NAME = "event_speakers"

FILE = sys.argv[1]
EXCEL_COLUMNS = ["date", "time_start", "time_end", "session", "title", "location", "description", "speaker"]

# event's primary key is row # in excel sheet
# parent_id is field by default null, only updated to above row's id if current row is a subsession. 
EVENT_SCHEMA = {"date" : "text NOT NULL", "time_start" : "text NOT NULL", "time_end" : "text NOT NULL", "session" : "text NOT NULL",
              "title" : "text NOT NULL", "location" : "text", "description" : "text", "speaker" : "text",
               "id" : "Integer PRIMARY KEY", "parent_id" : "Integer NULL", "FOREIGN KEY (parent_id)" : "REFERENCES agenda(id)"}

# speaker's id = index in list of all speakers
SPEAKERS_SCHEMA = {"id" : "Integer PRIMARY KEY", "name" : "text NOT NULL"}

# use many-to-many table organization between events and speakers since one speaker can have multiple events and one event can have multiple speakers
EVENT_SPEAKERS_SCHEMA = {"event_id" : "Integer", "speaker_id" : "Integer", "PRIMARY KEY" : "(event_id, speaker_id)",
                         "FOREIGN KEY (event_id)" : "REFERENCES agenda(id)", "FOREIGN KEY (speaker_id)" : "REFERENCES speakers(id)"}

# parses data in excel file given in CLI argument to sqlite3 interview_test.db tables
def parse_sheet_to_db():
    # check that correct arg format passed in
    if (len(sys.argv) < 2):
        print("enter args in format ./import_agenda.py agenda.xls (linux/mac) or python import_agenda.py agenda.xls (windows)")
        return
    
    # create tables
    agenda = db_table(EVENT_TABLE_NAME, EVENT_SCHEMA)
    speakers = db_table(SPEAKERS_TABLE_NAME, SPEAKERS_SCHEMA)
    event_speakers = db_table(ASSOCIATIVE_TABLE_NAME, EVENT_SPEAKERS_SCHEMA)
    
    # open excel file
    workbook = xlrd.open_workbook(FILE)
    sheet = workbook.sheet_by_index(0)
    
    # parse data to table
    last_session_id = 0 # keep track of last logged session's id
    speaker_list = []
    for row_num in range(15, sheet.nrows):
        event_row_vals = {}
        event_id = row_num

        for column_index in range(len(EXCEL_COLUMNS)):
            cell_value = str(sheet.cell_value(row_num, column_index))

            if EXCEL_COLUMNS[column_index] == "speaker":
                if cell_value != '':
                    # create list of all unique speakers to keep track of speaker ID, add to speakers table
                    for speaker in cell_value.split("; "):
                        if speaker not in speaker_list:
                            speaker_list.append(speaker)
                            # insert new speaker into speakers table. Id determined by position in list (current size)
                            speakers.insert({"id" : len(speaker_list) - 1, "name" : f"{speaker}"})
                        # insert speaker-event pair into event_spearkers table
                        speaker_id = speaker_list.index(speaker)
                        event_speakers.insert({"event_id" : event_id, "speaker_id" : speaker_id})  

            if EXCEL_COLUMNS[column_index] == "session":
                if cell_value == 'Sub':
                    event_row_vals["parent_id"] = last_session_id # set parent_id to last session_id fo subsessions
                else:
                    last_session_id = event_id

            # log all cell data into 'agenda' table
            event_row_vals[EXCEL_COLUMNS[column_index]] = cell_value
        # set event_id 
        event_row_vals["id"] = event_id
        agenda.insert(event_row_vals)

    agenda.close()
    return 0

if __name__ == "__main__":
    parse_sheet_to_db()
