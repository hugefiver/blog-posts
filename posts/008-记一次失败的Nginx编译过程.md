---
title: 记一次失败的Nginx编译过程
date: 2020-07-28 14:45:40
categories: 
    - 技术
tags: 
    - Nginx
---



最近要想做一个Nginx的docker镜像，写惯了Golang的我当然选择静态链接所有的库。可是事情远没有我想象中那么简单。

<!--more-->

## 下载依赖

1. 首先我们需要下载一些依赖库的源码，其实用包管理安装也行，不过为了更加通用还是直接用源码吧。

    我们需要的库有 `zlib` `prce` `boringssl`，其中`boringssl`是Google开发的`openssl`的分支，在这里替代`openssl`。

    ```makefile
    dep: get-nginx get-zlib get-pcre get-ssl
    get-nginx:
           curl $(nginx_url) -o $(nginx_file)
           tar zxf $(nginx_file) -C lib
           rm $(nginx_file)

    get-ssl:
           git clone --depth 1 https://github.com/google/boringssl.git lib/boringssl

    get-zlib:
           curl $(zlib_url) -o $(zlib_file)
           tar zxf $(zlib_file) -C lib
           rm $(zlib_file)

    get-pcre:
           curl $(pcre_url) -o $(pcre_file)
           tar zxf $(pcre_file) -C lib
           rm $(pcre_file)
    ```

2. 接着编译`boringssl`。

    ```makefile
    build-ssl:
        cd lib/boringssl && \
            mkdir -p build .openssl/{lib,include}
        cd lib/boringssl && \
            ln -sf `pwd`/include/openssl .openssl/include/
        cd lib/boringssl && cmake -S ./ -B build/ -DCMAKE_BUILD_TYPE=Release
        cd lib/boringssl && make -C build/ -j $(compile_process)
        cd lib/boringssl && \
            cp build/crypto/libcrypto.a build/ssl/libssl.a .openssl/lib
    ```

    不过`Makefile`每行命令在独立的shell里面运行确实有点烦，看着这么多东西其实全都是切换目录，其实也就那么点命令。

    ```shell
    cd lib/boringssl
    mkdir -p build .openssl/{lib,include/openssl}
    # ln -sf `pwd`/include/openssl .openssl/include/
    cp include/openssl/* .openssl/include/openssl
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cd build
    make -j2
    cp crypto/libcrypto.a ssl/libssl.a ../.openssl/lib
    ```

3. 然后运行`make dep; make build-ssl`就会下载依赖。（如果没有`make` `cmake` `gcc/clang` `golang` 要先安装这些 ）

## 编译Nginx

首先我们得切换到`Nginx`源码所在目录。

接着生成Nginx的Makefile。

```bash
# 传入静态编译/链接参数，一般情况不用设置
# export CC_OPTS="-static" LD_OPTS="-static"
./configure \
 --prefix=/opt/nginx \
    --sbin-path=/usr/sbin/nginx \
    --user=nginx --group=nginx \
    --modules-path=/opt/nginx/modules \
    --conf-path=/etc/nginx/nginx.conf \
    --error-log-path=/var/nginx/error.log \
    --http-log-path=/var/nginx/access.log \
    --with-cc-opt="-O2 $CC_OPTS" \
    --with-ld-opt="$LD_OPTS" \
    --with-file-aio \
    --with-stream \
    --with-stream_ssl_module \
    --with-stream_ssl_preread_module \
    --with-http_auth_request_module \
    --with-http_ssl_module \
    --with-http_v2_module \
    --with-http_realip_module \
    --with-http_addition_module \
    --with-pcre=../$(pcre) --with-pcre-jit \
    --with-zlib=../$(zlib) \
    --with-openssl=../$(boringssl)
```

然后记得要执行一下以下命令。

```bash
touch ../boringssl/.openssl/include/openssl/ssl.h
```

这个操作看起来不起眼，但是非常关键。`make`的时候会根据这个文件判断使用的`openssl`是不是最新的编译版本，如果是过时的编译它就会自己编译一份。但是因为我们用的不是原版`openssl`所以并不可能编译成功。

之后直接`make -j 4`就行了...本来应该是这样的。

## 神秘的问题

编译很正常的进行下去并完成。按照一般情况，这时候直接`make install`就行了。

但是我在查看输出信息的时候看到了这样的警告。

```plain
cc -o objs/nginx \
objs/src/core/nginx.o \
...
-static -ldl -lpthread -lcrypt ../pcre-8.43/.libs/libpcre.a ../boringssl/.openssl/lib/libssl.a ../boringssl/.openssl/lib/libcrypto.a -ldl -lpthread ../zlib-1.2.11/libz.a \
-Wl,-E
/usr/sbin/ld: objs/src/core/nginx.o: in function `ngx_load_module':
src/core/nginx.c:1523: warning: Using 'dlopen' in statically linked applications requires at runtime the shared libraries from the glibc version used for linking
/usr/sbin/ld: objs/src/os/unix/ngx_process_cycle.o: in function `ngx_worker_process_init':
src/os/unix/ngx_process_cycle.c:836: warning: Using 'initgroups' in statically linked applications requires at runtime the shared libraries from the glibc version used for linking
...
```

警告说：链接的时候发现即使是静态链接了，运行时使用某些glibc的函数时还是需要相应的动态链接库。

我当场就一万个问号：竟然还有这种操作？想想看可能libc里面里面也有不少依赖内核的系统调用吧，需要根据每个系统内核版本编译可以使用的libc。可能。

既然这样，那就不静态链接libc了呗。查了一下`ld`的帮助，看到了这样的参数。

```plain
-Bdynamic -dy -call_shared
    Link against dynamic libraries.  ...

-Bstatic -dn -non_shared -static
    Do not link against shared libraries.  ...
```

那就把链接参数改成了这样。

```plain
--with-ld-opt="-Wl,-dy -lc -Wl,-static"
```

但是这样的参数会在`./configure`的时候报错。

```plain
checking for int size ...auto/types/sizeof: line 43: objs/autotest: No such file or directory
  bytes
```

emmm...好像是检查`sizeof`也就是各种基本类型的位长的时候出错了。

那就手动改脚本吧。绕过之后发现还是编译失败了。链接的时候说没有找到`-lgcc_s`。

然后我就放弃了。

## 随后可能尝试的解决方法

第一种还是静态编译，就是不使用`glibc`，转而使用`musl-libc`。不过不知道会不会出现一样的情况，而且docker钦定的镜像`Alphine`就是使用的`musl`，所以意义不太大。

第二种是放弃静态编译，编译一份`glibc`部署的时候把需要使用的链接库附带进去，或者直接用系统的。

可能也有办法只动态链接部分不能静态链接的`glibc`吧，之后看看`ld`里面还有什么参数。

就这么一个小问题浪费了我整整一周的时间。连链接这种事情都要自己干预的情况，可能写`Golang`/`Rust`这些基本不可能碰到吧，更不用说写`Python`/`JS`/`Java`这种VM语言了。
