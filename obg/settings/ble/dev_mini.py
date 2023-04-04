import asyncio
import platform
import time
from bleak import BleakError, BleakClient
import subprocess as sp


# these are defined OK
UUID_T = '00002324-0000-1000-8000-00805f9b34fb'
UUID_R = '00002325-0000-1000-8000-00805f9b34fb'


def _is_cmd_done(c, a):
    # for Optode Mini devices
    if type(a) is bytes:
        a = a.decode()

    if c == 'l' and a == 'led_ok':
        return True


class BleOptodeMini:    # pragma: no cover
    def __init__(self, dbg_ans=False):
        self.cli = None
        self.ans = bytes()
        self.cmd = ''
        self.dbg_ans = dbg_ans
        # nice trick to start with fresh page
        if platform.system() == 'Linux':
            c = 'bluetoothctl -- disconnect'
            sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)

    async def is_connected(self):
        return self.cli and self.cli.is_connected

    async def _cmd(self, c: str, empty=True):
        self.cmd = c
        if empty:
            self.ans = bytes()

        if self.dbg_ans:
            print('<', c)

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

    async def cmd_led(self):
        await self._cmd('l')
        rv = await self._ans_wait()
        return 0 if rv == b'led_ok' else 1

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
                print('[ BLE ] connecting Optode Mini totally failed')
                rv = 1
                break

            try:
                if await self.cli.connect():
                    await self.cli.start_notify(UUID_T, c_rx)
                    rv = 0
                    break

            except (asyncio.TimeoutError, BleakError, OSError) as ex:
                _ = int(till - time.perf_counter())
                e = '[ BLE ] connect Optode Mini attempt failed, {} seconds left -> {}'
                print(e.format(_, ex))
                await asyncio.sleep(.5)

        return rv
