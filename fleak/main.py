import flet as ft
import bleak
import asyncio
from bleak import BLEDevice, BleakError
import platform
from fleak.main_elements import \
    rue, \
    dd_loggers, \
    dd_files, \
    lv, \
    lc, \
    progress_bar, dlg_file_downloaded


def fleak_main(page: ft.Page):

    def open_dlg_file_downloaded():
        page.dialog = dlg_file_downloaded
        dlg_file_downloaded.open = True
        page.update()

    def _t(s):
        lv.controls.append(ft.Text(str(s), size=20))
        page.update()
        print(str(s))

    def gui_scan(_):
        dd_loggers.value = ''
        dd_loggers.options = []
        page.update()
        rue(_ble_scan())

    def gui_cmd_dir(_):
        dd_files.value = ''
        dd_files.options = []
        page.update()
        return rue(_ble_cmd_dir())

    def gui_connect(_):
        # if not dd_loggers.value:
        #     return

        m = dd_loggers.value.split(' ')[0]
        if platform.node() == 'ARCHER':
            print('epi')
            m = '60:77:71:22:C9:B3'
        rue(_ble_connect(m))

    def gui_disconnect(_): rue(_ble_disconnect())
    def gui_cmd_bat(_): return rue(_ble_cmd_bat())
    def gui_cmd_stp(_): return rue(_ble_cmd_stp())
    def gui_cmd_led(_): return rue(_ble_cmd_led())
    def gui_cmd_run(_): return rue(_ble_cmd_run())
    def gui_cmd_sts(_): return rue(_ble_cmd_sts())

    def gui_cmd_download(_):
        if not dd_files.value:
            return
        return rue(_ble_cmd_download(dd_files.value))

    page.title = "FLET Lowell Instruments BLE console"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.add(
        ft.Row([
            ft.Column([
                dd_loggers,
                dd_files,
                progress_bar
            ], expand=1),
            ft.Column([
                lv
            ], expand=1)
        ], spacing=30, expand=8),
        ft.Row([
            ft.IconButton(ft.icons.SEARCH, on_click=gui_scan,
                          icon_size=50, icon_color='black',
                          tooltip='look for loggers'),
            ft.IconButton(ft.icons.BLUETOOTH_CONNECTED, on_click=gui_connect,
                          icon_size=50, icon_color='lightblue',
                          tooltip='connect to a logger'),
            ft.IconButton(ft.icons.BLUETOOTH_DISABLED, on_click=gui_disconnect,
                          icon_size=50, icon_color='lightblue',
                          tooltip='disconnect from a logger'),
            ft.IconButton(ft.icons.QUESTION_MARK, on_click=gui_cmd_sts,
                          icon_size=50, icon_color='black',
                          tooltip='query logger status'),
            ft.IconButton(ft.icons.STOP, on_click=gui_cmd_stp,
                          icon_size=50, icon_color='red',
                          tooltip='send STOP command to logger'),
            ft.IconButton(ft.icons.PLAY_ARROW, on_click=gui_cmd_run,
                          icon_size=50, icon_color='green',
                          tooltip='send RUN command to logger'),
            ft.IconButton(ft.icons.LIST_ALT_OUTLINED, on_click=gui_cmd_dir,
                          icon_size=50, icon_color='grey',
                          tooltip='get list of files in a logger'),
            ft.IconButton(ft.icons.WORKSPACES_FILLED, on_click=gui_cmd_led,
                          icon_size=50, icon_color='lightgreen',
                          tooltip='make LED in logger blink'),
            ft.IconButton(ft.icons.BATTERY_FULL, on_click=gui_cmd_bat,
                          icon_size=50, icon_color='orange',
                          tooltip='get logger battery level'),
            ft.IconButton(ft.icons.DOWNLOAD, on_click=gui_cmd_download,
                          icon_size=50, icon_color='black',
                          tooltip='get file from logger'),
        ], alignment=ft.MainAxisAlignment.CENTER, expand=1),
    )

    async def _ble_scan():
        _det = []

        def _scan_cb(d: BLEDevice, _):
            if d.name not in _det:
                _det.append(d.name)
                s = d.address + '   ' + d.name
                dd_loggers.options.append(ft.dropdown.Option(s))
                dd_loggers.value = s
                page.update()

        print('scanning...')
        try:
            scanner = bleak.BleakScanner(_scan_cb, None)
            await scanner.start()
            await asyncio.sleep(5)
            await scanner.stop()

        except (asyncio.TimeoutError, BleakError, OSError) as ex:
            print(ex)

    async def _ble_connect(mac):
        _t('connecting to {}'.format(mac))
        rv = await lc.connect(mac)
        s = 'connected!' if rv == 0 else 'error connecting'
        _t(s)

    async def _ble_disconnect():
        await lc.disconnect()
        _t('disconnected')

    async def _ble_cmd_bat():
        rv = await lc.cmd_bat()
        if rv[0] == 0:
            _t('BAT: {} mV'.format(rv[1]))

    async def _ble_cmd_dir():
        rv, ls = await lc.cmd_dir()
        for filename, size in ls.items():
            v = filename + ' - ' + str(size)
            o = ft.dropdown.Option(v)
            dd_files.options.append(o)
            dd_files.value = v
            page.update()

    async def _ble_cmd_stp():
        rv = await lc.cmd_stp()
        if rv == 0:
            _t('command STOP successful')

    async def _ble_cmd_led():
        rv = await lc.cmd_led()
        if rv == 0:
            _t('command LED successful')

    async def _ble_cmd_run():
        rv = await lc.cmd_run()
        if rv == 0:
            _t('command RUN successful')

    async def _ble_cmd_sts():
        rv = await lc.cmd_sts()
        s = 'logger is currently {}'.format(rv[1])
        _t(s)

    async def _ble_cmd_download(file_to_dl):
        name, _, size = file_to_dl.split()
        size = int(size)
        rv = await lc.cmd_dwg(name)
        if rv != 0:
            _t('error DWG')
        rv = await lc.cmd_dwl(size)
        if rv[0] == 0:
            s = 'download complete {}, {} bytes'
            _t(s.format(name, size))
            with open('_dl_files/{}'.format(name), 'wb') as f:
                f.write(rv[1])
            open_dlg_file_downloaded()


def main():
    ft.app(target=fleak_main,  view=ft.WEB_BROWSER)


if __name__ == '__main__':
    main()
