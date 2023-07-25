import panel as pn
pn.extension()
image_pane = pn.pane.PNG('https://openweathermap.org/img/wn/10d@4x.png',alt_text="éclaircie", max_width=400)
template = pn.Column(
    image_pane,
    pn.widgets.StaticText(value='<h2>Few clouds</h2>', align='center')
)
template.servable()