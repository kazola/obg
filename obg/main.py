import os
import socket
import threading
import flet as ft
import bleak
import asyncio
from bleak import BLEDevice, BleakError
from obg.ble.utils import restart_bluetooth_service
from obg.main_elements import \
    ruc, \
    dd_devs, \
    lv, \
    bom, boc, \
    progress_bar, \
    progress_bar_container, PORT_PROGRESS_BAR
from obg.settings.ctx import show_core_commands, show_mini_commands, \
    chosen_mac_hc

# bdc: Bluetooth device controller, can be core or mini
g_bdc_type = ''
g_scanning = False


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
        dd_devs.value = ''
        dd_devs.options = []
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

    def _on_click_ensure_mini(func):
        def wrapper(*args):
            if not g_bdc_type == 'op_mi':
                return
            func(*args)
        return wrapper

    def _on_click_ensure_core(func):
        def wrapper(*args):
            if not g_bdc_type == 'op_co':
                return
            func(*args)
        return wrapper

    def click_btn_scan(_):
        dd_devs.value = ''
        dd_devs.options = []
        page.update()
        global g_scanning
        g_scanning = True
        ruc(_ble_scan())
        g_scanning = False

    def click_btn_connect(_):

        if g_scanning:
            _t('BLE is currently scanning')
            return

        if ruc(_ble_is_connected()):
            _t('BLE is already connected')
            return

        if not dd_devs.value and not chosen_mac_hc:
            return

        # priority: first hardcoded, second dropdown
        m = dd_devs.value
        if chosen_mac_hc:
            m = chosen_mac_hc

        global g_bdc_type
        g_bdc_type = 'op_mi' if 'op_mi' in m else 'op_co'
        m = m.split(' ')[0]
        ruc(_ble_connect(m))

    @_on_click_ensure_connected
    def click_btn_disconnect(_):
        ruc(_ble_disconnect())

    @_on_click_ensure_connected
    @_on_click_ensure_core
    def click_btn_cmd_run(_):
        _t('sending cmd RUN')
        ruc(_ble_cmd_run())

    @_on_click_ensure_connected
    @_on_click_ensure_core
    def click_btn_cmd_dl(_):
        _t('sending cmd DL')
        ruc(_ble_cmd_dl())

    @_on_click_ensure_connected
    @_on_click_ensure_core
    def click_btn_cmd_inc_time(_):
        _t('sending cmd INC_TIME')
        ruc(_ble_cmd_inc_time())

    @_on_click_ensure_connected
    @_on_click_ensure_core
    def click_btn_cmd_query(_):
        _t('sending cmd STATUS')
        ruc(_ble_cmd_status())
        _t('sending cmd GET SCANNER MACS')
        ruc(_ble_cmd_macs())
        _t('sending cmd GET BATTERY LEVEL')
        ruc(_ble_cmd_battery())

    @_on_click_ensure_connected
    @_on_click_ensure_core
    def click_btn_cmd_led_on(_):
        _t('sending cmd LED_ON')
        ruc(_ble_cmd_led_on())

    @_on_click_ensure_connected
    @_on_click_ensure_core
    def click_btn_cmd_led_off(_):
        _t('sending cmd LED_OFF')
        ruc(_ble_cmd_led_off())

    @_on_click_ensure_connected
    @_on_click_ensure_core
    def click_btn_cmd_motor_left(_):
        _t('sending cmd MOTOR_LEFT')
        ruc(_ble_cmd_motor_left())

    @_on_click_ensure_connected
    @_on_click_ensure_core
    def click_btn_cmd_motor_right(_):
        _t('sending cmd MOTOR_RIGHT')
        ruc(_ble_cmd_motor_right())

    @_on_click_ensure_connected
    @_on_click_ensure_core
    def click_btn_cmd_limit_left(_):
        _t('sending cmd LIMIT_LEFT')
        ruc(_ble_cmd_limit_left())

    @_on_click_ensure_connected
    @_on_click_ensure_core
    def click_btn_cmd_limit_right(_):
        _t('sending cmd LIMIT_RIGHT')
        ruc(_ble_cmd_limit_right())

    @_on_click_ensure_connected
    @_on_click_ensure_mini
    def click_btn_cmd_mini_display_in(_):
        _t('sending cmd DISPLAY_IN')
        ruc(_ble_cmd_mini_display_in())

    @_on_click_ensure_connected
    @_on_click_ensure_mini
    def click_btn_cmd_mini_display_out(_):
        _t('sending cmd DISPLAY_OUT')
        ruc(_ble_cmd_mini_display_out())

    @_on_click_ensure_connected
    @_on_click_ensure_mini
    def click_btn_cmd_mini_display_wheel(_):
        _t('sending cmd DISPLAY_WH')
        ruc(_ble_cmd_mini_display_wh())

    @_on_click_ensure_connected
    @_on_click_ensure_mini
    def click_btn_cmd_mini_wifi_in(_):
        _t('sending cmd WIFI_IN')
        ruc(_ble_cmd_mini_wifi_in())

    @_on_click_ensure_connected
    @_on_click_ensure_mini
    def click_btn_cmd_mini_wifi_out(_):
        _t('sending cmd WIFI_OUT')
        ruc(_ble_cmd_mini_wifi_out())

    @_on_click_ensure_connected
    @_on_click_ensure_mini
    def click_btn_cmd_mini_leds(_):
        _t('sending cmd LEDS')
        ruc(_ble_cmd_leds())

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
                icon_size=50,
                icon_color='black',
                tooltip='look for optode devices'),
            ft.IconButton(
                ft.icons.BLUETOOTH_CONNECTED,
                on_click=click_btn_connect,
                icon_size=50,
                icon_color='lightblue',
                tooltip='connect to a optode device'),
            ft.IconButton(
                ft.icons.BLUETOOTH_DISABLED,
                on_click=click_btn_disconnect,
                icon_size=50,
                icon_color='lightblue',
                tooltip='disconnect from optode device'),
            ft.IconButton(
                ft.icons.DELETE,
                on_click=click_btn_clear_trace,
                icon_size=50,
                icon_color='red',
                tooltip='clear trace'),
        ], alignment=ft.MainAxisAlignment.CENTER, expand=1),
    )

    if show_core_commands:
        page.add(
            ft.Row([
                ft.Text(
                    "core ",
                    size=50,
                    color=ft.colors.BLACK,
                    weight=ft.FontWeight.BOLD,
                    overflow=ft.TextOverflow.VISIBLE,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.ElevatedButton(
                    content=ft.Text(value="get status", size=20),
                    tooltip='get core info',
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_query),
                ft.ElevatedButton(
                    content=ft.Text(value="led strip ON", size=20),
                    tooltip='turn LED strip ON',
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_led_on),
                ft.ElevatedButton(
                    content=ft.Text(value="led strip OFF", size=20),
                    tooltip='turn LED strip OFF',
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_led_off),
                ft.ElevatedButton(
                    content=ft.Text(value="motor left", size=20),
                    tooltip='move motor left',
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_motor_left),
                ft.ElevatedButton(
                    content=ft.Text(value="motor right", size=20),
                    tooltip='move motor right',
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_motor_right),
                ft.ElevatedButton(
                    content=ft.Text(value="limit left", size=20),
                    tooltip='test motor limit left',
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_limit_left),
                ft.ElevatedButton(
                    content=ft.Text(value="limit right", size=20),
                    tooltip='test motor limit right',
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_limit_right),
                # # todo: do this increase interval command in firmware
                # ft.ElevatedButton(
                #     content=ft.Text(value="increase interval", size=20),
                #     color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                #     on_click=click_btn_cmd_inc_time),
                ft.ElevatedButton(
                    content=ft.Text(value="run", size=20),
                    tooltip='go to run mode',
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_run),
                # ft.ElevatedButton(
                #     content=ft.Text(value="download", size=20),
                #     tooltip = 'go to download mode',
                #     color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                #     on_click=click_btn_cmd_dl),
            ], alignment=ft.MainAxisAlignment.CENTER, expand=1)
        )

    if show_mini_commands:
        page.add(
            ft.Row([
                ft.Text(
                    "mini ",
                    size=50,
                    color=ft.colors.BLACK,
                    weight=ft.FontWeight.BOLD),
                ft.ElevatedButton(
                    content=ft.Text(value="act display", size=20),
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_mini_display_out),
                ft.ElevatedButton(
                    content=ft.Text(value="read display", size=20),
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_mini_display_in),
                ft.ElevatedButton(
                    content=ft.Text(value="act wheel", size=20),
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_mini_display_wheel),
                ft.ElevatedButton(
                    content=ft.Text(value="act wifi", size=20),
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_mini_wifi_out),
                ft.ElevatedButton(
                    content=ft.Text(value="read wifi", size=20),
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_mini_wifi_in),
                ft.ElevatedButton(
                    content=ft.Text(value="act mini LED", size=20),
                    color=ft.colors.BLACK, bgcolor=ft.colors.LIGHT_BLUE,
                    on_click=click_btn_cmd_mini_leds),
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
            if not d.name:
                return

            # grabs either "op_co" or "op_mi", or "op_" for both
            if not d.name.startswith('op_co_'):
                return

            _t('found {} -> {}'.format(d.name, d.address))
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
        if g_bdc_type == 'op_mi':
            rv = await bom.connect(mac)
        else:
            rv = await boc.connect(mac)
        if rv == 0:
            _t('    connected to {}'.format(g_bdc_type))
        else:
            _t('    error connecting')

    async def _ble_disconnect():
        if g_bdc_type == 'op_mi':
            await bom.disconnect()
        else:
            await boc.disconnect()
        _t('disconnected')

    async def _ble_cmd_run():
        rv = await boc.cmd_run()
        if rv == 0:
            _t('    OK cmd RUN')
        else:
            _t('    error cmd RUN')

    async def _ble_cmd_dl():
        rv = await boc.cmd_dl()
        if rv == 0:
            _t('    OK cmd DL')
        else:
            _t('    error cmd DL')

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

    async def _ble_cmd_limit_left():
        rv, v = await boc.cmd_limit_left()
        if rv == 0:
            _t('    OK cmd LIMIT_LEFT is {}'.format(v))
        else:
            _t('    error cmd LIMIT_LEFT')

    async def _ble_cmd_limit_right():
        rv, v = await boc.cmd_limit_right()
        if rv == 0:
            _t(' OK cmd LIMIT_RIGHT is {}'.format(v))
        else:
            _t('    error cmd LIMIT_RIGHT')

    async def _ble_cmd_mini_display_in():
        rv, v = await bom.cmd_display_in()
        if rv == 0:
            _t('    cmd DISPLAY_IN {}'.format(v))
        else:
            _t('    error cmd DISPLAY_IN')

    async def _ble_cmd_mini_display_out():
        rv = await bom.cmd_display_out()
        if rv == 0:
            _t('    OK cmd DISPLAY_OUT')
        else:
            _t('    error cmd DISPLAY_OUT')

    async def _ble_cmd_mini_display_wh():
        rv = await bom.cmd_display_wh()
        if rv == 0:
            _t('    OK cmd DISPLAY_WH')
        else:
            _t('    error cmd DISPLAY_WH')

    async def _ble_cmd_mini_wifi_in():
        rv, v = await bom.cmd_wifi_in()
        if rv == 0:
            _t('    cmd WIFI_IN {}'.format(v))
        else:
            _t('    error cmd WIFI_IN')

    async def _ble_cmd_mini_wifi_out():
        rv = await bom.cmd_wifi_out()
        if rv == 0:
            _t('    OK cmd WIFI_OUT')
        else:
            _t('    error cmd WIFI_OUT')

    async def _ble_cmd_leds():
        rv = await bom.cmd_leds()
        if rv == 0:
            _t('    OK cmd LEDS')
        else:
            _t('    error cmd LEDS')

    async def _ble_is_connected():
        if g_bdc_type == 'op_mi':
            return await bom.is_connected()
        return await boc.is_connected()


# app can run from here OR setup.py entry point
def main():

    restart_bluetooth_service()
    ft.app(target=_main)
    # ft.app(target=_main, view=ft.WEB_BROWSER)


if __name__ == '__main__':
    main()
