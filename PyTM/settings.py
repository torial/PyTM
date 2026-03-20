import os

data_foldername = "pytm"
data_filename = "data.json"
state_filename = "state.json"
invoices_filename = "invoices.json"
archive_filename = "archive.json"
# make data folder hidden in the home directory
data_folder = os.path.expanduser(f"~/.{data_foldername}")
data_filepath = os.path.join(data_folder, data_filename)
state_filepath = os.path.join(data_folder, state_filename)
invoices_filepath = os.path.join(data_folder, invoices_filename)
archive_filepath = os.path.join(data_folder, archive_filename)

STARTED = "running"
STOPPED = "stopped"
FINISHED = "finished"
PAUSED = "paused"
ABORTED = "aborted"

# State keys
CURRENT_PROJECT = "current_project"
CURRENT_TASK = "current_task"

# Words that should be fully uppercased in invoice task name formatting
ACRONYMS = {"LLM", "RAG"}

# Incremented whenever the schema of any pytm data file changes in a
# backwards-incompatible way. Stored as "_schema_version" in every JSON file.
SCHEMA_VERSION = 1
