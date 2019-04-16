#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: zhoubin
# Date: 2019/4/15
# Description: 改脚本主要用于新服务器环境初始化

import configparser

from fabric.api import run, sudo, env, shell_env, settings, hide
from fabric.api import runs_once, execute, task
from fabric.colors import red, green, white
from fabric.utils import abort


server = configparser.ConfigParser(allow_no_value=True)
server.read('servers_config.ini')

env.hosts = server.options('hosts')
env.port = server.get('global', 'port')
env.user = server.get('global', 'user')
env.password = server.get('global', 'password')


@task
def turn_off_firewalld():
    """ 关闭 Firewalld（模块） """
    with settings(hide('everything'), warn_only=True):
        print(white('正在关闭 Firewalld...'))
        result = sudo('systemctl stop firewalld')
        if result.return_code == 0:
            print(green('Firewalld 关闭成功.'))
        else:
            abort(red('Firewalld 关闭失败，请手动检查！'))


@task
def turn_on_firewalld():
    """ 开启 Firewalld（模块）"""
    with settings(hide('everything'), warn_only=True):
        print(white('正在开启 Firewalld...'))
        result = sudo('systemctl start firewalld')
        if result.return_code == 0:
            print(green('Firewalld 开启成功.'))
        else:
            abort(red('Firewalld 开启失败，请手动检查！'))


@task
def disable_firewalld():
    """ 禁止 Firewalld 开机启动（模块）"""
    with settings(hide('everything'), warn_only=True):
        print(white('正在禁用 Firewalld...'))
        result = sudo('systemctl disable firewalld')
        if result.return_code == 0:
            print(green('Firewalld 禁用成功.'))
        else:
            abort(red('Firewalld 禁用失败，请手动检查！'))


@task
def enable_firewalld():
    """ 设置 Firewalld 开机启动（模块）"""
    with settings(hide('everything'), warn_only=True):
        print(white('正在启用 Firewalld...'))
        result = sudo('systemctl enable firewalld')
        if result.return_code == 0:
            print(green('Firewalld 设置开机启动成功.'))
        else:
            abort(red('Firewalld 设置开机启动失败，请手动检查！'))


@task
def disable_selinux():
    """ 永久禁用 SeLinux（模块）"""
    with settings(hide('everything'), warn_only=True):
        print('系统正在关闭 SeLinux')
        result = sudo('sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config')
        if result.return_code == 0:
            print(green('SeLinux 关闭完成.'))
        else:
            abort(red('SeLinux 关闭失败，请手动检查'))


@task
def install_software():
    """ 安装常用软件（模块）"""
    software = ['vim', 'wget', 'net-tools', 'lrzsz', 'tree', 'ntpdate']
    with settings(hide('everything'), warn_only=True):
        for i in software:
            print('正在安装软件 {}'.format(i))
            result = sudo('yum install -y {}'.format(i))
            if result.return_code == 0:
                print(green('软件 "{}" 安装完成.'.format(i)))
            else:
                print(green('软件 "{}" 安装失败,请手动检查！'.format(i)))


@task
def change_yum_mirror():
    """ 更换 YUM 使用国内镜像源（模块）"""
    mirrors = {
        'CentOS-Base.repo': 'http://mirrors.aliyun.com/repo/Centos-7.repo',
        'epel.repo': 'http://mirrors.aliyun.com/repo/epel-7.repo',
        'CentOS7-Base-163.repo': 'http://mirrors.163.com/.help/CentOS7-Base-163.repo'
    }
    with settings(hide('everything'), warn_only=True):
        print('正在安装扩展镜像源')
        result = sudo('yum install -y epel-release')
        if result.return_code == 0:
            print(green('扩展镜像源安装完成'))
        else:
            abort(red('扩展镜像源安装失败，请手动安装'))
        result = sudo('mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup')
        if result.return_code == 0:
            for k, v in mirrors.items():
                print('正在下载 "{}"'.format(k))
                result = sudo('wget -O /etc/yum.repos.d/{0} {1}'.format(k, v))
                if result.return_code == 0:
                    print(green('"{}" 下载完成'.format(k)))
                else:
                    print(red('"{}" 下载失败'.format(k)))
            print('正在刷新缓存...')
            result = sudo('yum clean all && yum makecache')
            if result.return_code == 0:
                print(green('缓存刷新完成。'))
            else:
                abort(red('缓存刷新失败，请手动检查'))
        else:
            abort(red('备份原始 mirror 失败！'))


@task
def set_crontab_ntpdate():
    """ 设置定时同步时间计划任务（模块）"""
    with settings(hide('everything'), warn_only=True):
        print("正在设置定时同步时间任务...")
        result = sudo('echo "*/20 * * * * /sbin/ntpdate pool.ntp.org > /dev/null 2>&1" >> /var/spool/cron/root')
        if result.return_code == 0:
            print(green("定时更新时间任务设置完成."))
        else:
            abort(red("定时计划任务设置失败，请手动检查！"))


@task
def shutdown():
    """ 关闭服务器 """
    with settings(hide('everything'), warn_only=True):
        sudo('sync && sync && sync && shutdown -t now')


@task
@runs_once
def start():
    """ 设置基础环境入口 """
    execute(turn_off_firewalld)
    execute(disable_firewalld)
    execute(disable_selinux)
    execute(install_software)
    execute(change_yum_mirror)
    execute(set_crontab_ntpdate)
