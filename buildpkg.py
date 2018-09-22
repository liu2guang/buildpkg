# -*- coding:utf-8 –*- 
# @File:   buildpkg.py 
# @Author: liu2guang
# @Date:   2018-09-19 18:07:00
#
# @LICENSE: GPLv3: https://github.com/rtpkgs/buildpkg/blob/master/LICENSE.
#
# Change Logs:
# Date           Author       Notes 
# 2018-09-19     liu2guang    The first version. 

# --------------------------------------------------------------------------------
# import module 
# --------------------------------------------------------------------------------
import os, sys 
import logging
import json
import argparse
import time
import shutil 
import platform

# --------------------------------------------------------------------------------
# @ 发布信息 
# @ Todo: 
#     1. 实现发布和调试配置的功能, 方便以后开发. 
# --------------------------------------------------------------------------------
_BUILDPKG_VERSION = "v0.2.0" 
_BUILDPKG_AUTHOR  = "liu2guang" 
_BUILDPKG_LICENSE = "GPLv3" 
_BUILDPKG_RELEASE = False

# --------------------------------------------------------------------------------
# @ 创建运行日志和Package生成日志
# @ Note: 
#     1. 运行日志是存储在"buildpkg.log"文件中. 
#     2. Package构建信息日志是存储在"packages/pkglist.log"中, INFO等级. 
#     3. 发布时run log写入文件中等级需要是最低的, 控制台的等级需要是INFO. 
# 
# @ Todo: 
#     1. 优化日志打印格式.  
#     2. 实现捕获所有异常这样日志才有作用, 还有就是邮箱发送日志? 
#     3. 优雅的实现这部分代码, 感觉很奇怪说不上来. 
# --------------------------------------------------------------------------------
_BUILDPKG_LOG_FORMAT = "[%(asctime)s %(filename)s L%(lineno).4d %(levelname)-8s]: %(message)s" 

# check packgae directory is exist
if os.path.exists("packages") == False: 
    os.makedirs("packages") 

def _buildpkg_run_log(file): 
    log = logging.getLogger("buildpkg") 
    log.setLevel(logging.DEBUG)
    format = logging.Formatter(_BUILDPKG_LOG_FORMAT)

    c = logging.StreamHandler()
    f = logging.FileHandler(file)
    c.setFormatter(format)
    f.setFormatter(format)
    c.setLevel(logging.DEBUG) 
    f.setLevel(logging.DEBUG)
    log.addHandler(c) 
    log.addHandler(f) 

    return log

def _buildpkg_pkg_log(file): 
    log = logging.getLogger("pkglist") 
    log.setLevel(logging.DEBUG)
    format = logging.Formatter(_BUILDPKG_LOG_FORMAT)

    f = logging.FileHandler(file)
    f.setFormatter(format)
    f.setLevel(logging.DEBUG)
    log.addHandler(f) 

    return log

run_log = _buildpkg_run_log("buildpkg.log") 
pkg_log = _buildpkg_pkg_log("packages/pkglist.log") 

# --------------------------------------------------------------------------------
# @ 命令配置
# @ Note: 
#     1. action: 
#           1. make: 构建或者迁移仓库, 可以构建空仓库, 也可以迁移开源的仓库. 
#           2. update: 更新readme, 版本号, scons脚本. 
#     2. pkgname: 构建或者迁移仓库时的生成的本地仓库的名称, 迁移仓库时可以不指定pkgname, 
#                 会自动从git地址去获取名称.
#     3. pkgrepo: 迁移仓库时的git地址. 
#     4. version: 构建或者迁移仓库时指定版本, 可选配置, 没有配置时默认为v1.0.0, 默认配置
#                 可以在"config.json"中的"pkg_def_version"进行修改配置. 
#     5. license: 构建或者迁移仓库时指定许可证, 支持的许可证类型有以下种类: 
#                 agpl3, apache, bsd2, bsd3, cddl, cc0, epl, gpl2, gpl3, lgpl, mit, mpl
#                 没有指定许可证时默认不添加许可证. 
# 
# @ Todo: 
#     1. 关于make同时构建或者迁移是否可以分为2个指令, create/transplant?. 
#     2. 实现捕获所有异常这样日志才有作用, 还有就是邮箱发送日志? 
#     3. 优雅的实现这部分代码, 感觉很奇怪说不上来. 
# --------------------------------------------------------------------------------
parser = argparse.ArgumentParser(
    description = "Quick build rt-thread pkg toolkits")
parser.add_argument(  "action"   ,        type = str, help = "The action of build package by buildpkg", choices=["make", "update"]) 
parser.add_argument(  "pkgname"  ,        type = str, help = "The package name to be make or update", nargs = "?") 
parser.add_argument(  "pkgrepo"  ,        type = str, help = "To make the package from the specified git repository", nargs = "?") 
parser.add_argument("--version"  , "-v" , type = str, help = "The package version to be make or update") 
parser.add_argument("--license"  , "-l" , type = str, help = "The package license to be make or update, one of: agpl3, apache, bsd2, bsd3, cddl, cc0, epl, gpl2, gpl3, lgpl, mit, mpl") 
parser.add_argument("--remove-submodule", action='store_true', help = "Remove the submodule of repository")

# Load buildpkg config 
# Todo: try
with open("config.json", 'r') as f:
    _config = json.load(f)
    run_log.debug("Read config: \n" + json.dumps(_config, indent=4)) 

# generate file
def _buildpkg_generate_file(template_name, pkgname, target_path, replace_list): 
    run_log.info("Ready add %s file." % (target_path)) 
    run_log.debug("Replace the list is " + str(replace_list)) 

    template_path = os.path.join("template", _config["template"][template_name])
    target_file_path = os.path.join("packages", pkgname, target_path) 
    # print(template_path)
    # print(target_file_path)

    if sys.version_info < (3, 0): 
        with open(template_path, 'r') as file_in, open(target_file_path, 'w+') as file_out: 
            textlist = file_in.readlines()
            for line in textlist: 
                for (key, value) in replace_list.items():
                    line = line.replace("{{" + key + "}}", value) 
                file_out.write(line) 
    else: 
        with open(template_path, 'r', encoding='utf-8') as file_in, open(target_file_path, 'w+', encoding='utf-8') as file_out: 
            textlist = file_in.readlines()
            for line in textlist: 
                for (key, value) in replace_list.items():
                    line = line.replace("{{" + key + "}}", value) 
                file_out.write(line) 

    run_log.info("Add %s file success." % (target_path)) 

# buildpkg cmd
def _buildpkg_make_package(pkgname = None, pkgrepo = None, version = _config["pkg_def_version"], license = None, remove_submodule = False): 
    base_repo_flag = False

    if version == None: 
        version = _config["pkg_def_version"]

    if pkgname == None and pkgrepo == None: 
        run_log.error("Please input pkgname or pkgrepo while you make package!") 
        run_log.error("Stop make package!\n") 
        exit(1); 

    # 2. buildpkg make cstring 
    # 3. buildpkg make https://github.com/liu2guang/cstring.git
    if pkgname != None and pkgrepo == None: 
        if pkgname.endswith(".git") == True: 
            package_name = pkgname.split("/")[-1].replace(".git", "") 
            pkgrepo = pkgname
        else: 
            package_name = pkgname
            base_repo_flag = True

    # 4. buildpkg make cstring https://github.com/liu2guang/cstring.git 
    elif pkgname != None and pkgrepo != None: 
        package_name = pkgname

    run_log.info("The package name is %s." % (package_name)) 
    run_log.info("The package repo addr is %s." % (pkgrepo)) 

    package_path = os.path.join("packages", package_name) 

    # check package/pkgname directory is exist 
    if os.path.exists(package_path) == True: 
        package_path_backup = package_path + "_backup_" + time.strftime("%y%m%d_%H%M%S", time.localtime()) 
        run_log.warning("\"%s\" already existed, backup to \"%s\"" %(package_path, package_path_backup))
        os.rename(package_path, package_path_backup)

    os.makedirs(package_path) 
    run_log.info("\"%s\" directory create success!" % (package_path)) 

    username = _config["username"]

    # 1. add readme.md 
    replace_list = {
        "username": username, 
        "pkgname": package_name, 
        "version": version
        }
    _buildpkg_generate_file("readme", package_name, "readme.md", replace_list) 

    # 2. add example dir and xxx_example.c + SConscript
    example_path = os.path.join(package_path, "example") 
    example_c_path = os.path.join(example_path, package_name + "_example.c") 
    os.makedirs(example_path) 
    with open(example_c_path, "a+") as fp: 
        pass
    replace_list = {
        "pkgname": package_name, 
        "version": version, 
        "pkgname_letter": package_name.upper()
        }
    _buildpkg_generate_file("sconscript-example", package_name, os.path.join("example", "SConscript"), replace_list) 

    # 3. add SConscript 
    replace_list = {
        "pkgname": package_name, 
        "version": version, 
        "pkgname_letter": package_name.upper(), 
        "list_ignore_inc": str(_config["list_ignore_inc"]), 
        "list_ignore_src": str(_config["list_ignore_src"])
        }
    _buildpkg_generate_file("sconscript", package_name, "SConscript", replace_list) 

    # 4. add github ci and copy 'template/bsp_script/' to 'pkg/scripts'
    replace_list = {
        "username": username, 
        "pkgname": package_name
        } 
    _buildpkg_generate_file("github-ci", package_name, ".travis.yml", replace_list) 
    shutil.copytree(os.path.join("template", "bsp_script"), os.path.join("packages", package_name, "scripts"))

    # 5. add license 
    if license != None: 
        run_log.info("add package %s license." % (license)) 
        cmd = "lice " + license.lower() + " -f " + os.path.join(package_path, "license") + " -o " + _config["username"]
        os.system(cmd) 
        run_log.info("add package license success.") 

    # 6. init git repo
    run_log.info("add git repository.") 
    pwd = os.getcwd()
    os.chdir(package_path) 
    os.system("git init") 
    run_log.debug("Initialize the git repository success") 

    # 6. add git repo
    if base_repo_flag == False: 
        if remove_submodule == True: 
            os.system('git clone --progress --recursive ' + pkgrepo + " " + package_name) 
            os.chdir(package_name) 
            git_removepath = os.path.join(os.getcwd(), '.git') 
            if platform.system() == 'Windows':
                run_log.debug("Windows platform") 
                os.system('attrib -r ' + git_removepath + '\\*.* /s') # 递归修改windows下面的只读文件为可读属性
            elif platform.system() == 'Linux': 
                run_log.debug("Linux platform") # Todo
            else:
                run_log.debug("Other platform") # Todo

            shutil.rmtree(git_removepath) 
            run_log.debug("Add the \"%s\" repository code" % (package_name)) 
        else: 
            os.system("git submodule add " + pkgrepo) 
            run_log.debug("Add the \"%s\" git submodule" % (package_name)) 
        run_log.info("add git repository success.") 

    os.chdir(pwd) 

    # 7. commit the first commit
    run_log.info("commit the first commit.") 
    pwd = os.getcwd()
    os.chdir(package_path) 

    # Prevent git from generating warnings: LF will be replaced by CRLF
    if(platform.system() == 'Windows'):
        os.system('git config --global core.autocrlf false') 

    os.system('git add -A') 
    commit_content = _config["commit_content"]
    os.system("git commit -m \"" + commit_content.replace("{{pkgname}}", package_name) + "\"") 
    os.chdir(pwd) 
    run_log.info("commit the first commit success.") 

    # 8. add pkg list log
    pkg_log.info("build package success: '%s'." % (package_name))

if __name__ == "__main__":
    run_log.info("Start run buildpkg") 
    run_log.info("Current buildpkg version %s" % (_BUILDPKG_VERSION)) 

    # parse and print input args 
    args = parser.parse_args() 
    run_log.debug(args) 

    # build package
    if args.action == "make": 
        run_log.info("The package is being built.") 
        _buildpkg_make_package(args.pkgname, args.pkgrepo, args.version, args.license, args.remove_submodule) 
        run_log.info("To completion package build.\n") 
    elif args.action == "update": 
        run_log.info("The package is being update.") 
        run_log.info("To completion package update.\n") 
