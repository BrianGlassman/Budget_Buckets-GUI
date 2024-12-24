# General imports
import dash
from dash.dash_table import DataTable
from dataclasses import dataclass, field
import itertools


# Project imports
from BaseLib.CategoryList import categories
from Buckets import Types


# I would like to create multiple DataTables and combine them
# But apparently that makes it a huge pain to style correctly
# So do this instead
@dataclass
class DataTableMaker:
    columns: list[dict]
    '[List of Dicts of {"id": unique ID string, "name": [list of header entries]} for each column]'
    data: list[dict]
    '[List of Dicts of {"column id": column value} for each row]'
    # merge_duplicate_headers: bool # Always merge
    # style_header: dict # Force styling
    # page_action: str # Always use "none"
    tooltip_header: dict[str, str] = field(default_factory=dict)

    chain = itertools.chain.from_iterable

    @classmethod
    def combine(cls, *others: "DataTableMaker"):
        ret = DataTableMaker([], [], {})
        for i, o in enumerate(others):
            ret.columns.extend({'name': column['name'], 'id': f"{i}.{column['id']}"} for column in o.columns)

            data = [{f"{i}.{id}":val for id, val in d.items()} for d in o.data]
            if len(ret.data) == 0:
                ret.data = data
            else:
                assert len(ret.data) == len(data), f"Must have the same number of rows, got {len(ret.data)} and {len(data)}"
                for row_i in range(len(ret.data)):
                    ret.data[row_i].update(data[row_i])

            ret.tooltip_header.update({f"{i}.{id}": val for id, val in o.tooltip_header.items()})

        # Make sure multi-row headers are all the same depth
        header_depth = len(ret.columns[0]['name'])
        assert all(len(column['name']) == header_depth for column in ret.columns)

        return ret
    
    def make(self, fixed_columns: int):
        # Style to indicate a tooltip is present
        tt_indicator = {'textDecoration': 'underline', 'textDecorationStyle': 'dotted'}
        
        style_header = dict(textAlign='center')

        return DataTable(
            columns=self.columns,
            data = self.data,
            merge_duplicate_headers = True,
            style_header = style_header,
            style_header_conditional=[{
                'if': {
                    'header_index': len(self.columns[0]['name']) - 1, # Only apply to the last row of multi-row headers
                    'column_id': list(self.tooltip_header.keys())
                },
                **tt_indicator
            }],
            page_action = "none",
            tooltip_header = self.tooltip_header,
            # fixed_rows={'headers': True}, # FIXME this should just freeze the headers, but also squishes some columns
            fixed_columns={'headers': True, 'data': fixed_columns},
            style_table={'minWidth': '100%'},
        )

# File format
# Second row is descriptions
descriptions = (
    "Initial bucket value",
    "Transaction totals for this month",
    "Bucket value after transactions",
    "Bucket capacity",
    "Difference between bucket value and capacity",
    "Movement from buckets to slush fund",
    "Bucket values after removing slush funds",
    "Difference between bucket value and capacity after removing slush funds",
    "Which buckets are critical (fill first)",
    "Amount needed to fill critical buckets to full",
    "Bucket values after refilling critical buckets",
    "Amount needed to fill non-critical buckets to full",
    "Make sure Scaled avoids rounding problems",
    "NC To Fill, but limited by slush fund",
    "Bucket values after refilling non-critical buckets",
    "Final bucket values",
    "",
)
# Third row is header
header = (
    "Start",
    "Transactions",
    "After T",
    "Capacity",
    "Cap Diff",
    "Slush",
    "Before Fill",
    "S Cap Diff",
    "Is Crit",
    "Crit To Fill",
    "Crit Filled",
    "NC To Fill",
    "Pre Scale",
    "Scaled",
    "NC Filled",
    "Final",
    "Unfilled",
)


def Buckets(data: Types.BucketsFull):
    months = [make_month(*item) for item in data.months.items()]
    transitions = [make_transition(*item) for item in data.transitions.items()]

    # The category list at the far left
    category_table = make_categories()

    # Initial values
    initial_table = make_initial(data.initial)

    # Interleave Months and transitions
    mt_table = [val for pair in zip(months, transitions) for val in pair]

    # Combine all the components
    combined = DataTableMaker.combine(
        category_table,
        initial_table,
        *mt_table,
    )
    return combined.make(fixed_columns=len(category_table.columns))

def make_ValueCapacityCritical(data: Types.ValueCapacityCritical):
    header = [
        "Value",
        "Capacity",
        "Is Crit",
    ]

    table_data = [
        data.value.values(),
        data.capacity.values(),
        data.is_critical.values(),
    ]
    table_data = [
        dict((id, value) for id, value in zip(header, row))
        for row in zip(*table_data)
    ]

    # --- Table ---
    # Turn lists into a single dict
    columns = [{'name': h, 'id': h} for h in header]
    # Make the table
    table = DataTableMaker(
        columns=columns,
        data=table_data,
    )
    return table

def make_ChangeSet(data: Types.ChangeSet):
    header = [
        "Val Diff",
        "Set Val",
        "Cap Diff",
        "Set Cap",
        "Is Crit",
    ]

    # Only stores changes, so have to fill in empty spaces
    def fill_empty(values: dict):
        return {category:values.get(category, '') for category in categories}

    table_data = [
        data.value_delta,
        data.value_set,
        data.capacity_delta,
        data.capacity_set,
        data.crit_set,
    ]
    table_data = [fill_empty(dct).values() for dct in table_data]
    table_data = [
        dict((id, value) for id, value in zip(header, row))
        for row in zip(*table_data)
    ]

    # --- Table ---
    # Turn lists into a single dict
    columns = [{'name': h, 'id': h} for h in header]
    # Make the table
    table = DataTableMaker(
        columns=columns,
        data=table_data,
    )
    return table

def add_header(table: DataTableMaker, new_row):
    """Adds a new row to the header of the table"""
    columns = table.columns

    # Allow passing a string to fill an entire row
    if isinstance(new_row, str):
        new_row = [new_row] * len(columns)
    
    for new_item, column in zip(new_row, columns):
        column['name'] = [new_item, column['name']]


def make_transition(month: str, data: Types.TransitionFull):
    end_previous = make_ValueCapacityCritical(data.end_previous)
    add_header(end_previous, "Previous Month")

    changes = make_ChangeSet(data.changes)
    add_header(changes, "Changes")

    start_next = make_ValueCapacityCritical(data.start_next)
    add_header(start_next, "Result")

    return DataTableMaker.combine(
        end_previous,
        changes,
        start_next,
    )

def make_month(month: str, data: Types.MonthFull):
    table_data = [d.values() for d in data.columns.values()]
    table_data = [
        dict((id, value) for id, value in zip(header, row))
        for row in zip(*table_data)
    ]

    # First cell is the month itself (using the whole row because it looks better)
    m, d, y = month.split('/')
    month = f"{m}/{y}"
    top = [month] * len(header)

    names = list(zip(top, header))
    tooltips = {i:d for i, d in zip(header, descriptions)}
    # FIXME tooltips get applied to the top two lines of the three-line header

    # --- Table ---
    # Turn lists into a single dict
    columns = [{'name': name, 'id': id} for name, id in zip(names, header)]
    # Make the table
    table = DataTableMaker(
        columns=columns,
        tooltip_header=tooltips,
        data=table_data,
    )
    return table

def make_initial(initial: Types.ValueCapacityCritical):
    """The initial setup before the first month"""
    table = make_ValueCapacityCritical(initial)
    add_header(table, 'WARNING: Approximate values')
    return table

def make_categories():
    """The category list at the far left"""
    # TODO handle Dir, Broad, and Specific columns, not just Key (category)
    # names = ['Dir', 'Broad', 'Specific', 'Key']
    names = ['Key']
    ids = names.copy()
    names = [['', name] for name in names]

    table_data = []
    for cat in categories:
        row = ['']*(len(names) - 1) + [cat]
        table_data.append(dict((id, value) for id, value in zip(ids, row)))

    # --- Table ---
    # Turn lists into a single dict
    columns = [{'name': name, 'id': id} for name, id in zip(names, ids)]
    # Make the table
    table = DataTableMaker(
        columns=columns,
        data=table_data,
    )
    return table

def wrapper():
    """Wraps the GUI with appropriate data loading"""
    from Loading.ExcelToJSON.buckets import xls_to_json
    from Buckets import load_buckets_data
    xls_to_json()
    data = load_buckets_data()
    return Buckets(data)

if __name__ == "__main__":
    app = dash.Dash(__name__)
    app.layout = dash.html.Div(wrapper())
    app.run(debug=True)
