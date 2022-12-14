import flet as ft
import asyncio
from mat.ble.bleak.cc26x2r import BleCC26X2


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
rue = loop.run_until_complete
lc = BleCC26X2()
lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)


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


progress_bar = ft.ProgressBar(
    color="amber",
    bgcolor="#eeeeee",
    expand=1,
    value=23,
    visible=False
)


dlg_file_downloaded = ft.AlertDialog(
    title=ft.Text('file downloaded!')
)
