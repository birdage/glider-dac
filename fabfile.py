from fabric.api import *
from fabric.contrib.files import *
import os
from copy import copy
import time

"""
    Call this with fab -c .fab TASK to pick up deploy variables
    Required variables in .fab file:
        mail_server = x
        mail_port = x
        mail_username = x
        mail_password = x
        mail_default_sender = x
        mailer_debug = x
        mail_default_to = x
        mail_default_list = x
        webpass = x
        secret_key = x
        data_root = x
        rsync_ssh_user = x
        rsync_to_host = x
        rsync_to_path = x
"""

env.user = "gliderweb"
code_dir = "/home/gliderweb/glider-mission"


def admin():
    env.user = "root"
def gliderweb():
    env.user = "gliderweb"

def deploy_tds():
    env.hosts = ['tds.gliders.ioos.us']

    sup_conf_file = "~/supervisord-catalog-monitor.conf"
    crontab_file = "~/crontab.txt"
    gliderweb()
    stop_supervisord(conf=sup_conf_file)
    gliderweb()
    with cd(code_dir):
        run("git pull origin master")
        update_supervisord(src_file="deploy/supervisord-catalog-monitor.conf", dst_file=sup_conf_file)
        update_crontab(src_file="deploy/gliderweb_crontab.txt", dst_file=crontab_file)
        update_libs()
        start_supervisord(conf=sup_conf_file)
        run("supervisorctl -c %s start all" % sup_conf_file)

def deploy_ftp():
    env.hosts = ['ftp.gliders.ioos.us']

    gliderweb()
    stop_supervisord(conf="~/supervisord.conf")
    gliderweb()
    with cd(code_dir):
        run("git pull origin master")
        update_supervisord(src_file="deploy/supervisord.conf", dst_file="/home/gliderweb/supervisord.conf")
        update_libs()
        start_supervisord(conf="~/supervisord.conf")
        run("supervisorctl -c ~/supervisord.conf start all")

    admin()
    stop_supervisord(conf="/root/supervisord-perms-monitor.conf")
    update_supervisord(src_file="deploy/supervisord-perms-monitor.conf", dst_file="/root/supervisord-perms-monitor.conf")
    update_libs(virtual_env="root-monitor")
    start_supervisord(conf="/root/supervisord-perms-monitor.conf")
    with prefix("workon root-monitor"):
        run("supervisorctl -c /root/supervisord-perms-monitor.conf start all")

    restart_nginx()

def update_crontab(src_file, dst_file):
    upload_template(src_file, dst_file, context=copy(env), use_jinja=True, use_sudo=False, backup=False, mirror_local_mode=True)
    run("crontab %s" % dst_file)

def update_supervisord(src_file, dst_file):
    run("pip install supervisor")
    upload_template(src_file, dst_file, context=copy(env), use_jinja=True, use_sudo=False, backup=False, mirror_local_mode=True)

def update_libs(virtual_env=None):
    with cd(code_dir):
        with settings(warn_only=True):
            if virtual_env is not None:
                with prefix("workon %s" % virtual_env):
                    run("pip install -r requirements.txt")
            else:
                run("pip install -r requirements.txt")

def restart_nginx():
    admin()
    run("/etc/init.d/nginx restart")

def stop_supervisord(conf):
    with cd(code_dir):
        with settings(warn_only=True):
            run("supervisorctl -c %s stop all" % conf)
            run("kill -QUIT $(ps aux | grep supervisord | grep -v grep | awk '{print $2}')")

    kill_pythons()

def kill_pythons():
    admin()
    with settings(warn_only=True):
        run("kill -QUIT $(ps aux | grep python | grep -v supervisord | awk '{print $2}')")

def start_supervisord(conf):
    with cd(code_dir):
        with settings(warn_only=True):
            run("supervisord -c %s" % conf)
