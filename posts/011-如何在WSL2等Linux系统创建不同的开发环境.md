---
title: 如何在WSL2等Linux系统创建不同的开发环境
date: 2022-03-16 02:43:26
categories: 
    - 技术
tags: 
    - WSL
    - 开发环境
    - systemd-nspawn
disc: 这篇文章本应该去年11月就写出来的...
---

## 首先是，为什么

在去年11月的时候，因为某种原因需要为一台系统版本非常古老的Linux机器上编译一个程序。因为这个系统一直没有更新过，glibc处于一个非常低的版本，在其他环境编译出来的程序显然是不能在这台机器上正常运行的。而我并不想在这台系统版本已经停止支持（没错，就是CentOS6）、很多软件没有更新、包管理器完全无法使用并且性能非常令人感叹的祖传传家宝上安装编译环境，所以只能找一个类似的环境编译出来然后把编译结果拷贝上去运行。

显然，最容易创建这样一个环境的方法就是`docker pull`一把梭了。但是鉴于docker对这样的经常需要在容器里面敲命令的场景不太友好，而且从外部操作它的文件系统的方式真的一言难尽，总而言之就是不太合适，所以直接被排除了。

我想要的是将一个操作系统的文件放置在一个目录，然后直接切换进去。大家喜闻乐见的`chroot`可以做到这一点，但是作为实用环境的话`proc`和`dev`这些目录都需要自己mount进去，或者写脚本完成，总之比较麻烦。

最后我选择了在WSL里面使用`systemd-nspawn`来完成，使用Linux环境的朋友可以直接使用。尤其是日常使用Linux桌面的朋友可以尝试一下用来运行某些比较坑爹的国产软件或者其他什么东西。

## 为WSL2安装systemd

WSL2是Windows中利用虚拟化等技术运行完整的Linux系统提供给开发人员使用的组件。具体怎么安装就不赘述了，自己搜索一下就知道了。

但是，WSL启动使用的init是微软自己写的，而`systemd-nspawn`顾名思义需要使用systemd作为init，所以得好办法在WSL中启动systemd。好在已经有好心人提供了[相关项目][systemd-genie]。

我们按照项目说明的直接进行安装。比如我使用的是Arch的WSL，~~所以直接从[AUR][AUR]安装~~。（因为连GitHub太慢了导致安装失败，所以还是从release页面下载`.tar.zst`后缀的安装包安装了）使用其他发行版的就到release界面找对应的安装包，如果没有就想办法自己安装吧。

关闭WSL虚拟机：

```shell
wsl --shutdown
```

然后在Windows终端执行以下命令启动WSL中的systemd守护进程：

```shell
# 启动systemd，并开启一个shell使用
wsl genie -s
```

然后我们就能看到systemd相关的进程了：

```plaintext
➜  ~ pstree -pt
systemd(1)─┬─(agetty)(78)
           ├─agetty(79)
           ├─dbus-daemon(75)
           ├─systemd(103)───(sd-pam)(104)
           ├─systemd-journal(30)
           ├─systemd-logind(76)
           ├─systemd-machine(99)
           ├─systemd-udevd(39)
           └─zsh(100)───pstree(503)
```

## 下载系统镜像并提取

### 直接下载需要的镜像

因为我显然不想自己用安装镜像安装一次系统，所以决定去找找有没有现成的rootfs可以下载。

然后在进行一些搜索之后，发现了某云服务相关的企业提供了一些镜像的[下载页面][dl1]。

但是我需要的CentOS6的镜像并不在其中，毕竟已经停止支持了嘛。所以只能另寻提供CentOS镜像下载的地方。

作为整了这么多年VPS的老油条，很多云服务商会提供ovz虚拟化的主机，并且提供一个很老版本的系统。那么OpenVZ应该会提供CentOS6的镜像吧。果不其然，在OpenVZ的支持页面找到了[下载模板的地方][dl2]，其中就包括我需要的CentOS6的镜像。下载之后解压到磁盘就行了。

某些发行版或者应用官方也会提供预安装的镜像下载，如果需要也可以找找看。

### 从Docker导出

或者我们可以直接用docker导出到文件系统，这样有更多的选择。

首先，将需要的镜像pull下来：

```shell
docker pull docker:6
```

然后我们需要创建一个container：

```shell
docker run --name centos centos:6

# 或者不运行直接创建
docker container create --name centos centos:6
```

最后将容器导出就行了：

```shell
cd centos

docker export centos | tar xf -
```

### 从安装镜像/LiveCD/安装程序安装

如果你使用的是ArchLinux的话，可以直接使用`pacstrap`命令生成一个新的系统环境。

如果是其他发行版，比如Fedora、CentOS、Ubuntu等等，应该也有类似的程序。例如Debian的`debootstrap`和`cdebootstrap`，使用CentOS的可以用`rpm --root <path> -initdb`，用Fedora的也可以使用`dnf --installroot=<path> groupinstall core`等等。

或者使用[`livemedia-creator`][livemedia-creator]等工具生成。

## 启动并进入容器

我们切换到centos的rootfs所在的目录，然后运行：

```shell
systemd-nspawn -a bash
```

然后报错了：

```plaintext
➜  centos systemd-nspawn -a
Spawning container centos on /opt/centos.
Press ^] three times within 1s to kill container.

Container centos failed with error code 255.
```

当时我经过了漫长的搜索，终于在某个[issue][vsyscall-issua]找到了原因。~~（然后现在的我完全忘掉了这档子事，只记得CentOS6需要wsl2启动的时候加一个参数，又花了很多时间搜索了一遍）~~

因为CentOS6的glibc中使用`vsyscall`调用，而64位系统不使用该调用并且在高版本的内核中默认启动参数中不会开启这个调用。我们只能在wsl启动时声明启用模拟`vsyscall`。

在Windows的用户目录创建一个`.wslconfig`文件，并填入以下内容并重启wsl虚拟机：

```ini
[wsl2]
kernelCommandLine = vsyscall=emulate
```

然后后我们看看是否生效：

```plaintext
➜  ~ cat /proc/cmdline
initrd=\initrd.img panic=-1 pty.legacy_count=0 nr_cpus=16 vsyscall=emulate
```

再次使用`systemd-nspawn`，就能进入系统了.

```plaintext
➜  centos systemd-nspawn -a
Spawning container centos on /opt/centos.
Press ^] three times within 1s to kill container.
[root@centos ~]# cat /etc/centos-release
CentOS release 6.10 (Final)
```

## 修改软件源并安装开发环境

因为CentOS已经停止支持，官方的软件源也被删除了，所以我们只能用某些还在为CentOS提供服务的镜像源，例如[阿里源][mirror-ali]和[清华源][mirror-tsinghua]。

这里我们按照清华源的[帮助][mirror-help]，执行以下代码替换软件源：

```shell
minorver=6.10
sed -e "s/^mirrorlist=/#mirrorlist=/g" \
         -e "s/^#baseurl=http:\/\/mirror.centos.org\/centos\/\$releasever/baseurl=https:\/\/mirrors.tuna.tsinghua.edu.cn\/centos-vault\/$minorver/g" \
         -i.bak \
         /etc/yum.repos.d/CentOS-*.repo
```

然后执行更新系统，并安装需要的开发工具：

```shell
yum update

yum groupinstall "development tools"
```

然后就能用来编译需要的程序了。

```plaintext
$ gcc -v
Using built-in specs.
Target: x86_64-redhat-linux
Configured with: ../configure --prefix=/usr --mandir=/usr/share/man --infodir=/usr/share/info --with-bugurl=http://bugzilla.redhat.com/bugzilla --enable-bootstrap --enable-shared --enable-threads=posix --enable-checking=release --with-system-zlib --enable-__cxa_atexit --disable-libunwind-exceptions --enable-gnu-unique-object --enable-languages=c,c++,objc,obj-c++,java,fortran,ada --enable-java-awt=gtk --disable-dssi --with-java-home=/usr/lib/jvm/java-1.5.0-gcj-1.5.0.0/jre --enable-libgcj-multifile --enable-java-maintainer-mode --with-ecj-jar=/usr/share/java/eclipse-ecj.jar --disable-libjava-multilib --with-ppl --with-cloog --with-tune=generic --with-arch_32=i686 --build=x86_64-redhat-linux
Thread model: posix
gcc version 4.4.7 20120313 (Red Hat 4.4.7-23) (GCC)
```

## 关于systemd-nspawn

这里只是简单地使用了一下systemd-nspawn，甚至这个场景都不需要这么复杂的工具。更多的使用说明参看[ArchLinux Wiki][wiki]。

对于使用Linux发行版作为日常使用的桌面环境的人来说，使用这个工具会很方便，毕竟大多数桌面发行版都带systemd，而且也没必要使用docker完成一些简单的事情。而且写好的配置文件放进systemd的目录，这样每次启动也会方便很多。

在我还在使用Linux系统的时候就为了对付某些毒瘤软件使用过。例如，使用systemd-nspawn运行完整的deepin系统然后运行Te\*\*\*nt家的某没有Linux版本的IM软件，虽然也有人封装了`deepin-wine`系列软件，但在原生系统上面运行毕竟~~naive~~一些。又比如，某Ne\*\*\*se家的某音乐播放器的缓存会非常大，甚至某个版本还必须用root权限否则没法启动，就可以用systemd-nspawn运行，并且给他的缓存目录挂一个tmpfs。

[systemd-genie]: https://github.com/arkane-systems/genie
[AUR]: https://aur.archlinux.org/packages/genie-systemd-git
[dl1]: https://uk.lxd.images.canonical.com/images/
[dl2]: https://download.openvz.org/template/precreated/
[livemedia-creator]: https://weldr.io/lorax/livemedia-creator.html
[vsyscall-issua]: https://github.com/microsoft/WSL/issues/4694
[mirror-ali]: https://mirrors.tuna.tsinghua.edu.cn/centos-vault/
[mirror-tsinghua]: https://mirrors.tuna.tsinghua.edu.cn/centos-vault/
[mirror-help]: https://mirrors.tuna.tsinghua.edu.cn/help/centos-vault/
[wiki]: https://wiki.archlinux.org/title/systemd-nspawn
