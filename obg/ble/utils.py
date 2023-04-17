import platform
import subprocess as sp


def restart_bluetooth_service():
    if platform.system() == 'Linux':
        # print('restarting Linux BLE service')
        c = 'bluetoothctl -- disconnect'
    elif platform.system() == 'Windows':
        print('restarting Windows BLE service')
        c = 'Get-Service -DisplayName *Bluetooth* | Restart-Service -force'
        sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
