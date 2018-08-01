import re


def get_org_table_as_json(org_file, table_name):
    lines = get_org_table_lines_by_name(org_file, table_name)
    return parse_org_table(lines)


def get_org_table_lines_by_name(org_file, table_name):
    with open(org_file, 'r') as f:
        lines = f.read().strip().splitlines()

    table_lines = []
    in_table = False
    for n, line in enumerate(lines):
        if line.startswith('#+NAME: tab:' + table_name):
            in_table = True
            continue
        if in_table and not line.startswith('|'):
            in_table = False
            break

        if in_table:
            table_lines.append(line)

    return table_lines


# import_from_orgtable.py
def parse_org_table(lines):
    """parse org table to a list of dicts like [{header1: value1, header2: value2, ...}, ...]"""
    header_fields = {}
    rows = []
    for line in lines:
        # skip extraneous lines
        if not line or not line[0] == '|' or line[1] == '-':
            continue

        # skip width-limiting lines
        if re.search('<[0-9]*>', line):
            continue

        # get header row
        fields = line.split('|')[1:-1]  # remove first and last, empty elements
        fields = [field.strip() for field in fields]
        if not header_fields:
            header_fields = fields
            continue

        # parse entry lines
        row = {k: v for k, v in zip(header_fields, fields)}
        row['_raw'] = line
        rows.append(row)

    return rows
