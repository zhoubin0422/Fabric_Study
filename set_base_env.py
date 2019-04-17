#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: zhoubin
# Date: 2019/4/15
# Description: 该脚本主要用于新服务器的环境初始化

import configparser

from fabric.api import run, sudo, env, settings, hide, put
from fabric.api import runs_once, execute, task
from fabric.colors import red, green, blue
from fabric.utils import abort


server = configparser.ConfigParser(allow_no_value=True)
server.read('servers_config.ini')

env.hosts = server.options('hosts')
env.port = server.get('global', 'port')
env.user = server.get('global', 'user')
env.password = server.get('global', 'password')


def get_hostname():
    """ 获取主机名 """
    with settings(hide('everything'), warn_only=True):
        result = run('hostname')
        return result


@task
def turn_off_firewalld():
    """ 关闭 Firewalld """
    with settings(hide('everything'), warn_only=True):
        print(blue('[{}] 正在关闭 Firewalld...'.format(get_hostname())))
        result = sudo('systemctl stop firewalld')
        if result.return_code == 0:
            print(green('[{}] Firewalld 关闭完成.'.format(get_hostname())))
        else:
            abort(red('[{}] Firewalld 关闭失败，请手动关闭！'.format(get_hostname())))


@task
def turn_on_firewalld():
    """ 开启 Firewalld """
    with settings(hide('everything'), warn_only=True):
        print(blue('[{}] 正在开启 Firewalld...'.format(get_hostname())))
        result = sudo('systemctl start firewalld')
        if result.return_code == 0:
            print(green('[{}] Firewalld 开启完成.'.format(get_hostname())))
        else:
            abort(red('[{}] Firewalld 开启失败，请手动关闭！'.format(get_hostname())))


@task
def disable_firewalld():
    """ 禁止 Firewalld 开机启动 """
    with settings(hide('everything'), warn_only=True):
        print(blue('[{}] 正在禁用 Firewalld...'.format(get_hostname())))
        result = sudo('systemctl disable firewalld')
        if result.return_code == 0:
            print(green('[{}] Firewalld 禁用完成.'.format(get_hostname())))
        else:
            abort(red('[{}] Firewalld 禁用失败，请手动关闭！'.format(get_hostname())))


@task
def enable_firewalld():
    """ 设置 Firewalld 开机启动 """
    with settings(hide('everything'), warn_only=True):
        print(blue('[{}] 正在启用 Firewalld...'.format(get_hostname())))
        result = sudo('systemctl enable firewalld')
        if result.return_code == 0:
            print(green('[{}] Firewalld 设置开机启动完成.'.format(get_hostname())))
        else:
            abort(red('[{}] Firewalld 设置开机启动失败，请手动关闭！'.format(get_hostname())))


@task
def disable_selinux():
    """ 永久禁用 SeLinux """
    with settings(hide('everything'), warn_only=True):
        print(blue('[{}] 正在关闭 SeLinux'.format(get_hostname())))
        result = sudo('sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config')
        if result.return_code == 0:
            print(green('[{}] Selinux 关闭完成.'.format(get_hostname())))
        else:
            abort(red('({}) SeLinux 关闭失败，请手动关闭！'.format(get_hostname())))


@task
def install_software():
    """ 安装常用软件 """
    software = ['vim', 'wget', 'net-tools', 'lrzsz', 'tree', 'ntpdate', 'git']
    with settings(hide('everything'), warn_only=True):
        for i in software:
            print(blue('[{0}] 正在安装常用软件 "{1}"...'.format(get_hostname(), i)))
            result = sudo('yum install -y {}'.format(i))
            if result.return_code == 0:
                print(green('[{0}] 软件 "{1}" 安装完成.'.format(get_hostname(), i)))
            else:
                abort(red('[{0}] 软件 "{1}" 安装失败,请手动安装！'.format(get_hostname(), i)))


@task
def install_development_tools():
    """ 安装开发者工具 """
    print(blue('[{}] 正在安装开发者工具...'.format(get_hostname())))
    with settings(hide('everything'), warn_only=True):
        result = sudo('yum groupinstall -y "Development Tools"')
        if result.return_code == 0:
            print(green('[{0}] 开发者工具安装完成.'.format(get_hostname())))
        else:
            abort(red('[{0}] 开发者工具安装失败，请手动安装！'.format(get_hostname())))


@task
def change_yum_mirror():
    """ 更换 YUM 使用国内镜像源 """
    mirrors = {
        'CentOS-Base.repo': 'http://mirrors.aliyun.com/repo/Centos-7.repo',
        'epel.repo': 'http://mirrors.aliyun.com/repo/epel-7.repo',
        'CentOS7-Base-163.repo': 'http://mirrors.163.com/.help/CentOS7-Base-163.repo'
    }
    with settings(hide('everything'), warn_only=True):
        print(blue('[{}] 正在安装 epel-release...'.format(get_hostname())))
        result = sudo('yum install -y epel-release')
        if result.return_code == 0:
            print(green('[{}] epel-release 安装完成.'.format(get_hostname())))
        else:
            abort(red('[{}] epel-release 安装失败，请手动安装！'.format(get_hostname())))
        result = sudo('mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup')
        if result.return_code == 0:
            for k, v in mirrors.items():
                print(blue('[{0}] 正在下载 "{1}"'.format(get_hostname(), k)))
                result = sudo('wget -O /etc/yum.repos.d/{0} {1}'.format(k, v))
                if result.return_code == 0:
                    print(green('[{0}] "{1}" 下载完成'.format(get_hostname(), k)))
                else:
                    abort(red('[{0}] "{1}" 下载失败！'.format(get_hostname(), k)))
            print(blue('[{}] 正在刷新缓存...'.format(get_hostname())))
            result = sudo('yum clean all && yum makecache')
            if result.return_code == 0:
                print(green('[{}] 缓存刷新完成.'.format(get_hostname())))
            else:
                abort(red('[{}] 缓存刷新失败，请手动刷新！'.format(get_hostname())))
        else:
            abort(red('[{}] 备份原始 repo 文件失败！'.format(get_hostname())))


@task
def set_crontab_ntpdate():
    """ 设置定时同步时间计划任务 """
    with settings(hide('everything'), warn_only=True):
        print(blue("[{}] 正在设置定时同步时间任务...".format(get_hostname())))
        result = sudo('echo "*/20 * * * * /sbin/ntpdate pool.ntp.org > /dev/null 2>&1" >> /var/spool/cron/root')
        if result.return_code == 0:
            print(green('[{0}] 定时更新时间任务设置完成'.format(get_hostname())))
        else:
            abort(red("[{}] 定时计划任务设置失败，请手动设置！".format(get_hostname())))


@task
def shutdown():
    """ 关闭服务器 """
    with settings(hide('everything'), warn_only=True):
        sudo('sync && sync && sync && shutdown -t now')


@task
def reboot():
    """ 重启服务器 """
    with settings(hide('everything'), warn_only=True):
        sudo('sync && sync && sync && reboot')


@task
def install_pyenv():
    """ 安装Python版本管理器 pyenv """
    print(blue("[{}] 正在安装Python版本控制器 pyenv...".format(get_hostname())))
    with settings(hide('everything'), warn_only=True):
        result = sudo('git clone git://github.com/yyuu/pyenv.git ~/.pyenv')
        if result.return_code == 0:
            sudo('echo \'export PYENV_ROOT="$HOME/.pyenv"\' >> ~/.bash_profile')
            sudo('echo \'export PATH="$PYENV_ROOT/bin:$PATH"\' >> ~/.bash_profile')
            sudo('echo \'eval "$(pyenv init -)"\' >> ~/.bash_profile')
            sudo('source ~/.bash_profile')
            print(green('[{0}] pyenv 插件安装完成'.format(get_hostname())))
        else:
            abort(red('[{}] pyenv 安装失败，请手动安装！'.format(get_hostname())))


@task
def install_virtualenv():
    """ 安装虚拟环境管理插件 pyenv-virtualenv """
    print(blue("[{}] 正在安装虚拟环境管理插件 pyenv-virtualenv...".format(get_hostname())))
    with settings(hide('everything'), warn_only=True):
        result = sudo('git clone https://github.com/pyenv/pyenv-virtualenv.git $(pyenv root)/plugins/pyenv-virtualenv')
        if result.return_code == 0:
            sudo('echo \'eval "$(pyenv virtualenv-init -)"\' >> ~/.bash_profile')
            sudo('source ~/.bash_profile')
            print(green('[{0}] pyenv-virtualenv 插件安装完成'.format(get_hostname())))
        else:
            abort(red('[{}] pyenv-virtualenv 安装失败，请手动安装！'.format(get_hostname())))


@task
def install_python(version):
    """ 安装 Python """
    """
    需要安装的依赖库： readline, readline-devel, readline-static, openssl, openssl-devel, 
    openssl-static, sqlite-devel, bzip2-devel, bzip2-libs
    """
    libs_list = ['readline', 'readline-devel', 'readline-static', 'openssl', 'openssl-devel',
                 'openssl-static', 'sqlite-devel', 'bzip2-devel', 'bzip2-libs']
    with settings(hide('everything'), warn_only=True):
        put('/Users/wanwu/Downloads/Python-{}.tar.xz'.format(version), '/tmp/Python-{}.tar.xz'.format(version))
        sudo('mkdir ~/.pyenv/cache')
        sudo('mv /tmp/Python-{}.tar.xz ~/.pyenv/cache'.format(version))
        print(blue('[{}] 正在安装Python需要的依赖库'.format(get_hostname())))
        for i in libs_list:
            sudo('yum install -y {}'.format(i))
        print(blue('[{0}] 正在安装 Python {1}'.format(get_hostname(), version)))
        result = sudo('pyenv install -v {}'.format(version))
        if result.return_code == 0:
            print(green('[{0}] Python {1} 安装完成'.format(get_hostname(), version)))
        else:
            abort(red('[{0}] Python {1} 安装失败，请手动安装！'.format(get_hostname(), version)))


@task
def change_python_ver(version):
    """ 更换全局Python版本 """
    with settings(hide('everything'), warn_only=True):
        result = sudo('pyenv versions |grep {}'.format(version))
        if result.return_code == 0:
            result = sudo('pyenv global {} && pyenv rehash'.format(version))
            if result.return_code == 0:
                print(green('[{0}] Python 版本已切换成 Python {1}'.format(get_hostname(), version)))
            else:
                abort(red('[{}] Python 版本切换失败.'.format(get_hostname())))
        else:
            abort('[{0}] Python 不存在版本 ({1})'.format(get_hostname(), version))


@task
@runs_once
def start():
    """ 开始配置环境 """
    execute(turn_off_firewalld)
    execute(disable_firewalld)
    execute(disable_selinux)
    execute(install_software)
    execute(install_development_tools)
    execute(change_yum_mirror)
    execute(set_crontab_ntpdate)
    execute(install_pyenv)
    execute(install_virtualenv)
    execute(install_python, '3.6.8')
    execute(change_python_ver, '3.6.8')
