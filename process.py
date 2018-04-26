import db
import cache
import parts
import sets
import csv

read_file_name = '/Users/josh/Downloads/ucs_atat_parts.csv'
write_file_name = '/Users/josh/Downloads/ucs_atat_parts_edited.csv'
edited_rows = []

all_parts = parts.get_all_for_sets(sets.get_all_my_sets())['parts']

print(len(all_parts))

with open(read_file_name) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        part_num = row['Part']
        color_num = row['Color']
        row['On Display'] = 0
        row['Says I have'] = 0
        if part_num in all_parts:
            part = all_parts[part_num]
            if color_num in part['colors']:
                color = part['colors'][color_num]
                print("part: %s, color: %s, display: %s, storage: %s" % (part_num, color, color['display'], color['storage']))
                row['On Display'] = color['display']
                row['Says I have'] = color['storage']
            else:
                print("no color %s for part %s" % (color, part_num))
        else:
            print("no part %s" % part_num)

        edited_rows.append(row)

with open(write_file_name, 'wb') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=edited_rows[0].keys())
    writer.writeheader()
    writer.writerows(edited_rows)
