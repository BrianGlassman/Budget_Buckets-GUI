# General imports
import dash


# Project imports
from BaseLib.CategoryList import categories


# File format
item_keys = ['start', 'end', 'data']
log_starts = {'2023': '9/1/2023', '2024': '1/1/2024'}
header = ['Start', 'End'] + categories + ['Total']

def Aggregate(data: list):
    # --- Data ---
    table_data = []
    for item in data:
        row = []
        for key in item_keys:
            val = item[key]
            if isinstance(val, dict):
                row.extend(val.values())
            else:
                row.append(val)
        table_data.append(dict((id, value) for id, value in zip(header, row)))

    # --- Headers ---
    # First line is meta-header
    meta_header = ['Log Start', '', list(log_starts.values())[-1]]
    meta_header += [''] * (len(header) - len(meta_header))
    names = [[x] for x in meta_header]
    ids = ['' for _ in meta_header]

    # Second line is true header
    for i, h in enumerate(header):
        names[i].append(h)
        ids[i] = h

    # Turn lists into a single dict
    columns = [{'name': name, 'id': id} for name, id in zip(names, ids)]
    
    # --- Table ---
    table = dash.dash_table.DataTable(
        columns=columns,
        merge_duplicate_headers=False,
        data=table_data,
        page_size=50,
        # page_action='none', # Can uncomment to show everything on one page, but then it gets pretty slow
    )
    return table

def wrapper():
    """Wraps the GUI with appropriate data loading"""
    from Loading.ExcelToJSON.aggregate import xls_to_json
    from Aggregate import load_aggregate_data
    xls_to_json()
    data = load_aggregate_data()
    return Aggregate(data)

if __name__ == "__main__":
    app = dash.Dash(__name__)
    app.layout = dash.html.Div(wrapper())
    app.run(debug=False)
