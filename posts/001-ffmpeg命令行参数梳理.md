---
title: ffmpeg命令行参数梳理
date: 2018-05-05 13:19:51
categories: 
    - 技术
tags: 
    - ffmpeg
---


最近因为要处理一些视频，无奈Linux环境也没有什么简便的小工具，就看了看久仰大名的`ffmpeg`的文档。准备把常用的选项写下来供以后查找。
<!--more-->

## 安装ffmpeg

### Ubuntu

对于我们这些普通人来说，ffmpeg也就偶尔用用。日常使用Linux的话，大部分人应该都会选择Ubuntu（或者Debian的衍生版本）吧。

Ubuntu的仓库有ffmpeg，直接用`apt`拿出来就行了。（也许是我改了源的原因，如果默认仓库没有的话就在源里加上`universe`组件，[中科大镜像源的ffmpeg](https://mirrors.ustc.edu.cn/ubuntu/pool/universe/f/ffmpeg/)。）

```bash
sudo apt-get install ffmpeg
```

### CentOS

有时候在VPS上下了一些视频（我的服务器OS都是CentOS），希望处理一下再拉回本地（不过VPS的性能堪忧，当然就算处理十天半个月也不打紧的啦），就需要在CentOS上安装ffmpeg了。CentOS官方的仓库中并没有提供ffmpeg，可以选择编译安装或者安装第三方源。以下安装第三方源。

CentOS6

```bash
sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el6/x86_64/nux-dextop-release-0-2.el6.nux.noarch.rpm
```

CentOS7

```bash
sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-5.el7.nux.noarch.rpm
```

然后安装：

```bash
sudo yum install ffmpeg
```

### Windows

Windows有很多功能相近的图形工具，ffmpeg能实现的功能基本都能实现而且更简单（可能有的就是ffmpeg套个图形界面）。推荐[小丸工具箱](https://maruko.appinn.me/)。

### Others

其他操作系统诸如MacOS、Debian之类应该也是可以使用包管理安装的。

也可以选择下载源码编译安装（[GitHub](https://github.com/FFmpeg/FFmpeg/releases)）。不过依赖很多，可能会很麻烦。

## 命令行选项

ffmpeg处理媒体文件的命令行参数结构大概是这样的：

```bash
ffmpeg  [[输入文件选项]  -i 输入文件名]...  [输出选项]  <输出文件名> 
 ```

通过 `ffmpeg --help` 或者 `ffmpeg -h` 即可看到可以使用的选项。

### 常用选项整理

#### 文件处理选项

```text
-f    文件格式
-c    编码
-codec   同上
-preset   preset
-t    截取媒体文件_（持续）时间（秒）
-to    截取媒体文件_结束时间（秒或时间格式[[[hh:]mm:]ss]）
-ss    截取媒体文件_开始时间（秒或时间格式[[[hh:]mm:]ss]）
-sseof   截取媒体文件_距离结束的时间长度
-fs    文件大小限制（bytes）
-frames <number> 输出文件的帧数
-filter   设置过滤器选项
-filter_script <filename> 从文件读取过滤器选项
-threads <number> 多线程处理
```

#### 视频选项

```text
-vframes <number> 输出视频帧数
-vf   同上
-r   输出视频帧率
-s <nxm> 设置输出画面大小（宽：n；高：m）
-aspect  设置画面比例（4:3 or 16:9 or 1.3333 or others）
-vn   不输出视频
-c:v  设置视频编码
-vcodec  同上
-b   比特率
```

#### 音频选项

```text
-aframes <number> 音频帧？？
-aq <quality>   音频质量
-ar             采集率（Hz）
-ac <number> 声道
-an    不输出音频
-c:a   设置音频编码
-acodec   同上
-vol <volume> 音量（256=Normal）
-af    音频过滤器
```

#### 字幕选项

```text
-s size             set frame size (WxH or abbreviation)
-sn                 disable subtitle
-scodec codec       force subtitle codec ('copy' to copy stream)
-stag fourcc/tag    force subtitle tag/fourcc
-fix_sub_duration   fix subtitles duration
-canvas_size size   set canvas size (WxH or abbreviation)
-spre preset        set the subtitle options to the indicated preset
```

#### 部分选项解释

> `-f` 通过`ffmpeg -formats`查看支持的文件格式
>
> `-codec`等 `ffmpeg -codecs`查看支持的编码格式

### 举些栗子

#### 视音频的分离与封装

##### 分离

将 `in.mp4` 的视频和音频分别保存到 `out.mp4`和 `out.mp3`

```bash
ffmpeg -i in.mp4 -vn -c:a copy out.mp3
ffmpeg -i in.mp4 -an -c:v copy out.mp4
```

> 其中 `copy` 为复制流，即不对数据进行额外的处理

##### 封装

将 `in.mp4`和 `in.mp3` 的视频和音频封装到 `out.mkv`

```bash
ffmpeg -i in.mp3 -i in.mp4 -c copy out.mkv
```

#### 连接视频片段

要连接 `in_01.flv` 和 `in_02.flv`

```bash
ffmpeg -i in_01.flv -i in_02.flv -c copy out.mkv
```

如果要连接的文件比较多，还可以使用`-f concat`选项。假如要连接 `in_*.flv`

```bash
for file in in_*.flv; do echo "file '$file' " >> list; done
cat list  #可省略
ffmpeg -f concat -i list -c copy out.mkv
```

#### 压制

压制的参数就比较复杂了。先举个栗子吧
压制60帧率的`in.flv`，采用H.264的编码，输出30帧720P的mp4文件：

```bash
ffmpeg -f flv -i in.flv -preset fast -crf 23.5 -r 30 -s 1280x720 -c:v libx264 -c:a aac -ca 2 -b:v 2000K -threads 4 out.mp4
```

> `-preset fast`: 将处理速度设置为`fast`。该选项对视频质量影响不大，速度设置越快，压制出来的文件越大。
>> 可选项有 `ultrafast`,`superfast`,`veryfast`, `faster`, `fast`, `medium`, `slow`, `slower`, `veryslow`, `placebo`
>
> `-crf 23.5`: `-crf`选项影响视频的质量，数字越小即画质越好。根据视频对画质要求调整参数。参数的范围`0-51`。
>
> `-r 30`: 输出帧率30.
>
> `-s 1280x720`: 输出视频画面`1280*720`。
>
> `-c:v libx264 -c:a aac -ca 2`: 视频使用x264、音频使用aac进行编码，声道2。
>
> `-b:v 2000K`: 视频码率设置为2000K。
>
> `-threads`: 4线程。

#### 视频裁剪

##### 截取片段，制作动图

取`in.flv`从1:20开始的10s的画面制作gif动图。

```bash
ffmpeg -i in.flv -ss 1:20 -t 10 -r 15 -s 400x300 out.gif
```

##### 裁剪视频画面的某一部分

实现这个功能可以使用`crop`滤镜。
![01.png](https://i.yusa.me/BEiLwLRJN93N.png "来源自网络")

例如，要裁剪(0,0)开始的640*400的画面

```bash
ffmpeg -i in.mp4 -vf crop=640:400:0:0 out.mp4
```
