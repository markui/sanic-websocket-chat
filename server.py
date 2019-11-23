from sanic import Sanic
from sanic.response import json
import asyncio
import aioredis
import motor.motor_asyncio
import ujson
import logging
from websockets import WebSocketCommonProtocol


app = Sanic(__name__)


async def reader(ch):
    while (await ch.wait_message()):
        msg = await ch.get_json()
        print("Got Message:", msg)

@app.listener('before_server_start')
async def setup_db(app, loop):
    app.motor_client = motor.motor_asyncio.AsyncIOMotorClient('localhost', 27017)
    app.db = app.motor_client.test
    # app.db.users.insert_one({'_id': 'dexter1234', 'nickname': 'dexter', 'dsf': 'sadf'})
    print('setup db!')

@app.listener('after_server_start')
async def notify_server_started(app, loop):
    print('Server successfully started!')

@app.listener('before_server_stop')
async def notify_server_stopping(app, loop):
    print('Server shutting down!')

@app.listener('after_server_stop')
async def close_db(app, loop):
    app.motor_client.close()
    print('close_db!')

@app.route('/')
async def test(request):
    print('hi')
    return json({'test': 'hello world!'})


async def example_func():
    await asyncio.sleep(5)
    print('sleeping finished!')

@app.route('/example')
async def example(request):
    # tsk1 = asyncio.create_task(example_func())
    # print(tsk1)
    pub = await aioredis.create_redis(
        'redis://localhost')
    sub = await aioredis.create_redis(
        'redis://localhost')
    res = await sub.subscribe('chan:1')
    ch1 = res[0]

    tsk = asyncio.ensure_future(reader(ch1))
    print(tsk)
    res = await pub.publish_json('chan:1', ["Hello", "world"])
    assert res == 1

    await sub.unsubscribe('chan:1')
    await tsk
    sub.close()
    pub.close()
    return json({'test': 'sleeping finished!'})

async def message_handler(message, ws: WebSocketCommonProtocol):
    _type = message.get('type')
    if _type == 'PING':
        await ws.send(ujson.dumps({
            'type': 'PONG'
        }))
    elif _type == 'SEND':
        pass
    else:
        pass

@app.websocket('/chat')
async def chat(request, ws: WebSocketCommonProtocol):
    print('Connected to WS Server!')
    print(request)
    print(ws)
    user_id = request.args.get('user_id')
    nickname = request.args.get('nickname')
    # 1. Authenticate User (create_or_update)
    db = app.db
    await db.users.update_one({'user_id': user_id}, {'$set': {'nickname': nickname}}, True)
    await ws.send(ujson.dumps({'type': 'LOGIN', 'user_id': user_id, 'nickname': nickname, 'profile_url': 'https://sendbird.com/main/img/profiles/profile_11_512px.png',
                              'ping_interval': 15, 'pong_timeout': 5, 'reconnect_interval': 3}))
    # 2. PING/PONG
    while True:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=90.0)
            loaded_msg = ujson.loads(msg)
            await message_handler(loaded_msg, ws)
        except Exception as e:
            # TODO: leave user from channel
            logging.error('WS RECV Error: ' + repr(e))
            break



# Websocket configs
# app.config.WEBSOCKET_MAX_SIZE = 2 ** 20
# app.config.WEBSOCKET_MAX_QUEUE = 32
# app.config.WEBSOCKET_READ_LIMIT = 2 ** 16
# app.config.WEBSOCKET_WRITE_LIMIT = 2 ** 16

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, auto_reload=False)


