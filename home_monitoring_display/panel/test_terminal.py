import panel as pn 



terminal = pn.widgets.Terminal(
    "Welcome to the Panel Terminal!\nI'm based on xterm.js\n\n",
    options={"cursorBlink": True},
    height=300, sizing_mode='stretch_width'
)
terminal.subprocess.run("bash")

run_ls = pn.widgets.Button(name="Run ls", button_type="success")
# run_ls.on_click(
#     lambda x: terminal.subprocess.run("ls", "-l")
# )
dashboard = pn.Column(run_ls, terminal, sizing_mode='stretch_both')

dashboard.servable()