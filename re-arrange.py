import pandas as pd

file_names = ['la_liga_teams']
for name in file_names:
    df = pd.read_csv('csv_files/' + name)
    pass