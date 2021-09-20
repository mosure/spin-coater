import asyncio
import time

from aiohttp import web
from aiohttp_middlewares import cors_middleware

from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Servo


def current_milli_time():
    return round(time.time() * 1000)


pin_factory = PiGPIOFactory()


class MockServo:
    def __init__(self):
        self.value = -1

class SpinCoater:
    def __init__(self, max_rpm, gpio):
        self.max_rpm = max_rpm
        self.current_rpm = 0
        self.estop = False

        try:
            self.servo = Servo(gpio, pin_factory=pin_factory)
        except Exception as e:
            print(e)
            self.servo = MockServo()

        self.servo.value = -1

    async def lerp_rpm(self, rpm, duration_ms):
        print(f'LERP: {rpm} rpm in {duration_ms} ms')

        remaining_ms = duration_ms
        start_rpm = self.current_rpm

        last_frame = current_milli_time()
        while remaining_ms > 0 and self.current_rpm != rpm:
            current_frame = current_milli_time()

            frame_rpm = (rpm - start_rpm) * (1 - remaining_ms / duration_ms) + start_rpm
            self.set_rpm(frame_rpm)

            remaining_ms -= current_frame - last_frame
            last_frame = current_frame

            await asyncio.sleep(0.01)

            if self.estop:
                break

        self.set_rpm(rpm)

    def set_estop(self, estop: bool):
        self.current_rpm = 0
        self.estop = estop

        if self.estop:
            print('EMERGENCY STOP')
        else:
            print('EMERGENCY STOP RESET')

    def set_rpm(self, rpm):
        self.current_rpm = rpm

        if self.estop:
            self.current_rpm = 0

        rpm_to_servo = 2 * self.current_rpm / self.max_rpm - 1

        self.servo.value = min(max(rpm_to_servo, -1), 1)


spin_coater = SpinCoater(6000, 25)


async def handle_lerp(request):
    try:
        body = await request.json()

        duration_ms = body['duration_ms']
        rpm = body['rpm']

        await spin_coater.lerp_rpm(rpm, duration_ms)

        return web.json_response({
            'rpm': spin_coater.current_rpm,
            'estop': spin_coater.estop
        })
    except Exception as e:
        return web.Response(text=e)

async def handle_estop(request):
    try:
        body = await request.json()

        spin_coater.set_estop(body['estop'])

        return web.json_response({
            'rpm': spin_coater.current_rpm,
            'estop': spin_coater.estop
        })
    except Exception as e:
        return web.Response(text=str(e))

async def handle_get(_):
    return web.json_response({
        'rpm': spin_coater.current_rpm,
        'estop': spin_coater.estop
    })


app = web.Application(
    middlewares=[cors_middleware(allow_all=True)],
)

app.router.add_static('/client', './client', name='static-client')

app.router.add_get('/api/spinner', handle_get)
app.router.add_post('/api/spinner/estop', handle_estop)
app.router.add_post('/api/spinner/lerp', handle_lerp)

web.run_app(app, host='0.0.0.0', port=1234)
