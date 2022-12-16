import flet as ft
import asyncio
from mat.ble.bleak.cc26x2r import BleCC26X2


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
lc = BleCC26X2(dbg_ans=False)
lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
rue = loop.run_until_complete


dd_loggers = ft.Dropdown(
    options=[],
    value='',
    expand=5,
    label='detected loggers',
    hint_text='detected loggers will be shown here'
)


dd_files = ft.Dropdown(
    options=[],
    value='',
    expand=5,
    label='list of files in a logger',
    hint_text='files inside a logger will be shown here'
)


progress_bar = ft.Row([
    ft.Text('file download progress'),
    ft.ProgressBar(
        color="lightblue",
        bgcolor="#eeeeee",
        value=0,
        bar_height=10,
        tooltip='downloading your file :)',
        expand=1
    )
], visible=False, expand=1)


progress_bar_container = ft.Container(
    content=progress_bar,
    alignment=ft.alignment.center_right,
    expand=1
)


dlg_file_downloaded = ft.AlertDialog(
    title=ft.Text(''),
    content=ft.Text('')
)
