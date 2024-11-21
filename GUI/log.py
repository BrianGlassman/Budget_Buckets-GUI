# General imports
import dash


# Project imports
from Validation.Log import LogItem
import Categorize


# File format
item_keys = ['Imported', 'Account', 'Override', 'Final', 'My Category', 'E', 'Comment']
# First line is meta-header
meta_header = (
    ['Imported - Untouched from base'] + ['']*5 +
    ['Account'] +
    ['Override - Changes from base'] + ['']*5 +
    ['Final - Values with overrides, to be used for calculation'] + ['']*5 +
    ['My Category', 'E', 'Comment']
)
# Second line is section headers
section_header_template = ["Date", "Description", "Original Description", "Category", "Amount", "Status"]
section_headers = (
    [x+'_i' for x in section_header_template] +
    ['Account'] +
    [x+'_o' for x in section_header_template] +
    section_header_template +
    ['My Category', 'E', 'Comment']
)
# Only category and comment are editable
editable = [(key in Categorize.output_keys) for key in meta_header]

def Log(data: list[LogItem]):
    # --- Data ---
    table_data = []
    for item in data:
        # Not a comprehension because it's exploding the values
        row = []
        for key in item_keys:
            row.extend(item[key].values())
        table_data.append(dict((id, value) for id, value in zip(section_headers, row)))

    # --- Headers ---
    # First line is meta-header
    names = [[] for _ in meta_header]
    ids = ['' for _ in meta_header]
    for i, name in enumerate(meta_header):
        if name:
            # Update to new cell
            last = name
        else:
            # Re-use last cell
            name = last
        names[i].append(name)
    
    # Second line is section headers
    for i, name in enumerate(section_headers):
        names[i].append(name.replace('_i', '').replace('_o', ''))
        ids[i] = name

    # Turn lists into a single dict
    columns = [{'name': name, 'id': id, 'editable': edit} for name, id, edit in zip(names, ids, editable)]
    
    # --- Table ---
    table = dash.dash_table.DataTable(
        columns=columns,
        merge_duplicate_headers=True,
        style_header=dict(textAlign='center'),
        data=table_data,
        page_size=50,
        # page_action='none', # Can uncomment to show everything on one page, but then it gets pretty slow
    )

    # TODO Move this out and reference it, rather than defining here
    # TODO only works with the "one rule per transaction" system, won't work with general rules
    @dash.callback(
        dash.Input(table, 'data'),
        dash.State(table, 'data_previous'),
        prevent_initial_call=True,
    )
    def onChange(new_data, old_data):
        """Callback triggered when data in the table is changed"""
        changed_rows = [new_row for new_row, old_row in zip(new_data, old_data) if new_row != old_row]
        for row in changed_rows:
            rule = Categorize.rules[Categorize.make_key(row)]
            for key in Categorize.output_keys:
                if rule[key] == row[key]: continue
                # FIXME make sure category is valid (or just make it a dropdown instead of text)
                print(f"Changing {key}: {rule[key]} --> {row[key]}")
                rule[key] = row[key]

    return table

if __name__ == "__main__":
    # Data handling
    from Validation.Log import load_log_data
    data = load_log_data()

    # Dash
    app = dash.Dash(__name__)
    app.layout = dash.html.Div(Log(data))
    app.run(debug=False)
