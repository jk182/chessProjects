from flask import Flask, render_template_string
import plotly.graph_objects as go
import plotly.express as px

app = Flask(__name__)


def create_plot():
    config = {'scrollZoom': True}
    data = {
            'accuracy': [94, 99, 97, 67, 90],
            'sharpness': [0.5, 0.1, 0.6, 1.2, 0.8],
            'rating': [2700, 2666, 2803, 2770, 2750]
            }
    fig = px.scatter(data, x='accuracy', y='sharpness', size='rating', title="sample figure")
    fig.update_layout(plot_bgcolor='#e6f7f2')
    return fig.to_html(full_html=False, config=config)


@app.route('/')
def home():
    plot_html = create_plot()
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>Interactive Plot</title>
        </head>
        <body>
            <div class="container">
                <h1 class="mt-5">Interactive Plotly Graph</h1>
                <div>{{ plot_html|safe }}</div>
            </div>
        </body>
        </html>
    ''', plot_html=plot_html)


if __name__ == '__main__':
    print(type(px.data.iris()))
    app.run(debug=True)
