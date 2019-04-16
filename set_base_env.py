#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: zhoubin
# Date: 2019/4/15
# Description: 该脚本主要用于新服务器的环境初始化

import configparser

from fabric.api import sudo, env, settings, hide
from fabric.api import runs_once, execute, task
from fabric.colors import red
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
        print('正在关闭 Firewalld...')
        result = sudo('systemctl stop firewalld')
        if result.return_code != 0:
            abort(red('Firewalld 关闭失败，请手动关闭！----- {}'.format(sudo('hostname'))))


@task
def turn_on_firewalld():
    """ 开启 Firewalld（模块）"""
    with settings(hide('everything'), warn_only=True):
        print('正在开启 Firewalld...')
        result = sudo('systemctl start firewalld')
        if result.return_code != 0:
            abort(red('Firewalld 开启失败，请手动关闭！'))


@task
def disable_firewalld():
    """ 禁止 Firewalld 开机启动（模块）"""
    with settings(hide('everything'), warn_only=True):
        print('正在禁用 Firewalld...')
        result = sudo('systemctl disable firewalld')
        if result.return_code != 0:
            abort(red('Firewalld 禁用失败，请手动关闭！'))


@task
def enable_firewalld():
    """ 设置 Firewalld 开机启动（模块）"""
    with settings(hide('everything'), warn_only=True):
        print('正在启用 Firewalld...')
        result = sudo('systemctl enable firewalld')
        if result.return_code != 0:
            abort(red('Firewalld 设置开机启动失败，请手动关闭！'))


@task
def disable_selinux():
    """ 永久禁用 SeLinux（模块）"""
    with settings(hide('everything'), warn_only=True):
        print('系统正在关闭 SeLinux')
        result = sudo('sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config')
        if result.return_code != 0:
            abort(red('SeLinux 关闭失败，请手动关闭！'))


@task
def install_software():
    """ 安装常用软件（模块）"""
    software = ['vim', 'wget', 'net-tools', 'lrzsz', 'tree', 'ntpdate']
    with settings(hide('everything'), warn_only=True):
        for i in software:
            print('正在安装软件 {}'.format(i))
            result = sudo('yum install -y {}'.format(i))
            if result.return_code != 0:
                print(red('软件 "{}" 安装失败,请手动安装！'.format(i)))


@task
def change_yum_mirror():
    """ 更换 YUM 使用国内镜像源（模块）"""
    mirrors = {
        'CentOS-Base.repo': 'http://mirrors.aliyun.com/repo/Centos-7.repo',
        'epel.repo': 'http://mirrors.aliyun.com/repo/epel-7.repo',
        'CentOS7-Base-163.repo': 'http://mirrors.163.com/.help/CentOS7-Base-163.repo'
    }
    with settings(hide('everything'), warn_only=True):
        print('正在安装 epel-release...')
        result = sudo('yum install -y epel-release')
        if result.return_code != 0:
            abort(red('epel-release 安装失败，请手动安装！'))
        result = sudo('mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup')
        if result.return_code == 0:
            for k, v in mirrors.items():
                print('正在下载 "{}"'.format(k))
                result = sudo('wget -O /etc/yum.repos.d/{0} {1}'.format(k, v))
                if result.return_code != 0:
                    abort(red('"{}" 下载失败！'.format(k)))
            print('正在刷新缓存...')
            result = sudo('yum clean all && yum makecache')
            if result.return_code != 0:
                abort(red('缓存刷新失败，请手动刷新！'))
        else:
            abort(red('备份原始 repo 文件失败！'))


@task
def set_crontab_ntpdate():
    """ 设置定时同步时间计划任务（模块）"""
    with settings(hide('everything'), warn_only=True):
        print("正在设置定时同步时间任务...")
        result = sudo('echo "*/20 * * * * /sbin/ntpdate pool.ntp.org > /dev/null 2>&1" >> /var/spool/cron/root')
        if result.return_code != 0:
            abort(red("定时计划任务设置失败，请手动设置！"))


def shutdown():
    """ 关闭服务器 """
    with settings(hide('everything'), warn_only=True):
        sudo('sync && sync && sync && shutdown -t now')


@task
def install_pyenv():
    """ 安装Python版本管理器 pyenv（模块） """
    print("正在安装Python版本控制器 pyenv...")
    with settings(hide('everything'), warn_only=True):
        result = sudo('git clone git://github.com/yyuu/pyenv.git ~/.pyenv')
        if result.return_code == 0:
            sudo('echo \'export PYENV_ROOT="$HOME/.pyenv"\' >> ~/.bash_profile')
            sudo('echo \'export PATH="$PYENV_ROOT/bin:$PATH"\' >> ~/.bash_profile')
            sudo('echo \'eval "$(pyenv init -)"\' >> ~/.bash_profile')
            sudo('source ~/.bash_profile')
        else:
            abort(red('pyenv 安装失败，请手动安装！'))


@task
def install_virtualenv():
    """ 安装虚拟环境管理插件 pyenv-virtualenv（模块） """
    print("正在安装虚拟环境管理插件 pyenv-virtualenv...")
    with settings(hide('everything'), warn_only=True):
        result = sudo('git clone https://github.com/pyenv/pyenv-virtualenv.git $(pyenv root)/plugins/pyenv-virtualenv')
        if result.return_code == 0:
            sudo('echo \'eval "$(pyenv virtualenv-init -)"\' >> ~/.bash_profile')
            sudo('source ~/.bash_profile')
        else:
            abort(red('pyenv-virtualenv 安装失败，请手动安装！'))


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
