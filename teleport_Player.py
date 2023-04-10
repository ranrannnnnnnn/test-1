import json
import os
import time
import threading
import queue

from mcdreforged.api.types import PluginServerInterface
from mcdreforged.api.command import *

PLUGIN_METADATA = {
    "id": "teleport",
    "version": "beta 0.2",
    "name": "Teleport_Player",
    "author": "ranrannnnnnn",
    "description": "好耶",
}

help_message = """传送指令帮助:
!!teleport <other_player> 将自己传送到所选玩家
!!sethome <x> <y> <z> 设置家坐标
!!home 传送到你所设置的家的坐标
!!teleport other_player <other_player>
other_player: 目标选择器,实体UUID,玩家名称
"""

accept_queue = queue.Queue(1)
tp_queue = queue.Queue(1)


def check(path, file, name):
    a = file.read()
    file.close()
    if a is None:
        b = {}
        a = json.dumps(b)
        file = open(path + '/' + name + '.json', 'w')
        file.write(a)
        file.close()
    else:
        pass


def file_check(path):
    file = open(path + '/' + 'homeset.json', 'a+')
    check(path, file, 'homeset')


def other_player_tp1(src, ctx, server):
    global accept_queue, accept, tp_queue
    player = src.player if src.is_player else 'Console'
    other_player = ctx['player']
    accept[other_player] = False
    tp_queue.put(accept)
    time_start = time.time()
    time_end = time_start + 30
    server.tell(other_player, f'§7[server] 玩家 {player} 请求将您传送至他身边,输入"!!accept"接受邀请\n'
                              f'§7[server] 你拥有30秒钟的时间同意邀请')
    server.tell(player, '§7[server] 申请已发出')
    server.say(f'计时器已启动 start: {time_start} end: {time_end}')
    while True:
        time_now = time.time()
        if time_now >= time_end:
            server.tell(player, f'§7[server] 你的传送请求已超时')
            server.tell(player, f'§7[server] 玩家 {player} 的传送请求已超时')
            del accept[other_player]
            server.say(f'线程结束')
            break
        elif accept_queue.full():
            accept = accept_queue.get()
            if accept[other_player]:
                server.execute(f'tp {other_player} {player}')
                server.tell(other_player, f'§7[server] 传送中...')
                server.tell(player, f'§7[server] {other_player}悄悄的来到了你的身边...')
                del accept[other_player]
                server.say(f'线程结束')
        time.sleep(1)


def other_player_tp(src, ctx, server):
    global accept_queue, accept, tp_queue
    player = src.player if src.is_player else 'Console'
    other_player = ctx['player']
    accept[other_player] = False
    tp_queue.put(accept)
    time_start = time.time()
    time_end = time_start + 30
    server.tell(other_player, f'§7[server] 玩家 {player} 请求将您传送至他身边,输入"!!accept"接受邀请\n'
                              f'§7[server] 你拥有30秒钟的时间同意邀请')
    server.tell(player, '§7[server] 申请已发出')
    server.say(f'计时器已启动 start: {time_start} end: {time_end}')
    accept = accept_queue.get()
    if accept[other_player]:
        server.execute(f'tp {other_player} {player}')
        server.tell(other_player, f'§7[server] 传送中...')
        server.tell(player, f'§7[server] {other_player}悄悄的来到了你的身边...')
        del accept[other_player]
        server.say(f'线程结束')


def on_load(server: PluginServerInterface, old):
    global q, accept
    server.logger.info('传送插件加载成功')
    builder = SimpleCommandBuilder()
    path = os.path.join('config', 'Teleport_Player')
    if not os.path.isdir(path):
        path = os.path.join('config')
        os.mkdir(path + './Teleport_Player')
    file_check(path)
    accept = {}

    def teleport(src, ctx):
        player = src.player if src.is_player else 'Console'
        other_player = ctx['player']
        if src.is_player:
            server.tell(player, f'§7[server] §d传送中...')
            server.tell(other_player, f'§7[server] §9{player} §d悄悄的来到了你的身边...')
            server.execute(f'tp {player} {other_player}')
        else:
            server.logger.info(f'控制台不能使用该指令!')

    def set_home(src, ctx):
        player = src.player if src.is_player else 'Console'
        x, y, z = ctx['x'], ctx['y'], ctx['z']
        file = open(path + '/' + 'homeset.json', 'r')
        homeset_str = file.read()
        homeset_dict = json.loads(homeset_str)
        file.close()
        if src.is_player:
            file = open(path + '/' + 'homeset.json', 'w')
            homeset_dict[player] = [x, y, z]
            homeset_str = json.dumps(homeset_dict)
            file.write(homeset_str)
            file.close()
            server.tell(player, '§7[server] §d设置成功/n'
                                f'§7[server] §d设定坐标为 {x}, {y}, {z}, 以后可以使用/home快速返回你设定的坐标了哦~')
        else:
            server.logger.info('控制台无法使用该指令!')

    def home(src, ctx):
        player = src.player if src.is_player else 'Console'
        if src.is_player:
            file = open('homeset.json', 'r')
            homeset_str = file.read()
            homeset_dict = json.loads(homeset_str)
            file.close()
            if homeset_dict.get(player) is not None:
                xyz = homeset_dict[player]
                server.tell(player, '传送中...')
                server.execute(f'tp {player} {xyz[0]} {xyz[1]} {xyz[2]}')
            else:
                server.tell(player, '§7[server] §d你还没有设置坐标哦~')
        else:
            server.logger.info('控制台无法使用该指令!')

    def other_player(src, ctx):
        thread1 = threading.Thread(target=other_player_tp(src, ctx, server), name='abc')
        thread1.start()

    def teleport_help(server: PluginServerInterface):
        server.reply(f'[teleport] {help_message}')

    def accept_command(src, ctx):
        global accept_queue, accept, tp_queue
        player = src.player if src.is_player else 'Console'
        if tp_queue.full():
            accept = tp_queue.get()
            if player in accept:
                accept[player] = True
                accept_queue.put(accept)
            else:
                server.tell(player, '§7[server] 没有任何一个人向你发出申请...')
        else:
            server.tell(player, '§7[server] 没有任何一个人向你发出申请...')

    builder.command('!!teleport help', teleport_help)
    builder.command('!!teleport <player>', teleport)
    builder.command('!!teleport other_player <player>', other_player)
    builder.command('!!home', home)
    builder.command('!!sethome <x> <y> <z>', set_home)
    builder.command('!!accept', accept_command)
    builder.arg('player', Text)
    builder.arg('x', Float)
    builder.arg('y', Float)
    builder.arg('z', Float)
    builder.register(server)
