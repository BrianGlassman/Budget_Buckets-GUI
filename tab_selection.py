# Generat imports
from dash import Dash, html, Output, Input
from functools import partial


# Project imports
import GUI


def main():
    app = Dash(__name__)
    
    # FIXME what's the point of this?
    def discard_args(func, *_):
        return func()

    output = html.Section(html.Div("Select a tab to begin"), id='Output')

    # Define the "tabs"
    buttons = []
    for tag, callback in (
        ('Log', GUI.log.wrapper),
        ('Aggregate', GUI.aggregate.wrapper),
        ('Buckets', GUI.buckets.wrapper),
    ):
        button = html.Button(tag, id=tag)
        buttons.append(button)
        
        # Add the arguments to the callback and wrap it to discard the Input
        callback = partial(discard_args, callback)

        app.callback(Output(output, 'children', allow_duplicate=True), Input(button, 'n_clicks'), prevent_initial_call=True)(callback)

    app.layout = html.Div([
        html.Section(buttons, id='Buttons'),
        output,
    ])

    app.run(debug=True)

if __name__ == "__main__":
    main()
