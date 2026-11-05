import csv
import io

def spreadsheet_cell(value):
    return "\t" + value if value and value[0] in "=+-@" else value

output = io.StringIO()
writer = csv.writer(output, lineterminator="\n", quoting=csv.QUOTE_ALL)
writer.writerow([spreadsheet_cell("=47+1"), spreadsheet_cell("safe-label")])
print(repr(output.getvalue()))
