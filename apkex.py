#!/usr/bin/env python3
import sys
import os
import json
import shutil
import subprocess

G_ADB = ""
G_ZIPALIGN = ""
G_apksigner = ""


def init_tools():
    global G_ADB
    global G_ZIPALIGN
    global G_apksigner

    android_sdk_path = os.environ.get(
        'ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    if android_sdk_path is None or (not os.path.isdir(android_sdk_path)):
        android_sdk_path = "/Users/Shared/Android/sdk"
    if not os.path.isdir(android_sdk_path):
        android_sdk_path = os.path.expanduser("~/Library/Android/sdk")
    if not os.path.isdir(android_sdk_path):
        print("ANDROID_HOME or ANDROID_SDK_ROOT not found")
        exit(1)

    platform_tools_path = os.path.join(android_sdk_path, "platform-tools")

    G_ADB = os.path.join(platform_tools_path, "adb")

    build_tools_path = os.path.join(android_sdk_path, "build-tools")
    build_tools_list = os.listdir(build_tools_path)
    build_tools_list.sort()

    last_build_tool = os.path.join(build_tools_path, build_tools_list[-1])

    if os.path.isdir(last_build_tool):
        G_ZIPALIGN = os.path.join(last_build_tool, "zipalign")
        G_apksigner = os.path.join(last_build_tool, "apksigner")
        # os.system(G_ADB + " kill-server")


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


def read_config(conf_file_path):
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


def sign(src_name, conf):
    if not param_exists(src_name):
        print("no src name input, exit")
        return

    des_name = os.path.splitext(src_name)[0] + "_resigned.apk"

    key_path = conf["key_path"]
    alias_name = conf["alias_name"]
    store_pwd = conf["store_pwd"]
    key_pwd = conf["key_pwd"]

    command = "jarsigner -verbose"
    command += " -keystore '" + key_path + "'"
    command += " -digestalg SHA1"
    command += " -sigalg MD5withRSA"
    command += " -storepass '" + store_pwd + "'"
    command += " -keypass '" + key_pwd + "'"
    command += " -signedjar '" + des_name + "'"
    command += " '" + src_name + "' '" + alias_name + "'"

    print("exec: " + command)
    os.system(command)
    return des_name


def align(src_name):
    des_name = os.path.splitext(src_name)[0] + "_aligned.apk"
    command = G_ZIPALIGN + " -f -v 4 " + src_name + " " + des_name
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


def pack_unity(src_name):
    if src_name.endswith("/"):
        src_name = src_name[:len(src_name) - 1]

    log_path = os.path.join(os.path.expanduser(
        "~"), "Library/Logs/Unity/Editor.log")
    if os.path.isfile(log_path):
        os.remove(log_path)

    command = "/Applications/Unity/Unity.app/Contents/MacOS/Unity -projectPath " + src_name \
              + " -batchmode -executeMethod PerformBuild.BuildAndroid -quit"
    print("exec: " + command)
    os.system(command)

    f = open(log_path, mode='rb')
    print(f.read())
    f.close()


def __main__():
    init_tools()

    # self_install
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        self_install("apkex.py", "/usr/local/bin")
        return

    argLen = len(sys.argv)

    cmd = ""
    cfg = ""
    path = ""

    idx = 1
    while idx < argLen:
        cmd_s = sys.argv[idx]
        if cmd_s[0] == "-":
            c = cmd_s[1:]
            v = sys.argv[idx + 1]
            if c == "c":
                cmd = v
            elif c == "g":
                cfg = v
            elif c == "f":
                path = v
            idx += 2
        else:
            idx += 1

    if path == "":
        print("using apkex "
              "\n\t-c [u unpack;"
              "\n\t\tp pack;"
              "\n\t\ts print sign] "
              "\n\t-f [file path] "
              "\n\t-g [config file path] "
              "\n\tto run with apktool")
        return

    # if not os.path.isabs(path):
    #     path = os.path.join(os.getcwd(), path)

    if cmd == "u":
        tmp = unpack(path)
        print("\n\nunpack to: " + tmp)
    elif cmd == "p":
        if cfg == "":
            print("using apkex "
                  "\n\t-c [u unpack;"
                  "\n\t\tp pack;"
                  "\n\t\ts print sign] "
                  "\n\t-f [file path] "
                  "\n\t-g [config file path] "
                  "\n\tto run with apktool")
            return

        if not os.path.isabs(cfg):
            cfg = os.path.join(os.getcwd(), cfg)

        cfg_folder = os.path.dirname(cfg)

        conf = read_config(cfg)

        if not os.path.isabs(conf["key_path"]):
            conf["key_path"] = os.path.join(cfg_folder, conf["key_path"])

        packed = pack(path)
        print("\n\npack to: " + packed)
        signed = sign(packed, conf)
        print("\n\nsign to: " + signed)
        aligned = align(signed)
        print("\n\nalign to: " + aligned)
        os.remove(packed)
        os.remove(signed)
    elif cmd == "s":

        command = G_apksigner + " verify -v " + path
        print("exec: " + command)
        os.system(command)

        apk_results = run_cmd(
            ['keytool', "-list", "-printcert", '-jarfile', path])
        print('check apk sign')
        print(apk_results)

        if not cfg == "":
            if not os.path.isabs(cfg):
                cfg = os.path.join(os.getcwd(), cfg)

            cfg_folder = os.path.dirname(cfg)

            conf = read_config(cfg)

            if not os.path.isabs(conf["key_path"]):
                conf["key_path"] = os.path.join(cfg_folder, conf["key_path"])

            key_results = run_cmd(['keytool', "-list",
                                   "-alias", conf["alias_name"],
                                   '-keystore', conf["key_path"],
                                   '-storepass', conf["store_pwd"],
                                   '-keypass', conf["key_pwd"],
                                   '-v'])
            print('check key sign')
            print(key_results)

            apk_lines = apk_results.split('\n')
            for l in apk_lines:
                if l.strip().startswith('MD5: '):
                    apk_md5 = l.strip()
                    break

            key_lines = key_results.split('\n')
            for l in key_lines:
                if l.strip().startswith('MD5: '):
                    key_md5 = l.strip()
                    break

            print('apk md5:')
            print(apk_md5)
            print('key md5:')
            print(key_md5)

            if apk_md5 == key_md5:
                print('check match')
            else:
                print('check not match')

    elif cmd == "unity":
        pack_unity(path)
    else:
        print("using apkex "
              "\n\t-c [u unpack;"
              "\n\t\tp pack;"
              "\n\t\ts print sign] "
              "\n\t-f [file path] "
              "\n\t-g [config file path] "
              "\n\tto run with apktool")


__main__()
