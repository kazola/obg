import flet as ft
import asyncio

from obg.settings.ble.dev_core import BleOptodeCore
from obg.settings.ble.dev_mini import BleOptodeMini


PORT_PROGRESS_BAR = 56142

boc = BleOptodeCore()
bom = BleOptodeMini()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
ruc = loop.run_until_complete


dd_devs = ft.Dropdown(
    options=[],
    value='',
    expand=5,
    label='detected optode devices',
    hint_text='detected optode devices will appear here'
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
