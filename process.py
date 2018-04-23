import db
import cache
import parts
import sets
import csv

read_file_name = '/Users/josh/Downloads/ucs_atat_parts.csv'
write_file_name = '/Users/josh/Downloads/ucs_atat_parts_edited.csv'
edited_rows = []

with open(read_file_name) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        part = row['Part']
        color = int(row['Color'])
        print ("%s: %s" % (part, color))
        all_sets_with_part = sets.get_all_my_sets_containing_part(part, color)
        row['On Display'] = 0
        row['Says I have'] = 0
        for myset in all_sets_with_part:
            if myset.is_on_display():
                row['On Display'] += myset.quantity_owned
            else:
                row['Says I have'] += myset.quantity_owned

        edited_rows.append(row)

with open(write_file_name, 'wb') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=edited_rows[0].keys())
    writer.writeheader()
    writer.writerows(edited_rows)
