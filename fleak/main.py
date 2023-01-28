import os
import pathlib
import socket
import threading
import time
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
    progress_bar, \
    dlg_file_downloaded, \
    progress_bar_container
from fleak.settings.ctx import hook_ble_scan_simulated_loggers, hook_ble_hardcoded_mac_to_connect

PORT_PROGRESS_BAR = 56142


def _main(page: ft.Page):

    def _th_fxn_progress_bar_display():
        _sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sk.settimeout(.5)
        _sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _sk.bind(('127.0.0.1', PORT_PROGRESS_BAR))

        while 1:
            try:
                # -----------------------
                # receive orders via UDP
                # -----------------------
                _u, addr = _sk.recvfrom(1024)
                v = _u.split(b'/')

                # parse UDP frame sent by lowell-mat
                if v[0] == b'state_dds_ble_download_progress':
                    p = float(v[1].decode()) / 100
                    progress_bar.controls[1].value = p
                    page.update()

                # parse UDP frame same from this same app
                elif v[0] == b'bye_thread':
                    print('received: closing progress bar thread')
                    return

            except TimeoutError:
                pass

    # create thread
    th = threading.Thread(target=_th_fxn_progress_bar_display)
    th.start()

    # -----------------------------------------
    # PAGE dialogs and events
    # -----------------------------------------
    def _page_on_tab_close(_):
        try:
            # bye me and bye thread
            click_btn_disconnect(None)
            _sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            _sk.sendto(b'bye_thread', ('127.0.0.1', PORT_PROGRESS_BAR))
            print('sent: closing progress bar thread')
            page.window_destroy()

        except (Exception, ):
            # whatever, I don't care anymore
            pass

        finally:
            os._exit(0)

    def _page_on_error(e):
        print(e)

    page.on_disconnect = _page_on_tab_close
    page.on_error = _page_on_error
    page.title = "FLET Lowell Instruments BLE console"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def _page_show_dlg_file_downloaded(p):
        # this gets called at the end of BLE download
        page.dialog = dlg_file_downloaded
        dlg_file_downloaded.title = ft.Text('file downloaded OK!')
        dlg_file_downloaded.content = ft.Text('we left it in\n{}'.format(p))
        dlg_file_downloaded.open = True
        page.update()

    def _page_trace(s):
        lv.controls.append(ft.Text(str(s), size=20))
        page.update()
        print(str(s))

    def _t(s):
        _page_trace(s)

    # ----------------------------------------------------
    # PAGE icon GUI button clicks
    # ----------------------------------------------------

    def click_btn_scan(_):
        dd_loggers.value = ''
        dd_loggers.options = []
        page.update()
        rue(_ble_scan())

    def click_btn_cmd_dir(_):
        dd_files.value = ''
        dd_files.options = []
        page.update()
        rue(_ble_cmd_dir())

    def click_btn_connect(_):
        if hook_ble_scan_simulated_loggers:
            _t('detected simulation setting, forcing fake mac')
            m = '11:22:33:44:55:66'
            rue(_ble_connect(m))
            return

        hardcoded_mac = hook_ble_hardcoded_mac_to_connect
        if not dd_loggers.value and not hardcoded_mac:
            return
        if hardcoded_mac:
            _t('detected ARCHER laptop, forcing mac')
            m = hardcoded_mac
        else:
            _t('detected normal mac to connect')
            m = dd_loggers.value.split(' ')[0]
        rue(_ble_connect(m))

    def click_btn_disconnect(_): rue(_ble_disconnect())
    def click_btn_cmd_stp(_): rue(_ble_cmd_stp())
    def click_btn_cmd_led(_): rue(_ble_cmd_led())
    def click_btn_cmd_run(_): rue(_ble_cmd_run())
    def click_btn_cmd_gdo(_): rue(_ble_cmd_gdo())

    def click_btn_cmd_sts(_):

        # todo > maybe do this everywhere
        if not rue(_ble_is_connected()):
            return

        rue(_ble_cmd_sts())
        _t('logger datetime before sync')
        rue(_ble_cmd_gtm())
        rue(_ble_cmd_stm())
        _t('logger datetime after sync')
        rue(_ble_cmd_gtm())
        rue(_ble_cmd_gfv())
        rue(_ble_cmd_bat())

    def click_btn_cmd_mts(_):
        rue(_ble_cmd_mts())
        _t('refreshing file dropbox after dummy created')
        click_btn_cmd_dir(None)

    def click_bnt_cmd_download(_):
        if not dd_files.value:
            return
        rue(_ble_cmd_download(dd_files.value))

    def click_btn_cmd_delete(_):
        if not dd_files.value:
            return
        rue(_ble_cmd_delete(dd_files.value))
        _t('refreshing file dropbox after deletion')
        click_btn_cmd_dir(None)

    # -----------------
    # page HTML layout
    # -----------------

    page.add(

        ft.Row([
            ft.Column([
                dd_loggers,
                dd_files,
                progress_bar_container
            ], expand=1),

            ft.Column([
                lv
            ], expand=1)
        ], spacing=30, expand=8),

        ft.Row([
            ft.IconButton(
                ft.icons.SEARCH,
                on_click=click_btn_scan,
                icon_size=50, icon_color='black',
                tooltip='look for loggers'),
            ft.IconButton(
                ft.icons.BLUETOOTH_CONNECTED,
                on_click=click_btn_connect,
                icon_size=50, icon_color='lightblue',
                tooltip='connect to a logger'),
            ft.IconButton(
                ft.icons.BLUETOOTH_DISABLED,
                on_click=click_btn_disconnect,
                icon_size=50, icon_color='lightblue',
                tooltip='disconnect from a logger'),
            ft.IconButton(
                ft.icons.QUESTION_MARK,
                on_click=click_btn_cmd_sts,
                icon_size=50, icon_color='black',
                tooltip='query logger status'),
            ft.IconButton(
                ft.icons.STOP,
                on_click=click_btn_cmd_stp,
                icon_size=50, icon_color='red',
                tooltip='send STOP command to logger'),
            ft.IconButton(
                ft.icons.PLAY_ARROW,
                on_click=click_btn_cmd_run,
                icon_size=50, icon_color='green',
                tooltip='send RUN command to logger'),
            ft.IconButton(
                ft.icons.WORKSPACES_FILLED,
                on_click=click_btn_cmd_led,
                icon_size=50, icon_color='lightgreen',
                tooltip='make LED in logger blink'),
            ft.IconButton(
                ft.icons.LIST_ALT_OUTLINED,
                on_click=click_btn_cmd_dir,
                icon_size=50, icon_color='grey',
                tooltip='get list of files in a logger'),
            ft.IconButton(
                ft.icons.DOWNLOAD,
                on_click=click_bnt_cmd_download,
                icon_size=50, icon_color='black',
                tooltip='get file from logger'),
            ft.IconButton(
                ft.icons.DELETE,
                on_click=click_btn_cmd_delete,
                icon_size=50, icon_color='red',
                tooltip='delete file from logger'),
            ft.IconButton(
                ft.icons.FILE_UPLOAD,
                on_click=click_btn_cmd_mts,
                icon_size=50, icon_color='black',
                tooltip='create dummy file in logger'),
            ft.IconButton(
                ft.icons.BUBBLE_CHART_OUTLINED,
                on_click=click_btn_cmd_gdo,
                icon_size=50, icon_color='cyan',
                tooltip='do an oxygen measurement'),
        ], alignment=ft.MainAxisAlignment.CENTER, expand=1),
    )

    # ---------------------
    # Bluetooth functions
    # ---------------------

    async def _ble_scan():
        _det = []

        def _scan_cb(d: BLEDevice, _):
            logger_accepted_types = [
                'DO-2',
                'DO-1',
                'TAP'
            ]
            if d.name not in logger_accepted_types:
                return

            if d.name not in _det:
                _det.append(d.name)
                s = d.address + '   ' + d.name
                dd_loggers.options.append(ft.dropdown.Option(s))
                dd_loggers.value = s
                page.update()

        print('scanning...')
        try:
            if hook_ble_scan_simulated_loggers:
                s = '11:22:33:44:55:66   DO-2'
                dd_loggers.options.append(ft.dropdown.Option(s))
                dd_loggers.value = s
                page.update()
                return

            scanner = bleak.BleakScanner(_scan_cb, None)
            await scanner.start()
            await asyncio.sleep(1)
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
            _t('battery: {} mV'.format(rv[1]))

    async def _ble_cmd_gfv():
        rv = await lc.cmd_gfv()
        if rv[0] == 0:
            _t('firmware version: {}'.format(rv[1]))

    async def _ble_cmd_gtm():
        rv = await lc.cmd_gtm()
        if rv[0] == 0:
            _t('{}'.format(rv[1]))

    async def _ble_cmd_stm():
        rv = await lc.cmd_stm()
        if rv == 0:
            _t('logger time synced OK')

    async def _ble_cmd_dir():
        rv, ls = await lc.cmd_dir()
        if ls == 'error':
            _t('to list files, logger must be stopped')
            return
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

    async def _ble_cmd_gdo():
        rv = await lc.cmd_gdo()
        if not rv:
            _t('sensor DO error')
        else:
            _t(str(rv))

    async def _ble_cmd_run():
        rv = await lc.cmd_run()
        if rv == 0:
            _t('command RUN successful')

    async def _ble_cmd_mts():
        rv = await lc.cmd_mts()
        if rv == 0:
            _t('command MTS successful')

    async def _ble_cmd_sts():
        rv = await lc.cmd_sts()
        s = 'logger is currently {}'.format(rv[1])
        _t(s)

    async def _ble_is_connected():
        if not await lc.is_connected():
            _t('BLE is not connected')
            return
        return True

    async def _ble_cmd_download(file_to_dl):
        filename, _, size = file_to_dl.split()

        rv = await lc.cmd_dwg(filename)
        if rv != 0:
            _t('error DWG')
            return

        # -----------------------------
        # progress bar & download file
        # -----------------------------
        _t_dl = time.perf_counter()
        progress_bar.value = 0
        progress_bar.visible = True
        page.update()
        ip = '127.0.0.1'
        port = PORT_PROGRESS_BAR
        size = int(size)

        # internally, this sends UDP flags
        rv = await lc.cmd_dwl(size, ip, port)
        elapsed_time = time.perf_counter() - _t_dl
        speed = (size / elapsed_time) / 1000
        _t('speed {:.2f} KBps'.format(speed))
        progress_bar.visible = False
        page.update()

        # save file locally
        if rv[0] == 0:
            s = 'download complete {}, {} bytes'
            _t(s.format(filename, size))
            p = str(pathlib.Path.home())
            if hook_ble_scan_simulated_loggers:
                m = '11-22-33-44-55-66'
            else:
                m = lc.cli.address.replace(':', '-')

            p = p + '/Downloads/dl_fleak/{}'.format(m)
            os.makedirs(p, exist_ok=True)
            p = p + '/{}'.format(filename)
            with open(p, 'wb') as f:
                f.write(rv[1])
            _page_show_dlg_file_downloaded(p)

    async def _ble_cmd_delete(f):
        name, _, __ = f.split()
        rv = await lc.cmd_del(name)
        if rv == 0:
            _t('file {} deleted OK'.format(f))
        else:
            _t('error deleting file {}'.format(f))


# app can run from here OR setup.py entry point 'fleak'
def main():
    ft.app(target=_main)
    # ft.app(target=_main,  view=ft.WEB_BROWSER)


if __name__ == '__main__':
    main()
