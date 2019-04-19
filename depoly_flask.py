#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: zhoubin
# Date: 2019/4/19
# Description:

import os
import sys
import configparser

from fabric.api import (cd, run, runs_once, task, env, roles, put, execute, hide, settings, sudo)
from fabric.colors import red, green, yellow
from fabric.contrib.files import exists

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_PATH)

from Fabric_study.set_base_env import get_hostname

server = configparser.ConfigParser(allow_no_value=True)
server.read('servers_config.ini')

env.user = server.get('global', 'user')
env.password = server.get('global', 'password')
env.port = server.get('global', 'port')
env.roledefs = {
    'web': server.options('web'),
    'db': server.options('db')
}


def is_redis_installed():
    """ 判断 redis 是否运行 """
    with settings(hide('everything'), warn_only=True):
        result = run("netstat -tl | grep -w 6379")
        return result.return_code == 0


def install_redis():
    """ 安装 redis """
    sudo("yum install -y redis")


def change_redis_conf():
    """ 更改 Redis 配置 """
    sudo("sed -i 's/bind 127.0.0.1/bind 0.0.0.0/' /etc/redis.conf")


def reboot_redis():
    """ 重启 Redis """
    sudo("systemctl restart redis", pty=False)


@task
@roles('db')
def depoly_db():
    """ 部署Redis """
    if is_redis_installed():
        print(yellow('[{0}] redis was successfully installed'.format(get_hostname())))
    else:
        install_redis()
        change_redis_conf()
        reboot_redis()
        print(green('[{0}] redis has successfully installed'.format(get_hostname())))


def is_python_package_installed(package):
    """ 判断包Python包是否正确安装 """
    with settings(hide('everything'), warn_only=True):
        result = sudo("python -c 'import {0}'".format(package))
        return result.return_code == 0


def install_python_package(package):
    """ 安装Python 包 """
    sudo('pip install {0}'.format(package))


def pip_install_if_need(package):
    """ 安装需要的包 """
    if not is_python_package_installed(package):
        install_python_package(package)
        print(green('[{0}] {1} has installed'.format(get_hostname(), package)))
    else:
        print(yellow('[{0}] {1} was installed'.format(get_hostname(), package)))


def install_package():
    """ 安装包 """
    for package in ['redis', 'gunicorn', 'flask']:
        pip_install_if_need(package)


def kill_web_app_if_exists():
    """ 杀死 web 进程 """
    with cd('/tmp'):
        if exists('app.pid'):
            pid = run('cat app.pid')
            print(yellow('[{0}] kill app which pip is {1}'.format(get_hostname(), pid)))
            with settings(hide('everything'), warn_only=True):
                run('kill -9 {0}'.format(pid))
        else:
            print(red('[{0}] pid file not exists.'.format(get_hostname())))


def upload_web_app():
    """ 上传 web 应用文件 """
    put('app.py', '/tmp/app.py')


def run_web_app():
    """ 运行 web 应用 """
    with cd('/tmp'):
        sudo('gunicorn -w 1 app:app -b 0.0.0.0:5000 -D -p /tmp/app.pid --log-file /tmp/app.log', pty=False)


def restart_web_app():
    """ 重启web应用 """
    kill_web_app_if_exists()
    run_web_app()


@task
@roles('web')
def depoly_web():
    """ 部署web """
    install_package()
    upload_web_app()
    restart_web_app()


@task
@runs_once
def depoly_all():
    """ 部署所有应用 """
    execute(depoly_db)
    execute(depoly_web)
