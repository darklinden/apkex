#!/usr/bin/env python
import sys
import os
import json
import shutil
import subprocess

def run_cmd(cmd):
    print("run cmd: " + " ".join(cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        print(err)
    return out

def self_install(file, des):
    file_path = os.path.realpath(file)

    filename = file_path

    pos = filename.rfind("/")
    if pos:
        filename = filename[pos + 1:]

    pos = filename.find(".")
    if pos:
        filename = filename[:pos]

    to_path = os.path.join(des, filename)

    print("installing [" + file_path + "] \n\tto [" + to_path + "]")
    if os.path.isfile(to_path):
        os.remove(to_path)

    shutil.copy(file_path, to_path)
    run_cmd(['chmod', 'a+x', to_path])

def read_json(file_path):
    f = open(file_path, mode='rb')
    content = f.read()
    f.close()

    return json.loads(content)

def read_config():
    home = os.path.expanduser("~")
    conf_file_path = os.path.join(home, ".apkcfg")
    if os.path.isfile(conf_file_path):
        jo = read_json(conf_file_path)
        return jo
    else:
        return {"key_path": "", "alias_name": "", "store_pwd": "", "key_pwd": ""}

def param_exists(param):
    if param:
        if len(param) > 0:
            return True

    return False

def sign(src_name, key_path = "", alias_name = "", store_pwd = "", key_pwd = ""):

    if not param_exists(src_name):
        print("no src name input, exit")
        return

    conf = read_config()
    des_name = os.path.splitext(src_name)[0] + "_resigned.apk"

    if not param_exists(key_path):
        key_path = conf["key_path"]

    if not param_exists(alias_name):
        alias_name = conf["alias_name"]

    if not param_exists(store_pwd):
        store_pwd = conf["store_pwd"]

    if not param_exists(key_pwd):
        key_pwd = conf["key_pwd"]

    command = "jarsigner -verbose"
    command += " -keystore " + key_path
    command += " -digestalg SHA1"
    command += " -sigalg MD5withRSA"
    command += " -storepass " + store_pwd
    command += " -keypass " + key_pwd
    command += " -signedjar " + des_name
    command += " " + src_name + " " + alias_name

    print("exec: " + command)
    os.system(command)
    return des_name

def align(src_name):
    des_name = os.path.splitext(src_name)[0] + "_aligned.apk"
    command = "zipalign -f -v 4 " + src_name + " " + des_name
    print("exec: " + command)
    os.system(command)
    return des_name

def unpack(src_name):
    des = os.path.splitext(src_name)[0]
    if os.path.isdir(des):
        shutil.rmtree(des)

    command = "apktool d " + src_name + " -o " + des
    print("exec: " + command)
    os.system(command)
    return des

def pack(src_name):
    if src_name.endswith("/"):
        src_name = src_name[:len(src_name) - 1]

    des = os.path.splitext(src_name)[0] + "_repacked.apk"
    if os.path.isfile(des):
        os.remove(des)

    command = "apktool b " + src_name + " -o " + des
    print("exec: " + command)
    os.system(command)
    return des

def __main__():

    # self_install
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        self_install("apkex.py", "/usr/local/bin")
        return

    if len(sys.argv) <= 2:
        print("apkex\n\tu:unpack [src]\n\tp:pack [src]\n")
        return

    if len(sys.argv) > 2:
        cmd = sys.argv[1]
        path = sys.argv[2]

        if not str(path).startswith("/"):
            path = os.path.join(os.getcwd(), path)

        if cmd == "u":
            tmp = unpack(path)
            print("\n\nunpack to: " + tmp)
        elif cmd == "p":
            packed = pack(path)
            print("\n\npack to: " + packed)
            signed = sign(packed)
            print("\n\nsign to: " + signed)
            aligned = align(signed)
            print("\n\nalign to: " + aligned)
            os.remove(packed)
            os.remove(signed)
        else:
            print("apkex\n\tu:unpack [src]\n\tp:pack [src]\n")

__main__()
