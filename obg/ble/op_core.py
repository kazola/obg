import asyncio
import platform
import time
from bleak import BleakError, BleakClient
import subprocess as sp

from obg.ble.utils import restart_bluetooth_service

g_states_core = (
    'st_booting',
    'st_ready_to_conf',
)


# these are set OK for optode core
UUID_T = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'
UUID_R = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'


def _is_cmd_done(c, a):
    # for Optode Core devices
    rv = False

    if type(a) is bytes:
        a = a.decode()

    if a == 'ERR':
        return True

    if c == 'ru' and a == 'run_ok':
        rv = True
    if c == 'dl' and a == 'dl_ok':
        rv = True
    # increase time
    if c == 'it' and a == 'inc_time_ok':
        rv = True
    if c == 'ma' and len(a) == 17:
        rv = True
    if c == 'st' and a in g_states_core:
        rv = True
    if c == 'lo' and a == 'lo_ok':
        rv = True
    if c == 'lf' and a == 'lf_ok':
        rv = True
    if c == 'ml' and a == 'ml_ok':
        rv = True
    if c == 'mr' and a == 'mr_ok':
        rv = True
    if c == 'ba' and int(a):
        rv = True
    if c == 'll' and len(a) == 4:
        rv = True
    if c == 'lr' and len(a) == 4:
        rv = True

    # debug
    # if rv:
    #     print(c, a)
    return rv


class BleOptodeCore:    # pragma: no cover
    def __init__(self, dbg_ans=False):
        self.cli = None
        self.ans = bytes()
        self.cmd = ''
        self.dbg_ans = dbg_ans

    async def is_connected(self):
        return self.cli and self.cli.is_connected

    async def _cmd(self, c: str, empty=True):
        self.cmd = c
        if empty:
            self.ans = bytes()

        if self.dbg_ans:
            print('<-', c)

        await self.cli.write_gatt_char(UUID_R, c.encode())

    async def _ans_wait(self, timeout=10.0):

        # for benchmark purposes
        start = time.time()

        # accumulate command answer in notification handler
        while self.cli and self.cli.is_connected and timeout > 0:
            await asyncio.sleep(0.1)
            timeout -= 0.1

            # ---------------------------------
            # considers the command answered
            # ---------------------------------

            if _is_cmd_done(self.cmd, self.ans):
                if self.dbg_ans:
                    # debug good answers
                    elapsed = time.time() - start
                    print('>', self.ans)
                    print('\ttook {} secs'.format(int(elapsed)))
                return self.ans

        # allows debugging timeouts
        elapsed = int(time.time() - start)

        # useful in case we have errors
        print('[ BLE ] timeout {} for cmd {}'.format(elapsed, self.cmd))
        if not self.ans:
            return
        print('\t dbg_ans:', self.ans)

    async def cmd_run(self):
        await self._cmd('ru')
        rv = await self._ans_wait()
        return 0 if rv == b'run_ok' else 1

    async def cmd_dl(self):
        await self._cmd('dl')
        rv = await self._ans_wait()
        return 0 if rv == b'dl_ok' else 1

    async def cmd_inc_time(self):
        await self._cmd('it')
        rv = await self._ans_wait()
        return 0 if rv == b'inc_time_ok' else 1

    async def cmd_status(self):
        await self._cmd('st')
        rv = await self._ans_wait()
        if rv and rv.decode() in g_states_core:
            return 0, rv.decode()
        return 1, ''

    async def cmd_limit_left(self):
        await self._cmd('ll')
        rv = await self._ans_wait()
        if len(rv) == 4 and b'll' in rv:
            return 0, rv.decode()
        return 1, ''

    async def cmd_limit_right(self):
        await self._cmd('lr')
        rv = await self._ans_wait()
        if len(rv) == 4 and b'lr' in rv:
            return 0, rv.decode()
        return 1, ''

    async def cmd_macs(self):
        await self._cmd('ma')
        rv = await self._ans_wait()
        if len(rv) == 17:
            return 0, rv.decode()
        return 1, ''

    async def cmd_battery(self):
        await self._cmd('ba')
        rv = await self._ans_wait()
        if len(rv) == 4:
            return 0, rv.decode()
        return 1, ''

    async def cmd_led_on(self):
        await self._cmd('lo')
        rv = await self._ans_wait()
        return 0 if rv == b'lo_ok' else 1

    async def cmd_led_off(self):
        await self._cmd('lf')
        rv = await self._ans_wait()
        return 0 if rv == b'lf_ok' else 1

    async def cmd_motor_left(self):
        await self._cmd('ml')
        rv = await self._ans_wait()
        return 0 if rv == b'ml_ok' else 1

    async def cmd_motor_right(self):
        await self._cmd('mr')
        rv = await self._ans_wait()
        return 0 if rv == b'mr_ok' else 1

    async def disconnect(self):
        try:
            await self.cli.disconnect()
        except (Exception, ):
            pass

    async def connect(self, mac):
        def c_rx(_: int, b: bytearray):
            self.ans += b

        till = time.perf_counter() + 30
        self.cli = BleakClient(mac)
        rv: int

        while True:
            now = time.perf_counter()
            if now > till:
                print('[ BLE ] connecting Optode Core totally failed')
                rv = 1
                break

            try:
                if await self.cli.connect():
                    await self.cli.start_notify(UUID_T, c_rx)
                    rv = 0
                    break

            except (asyncio.TimeoutError, BleakError, OSError) as ex:
                _ = int(till - time.perf_counter())
                e = '[ BLE ] connect Optode Core attempt failed, {} seconds left -> {}'
                print(e.format(_, ex))
                await asyncio.sleep(.5)

        return rv
