import os
import subprocess as sp
import platform
import socket
import threading
import flet as ft
import bleak
import asyncio
from bleak import BLEDevice, BleakError
from obg.main_elements import \
    ruc, \
    dd_devs, \
    lv, \
    bom, boc, \
    progress_bar, \
    progress_bar_container, PORT_PROGRESS_BAR
from obg.settings.ctx import show_mini_commands


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

                # UDP frame incoming from somewhere else
                if v[0] == b'progress_bar_step':
                    p = float(v[1].decode()) / 100
                    progress_bar.controls[1].value = p
                    page.update()

                # UDP frame same from this same app
                elif v[0] == b'bye_thread':
                    print('received: closing progress bar thread')
                    return

            except (Exception, ):
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
    page.title = "Optode BLE GUI"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # def _page_show_dlg_file_downloaded(p):
    #     # this gets called at the end of BLE download
    #     page.dialog = dlg_file_downloaded
    #     dlg_file_downloaded.title = ft.Text('file downloaded OK!')
    #     dlg_file_downloaded.content = ft.Text('we left it in\n{}'.format(p))
    #     dlg_file_downloaded.open = True
    #     page.update()

    def _page_trace(s):
        lv.controls.append(ft.Text(str(s), size=20))
        page.update()
        print(str(s))

    def click_btn_clear_trace(_):
        lv.controls = []
        _t('cleared trace area')
        dd_devs.value = ''
        dd_devs.options = []
        _t('cleared scanned loggers dropdown')
        page.update()

    def _t(s):
        _page_trace(s)

    # ----------------------------------------------------
    # PAGE icon GUI button clicks
    # ----------------------------------------------------

    def _on_click_ensure_connected(func):
        def wrapper(*args):
            if not ruc(_ble_is_connected()):
                _t('BLE is not connected')
                return
            func(*args)
        return wrapper

    def click_btn_scan(_):
        dd_devs.value = ''
        dd_devs.options = []
        page.update()
        ruc(_ble_scan())

    def click_btn_connect(_):
        # if not dd_devs.value:
        #     return
        # m = dd_devs.value
        # todo: remove this hardcoded
        # m_op_mi = '4b:45:2d:e9:38:a0 op_mi_4b452de938a0'
        m_op_co = 'F0:BC:8C:34:15:14 op_co'
        m = m_op_co
        m = m.split(' ')[0]
        _t('connecting to mac {} chosen from dropdown'.format(m))
        ruc(_ble_connect(m))

    @_on_click_ensure_connected
    def click_btn_disconnect(_):
        ruc(_ble_disconnect())

    @_on_click_ensure_connected
    def click_btn_cmd_run(_):
        _t('sending cmd RUN')
        ruc(_ble_cmd_run())

    @_on_click_ensure_connected
    def click_btn_cmd_inc_time(_):
        _t('sending cmd INC_TIME')
        ruc(_ble_cmd_inc_time())

    @_on_click_ensure_connected
    def click_btn_cmd_query(_):
        _t('sending cmd STATUS')
        ruc(_ble_cmd_status())
        _t('sending cmd GET SCANNER MACS')
        ruc(_ble_cmd_macs())
        _t('sending cmd GET BATTERY LEVEL')
        ruc(_ble_cmd_battery())

    @_on_click_ensure_connected
    def click_btn_cmd_led_on(_):
        _t('sending cmd LED_ON')
        ruc(_ble_cmd_led_on())

    @_on_click_ensure_connected
    def click_btn_cmd_led_off(_):
        _t('sending cmd LED_OFF')
        ruc(_ble_cmd_led_off())

    @_on_click_ensure_connected
    def click_btn_cmd_motor_left(_):
        _t('sending cmd MOTOR_LEFT')
        ruc(_ble_cmd_motor_left())

    @_on_click_ensure_connected
    def click_btn_cmd_motor_right(_):
        _t('sending cmd MOTOR_RIGHT')
        ruc(_ble_cmd_motor_right())

    # -----------------
    # page HTML layout
    # -----------------

    page.add(

        ft.Row([
            ft.Column([
                dd_devs,
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
                tooltip='look for optode devices'),
            ft.IconButton(
                ft.icons.BLUETOOTH_CONNECTED,
                on_click=click_btn_connect,
                icon_size=50, icon_color='lightblue',
                tooltip='connect to a optode device'),
            ft.IconButton(
                ft.icons.BLUETOOTH_DISABLED,
                on_click=click_btn_disconnect,
                icon_size=50, icon_color='lightblue',
                tooltip='disconnect from optode device'),
        ], alignment=ft.MainAxisAlignment.CENTER, expand=1),
        ft.Row([
            ft.Text(
                "core",
                size=50,
                color=ft.colors.BLACK,
                bgcolor=None,
                weight=ft.FontWeight.NORMAL,
            ),
            ft.IconButton(
                ft.icons.QUESTION_MARK,
                on_click=click_btn_cmd_query,
                icon_size=50,
                icon_color='black',
                tooltip='get status'),
            ft.IconButton(
                ft.icons.FLASHLIGHT_ON,
                on_click=click_btn_cmd_led_on,
                icon_size=50,
                icon_color='black',
                tooltip='led ON'),
            ft.IconButton(
                ft.icons.FLASHLIGHT_OFF,
                on_click=click_btn_cmd_led_off,
                icon_size=50,
                icon_color='black',
                tooltip='led OFF'),
            ft.IconButton(
                ft.icons.KEYBOARD_ARROW_LEFT,
                on_click=click_btn_cmd_motor_left,
                icon_size=50,
                icon_color='black',
                tooltip='motor left'),
            ft.IconButton(
                ft.icons.KEYBOARD_ARROW_RIGHT,
                on_click=click_btn_cmd_motor_right,
                icon_size=50,
                icon_color='black',
                tooltip='motor right'),
            ft.IconButton(
                ft.icons.MORE_TIME,
                on_click=click_btn_cmd_inc_time,
                icon_size=50,
                icon_color='black',
                tooltip='increase time'),
            ft.IconButton(
                ft.icons.PLAY_ARROW,
                on_click=click_btn_cmd_run,
                icon_size=50,
                icon_color='green',
                tooltip='run'),
        ], alignment=ft.MainAxisAlignment.CENTER, expand=1)
    )

    if show_mini_commands:
        page.add(
            ft.Row([
                ft.Text(
                    "mini",
                    size=50,
                    color=ft.colors.BLACK,
                    bgcolor=None,
                    weight=ft.FontWeight.NORMAL,
                ),
                # ft.IconButton(
                #     ft.icons.LIGHTBULB,
                #     on_click=click_btn_cmd_led,
                #     icon_size=50,
                #     icon_color='orange',
                #     tooltip='blink leds'),
            ], alignment=ft.MainAxisAlignment.CENTER, expand=1)
        )

    # ---------------------
    # Bluetooth functions
    # ---------------------

    async def _ble_scan():
        _det = []

        def _scan_cb(d: BLEDevice, _):
            if d.address in _det:
                return
            if not d.name.startswith('op_'):
                return

            _det.append(d.address)
            s = d.address + '   ' + d.name
            dd_devs.options.append(ft.dropdown.Option(s))
            dd_devs.value = s
            page.update()

        _t('scanning for nearby optode devices...')
        try:
            scanner = bleak.BleakScanner(_scan_cb, None)
            await scanner.start()
            await asyncio.sleep(3)
            await scanner.stop()
            _t('scan complete')

        except (asyncio.TimeoutError, BleakError, OSError) as ex:
            print(ex)

    async def _ble_connect(mac):
        _t('connecting to {}'.format(mac))
        rv = await boc.connect(mac)
        s = 'connected!' if rv == 0 else 'error connecting'
        _t(s)

    async def _ble_disconnect():
        await boc.disconnect()
        _t('disconnected')
        if platform.system() == 'Linux':
            c = 'bluetoothctl -- disconnect'
            sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)

    async def _ble_cmd_run():
        rv = await boc.cmd_run()
        if rv == 0:
            _t('    OK cmd RUN')
        else:
            _t('    error cmd RUN')

    async def _ble_cmd_inc_time():
        rv = await boc.cmd_inc_time()
        if rv == 0:
            _t('    OK cmd INC_TIME')
        else:
            _t('    error cmd INC_TIME')

    async def _ble_cmd_status():
        rv, v = await boc.cmd_status()
        if rv == 0:
            _t('    OK cmd STATUS {}'.format(v))
        else:
            _t('    error cmd STATUS')

    async def _ble_cmd_macs():
        rv, v = await boc.cmd_macs()
        if rv == 0:
            _t('    OK cmd MAC {}'.format(v))
        else:
            _t('    error cmd MAC')

    async def _ble_cmd_battery():
        rv, v = await boc.cmd_battery()
        if rv == 0:
            _t('    OK cmd BATTERY {}'.format(v))
        else:
            _t('    error cmd BATTERY')

    async def _ble_cmd_led_on():
        rv = await boc.cmd_led_on()
        if rv == 0:
            _t('    OK cmd LED_ON')
        else:
            _t('    error cmd LED_ON')

    async def _ble_cmd_led_off():
        rv = await boc.cmd_led_off()
        if rv == 0:
            _t('    OK cmd LED_OFF')
        else:
            _t('    error cmd LED_OFF')

    async def _ble_cmd_motor_left():
        rv = await boc.cmd_motor_left()
        print(rv, v)
        if rv == 0:
            _t('    OK cmd MOTOR_LEFT')
        else:
            _t('    error cmd MOTOR_LEFT')

    async def _ble_cmd_motor_right():
        rv = await boc.cmd_motor_right()
        if rv == 0:
            _t('    OK cmd MOTOR_RIGHT')
        else:
            _t('    error cmd MOTOR_RIGHT')

    async def _ble_is_connected():
        return await boc.is_connected()


# app can run from here OR setup.py entry point 'fleak'
def main():
    # ft.app(target=_main)
    ft.app(target=_main, view=ft.WEB_BROWSER)


if __name__ == '__main__':
    main()
