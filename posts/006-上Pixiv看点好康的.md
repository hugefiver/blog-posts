---
title: 上Pixiv看点好康的
date: 2019-12-26 15:49:13
categories: 
    - 技术
tags: 
    - pixiv
---

终于可以愉快的康P站了。
<!--more-->

> 2020/01/12 更新
> 
> 现在可以用于Discord了。

## 原理

众所周知，一个神秘力量使得在中国访问一些网站时会出现不正常的访问出错。所以我们在康Pixiv的时候往往要借助一些特殊手段。这篇文章介绍一个不太一样的方法。

组织我们访问Pixiv的方法一般有两种。第一种是DNS投毒，即在DNS请求的时候返回错误的IP地址。这种比较容易解决，传统的方法有改hosts文件和使用无污染的DNS。第二种就比较麻烦，下面我们来看一张图。

![][pic1]

我们使用HTTPS访问一个网站时，虽然内容是加密的，但是因为一些特殊的需求，在请求时需要带上访问的域名，而这部分信息在加密协议生效之前。因此防火墙可以识别出你访问的网站，然后中断你的连接。

但是有的网站即使提供的SNI和访问的也是可以访问的。例如Pixiv就不检查SNI，所以我们可以通过中间人攻击自己的方法修改SNI来访问Pixiv。

![][pic2]

`Project V` 是一个功能强大的网络工具平台，我们可以使用它完成我们要做的事情。

## 实现

### 下载工具

到 `V2Ray` 的[Github页面][v2ray]下载下载对应平台的文件并解压。

### 改Hosts

因为我们需要中间人攻击自己，所以需要通过修改hosts文件让浏览器或软件访问时被定向到我们自己的服务器。

在hosts文件添加以下代码：

* Pixiv 网址

  ``` plaintext
  127.0.0.1	www.pixiv.net
  127.0.0.1	pixiv.net
  127.0.0.1	source.pixiv.net
  127.0.0.1	imp.pixiv.net
  127.0.0.1	sketch.pixiv.net
  127.0.0.1	accounts.pixiv.net
  127.0.0.1	i.pximg.net
  127.0.0.1	s.pximg.net
  127.0.0.1	pixiv.pximg.net
  ```

* Discord 网址

  ``` plaintext
  127.0.0.1	discordapp.com 
  127.0.0.1	dl.discordapp.net
  127.0.0.1	status.discordapp.com 
  127.0.0.1	gateway.discordapp.gg
  127.0.0.1	cdn.discordapp.com 
  127.0.0.1	media.discordapp.net 
  127.0.0.1	discordcdn.com
  127.0.0.1	best.discord.media
  ```

### 生成证书并安装

在V2Ray的目录输入以下命令：

``` shell
./v2ctl cert --ca --domain="csust.xyz" --expire=87600h --file=ca
```



我们可以在目录看到名为 `ca_cert.pem` 和 `ca_key.pem` 的两个文件，前者是证书后者是密钥。然后将证书的后缀名改为 `crt` 双击安装即可。

### 写配置

我们打开 `config.json` 可以看到形如下面的JSON文本。

```json
{
  "log": {},
  "inbounds": [],
  "outbounds": [],
  "routing": {},
  "dns": {}
}
```



1. 我们首先在 `inbounds` 中添加一个任意门的配置:

   ```json
   {
       "listen": "127.0.0.1",
       "port": 443,
       "tag": "tls-in",
       "protocol": "dokodemo-door",
       "settings": {
           "network": "tcp",
           "port": 443,
           "followRedirect": true
       },
       "streamSettings": {
           "security": "tls",
           "tlsSettings": {
               "alpn": [
                   "h2",
                   "http/1.1"
               ],
               "certificates": [
                   {
                       "usage": "issue",
                       "certificate": [], // 此处填生成的证书的内容
                       "key": [] // 此处填生成的密钥的内容
                   }
               ]
           }
       }
   }
   ```

2. 然后我们在 `outbounds` 中添加出口配置: 

   ```json
   {
       "protocol": "freedom",
       "tag": "out",
       "settings": {
           "domainStrategy": "UseIP" // 使用后面的DNS配置解析IP
       },
       "streamSettings": {
           "security": "tls",
           "tlsSettings": {
               // 这一行不需要。
               //  "serverName": "csust.xyz", // 将SNI信息
               "allowInsecure": true,
               "alpn": [
                   "h2",
                   "http/1.1"
               ]
           }
       }
   }
   ```

3. 在 `routing` 的 `rules` 中添加路由: 

   ```json
   {
       "inboundTag": [
           "tls-in"
       ],
       "outboundTag": "out",
       "type": "field"
   }
   ```

   这样我们通过任意门访问的连接即可在修改SNI后转发到P站服务器。

4. 修改 `dns` 使流量正确转发: 

   ```json
   {
       "hosts": {
           "geosite:discord": "162.159.135.233",
           "geosite:pixiv": "210.140.131.222" // 方法一：在此处填入正确的IP
       },
       "servers": [
           "1.1.1.1" // 方法二：在此处填入纯净的DNS服务器
       ]
   }
   ```
   
5. 双击打开 `v2ray`，之后我们在浏览器打开 `https://www.pixiv.net/` 即可访问P站。

## 写在后面

本文的方法来源为 `Project V` 作者的一篇 [文章][ref1] 。

感谢 `Project V` 作者的文章。也感谢长期以来为该项目共献代码的人们。

其实老早之前就看过了这篇文章了，当时我准备作为 [GoPSP][psp] 项目的实现方法尝试了一下。不过后来后来这个项目鸽了。（

最近想要尝试不挂梯子用 `discord` 时想到了这个方法。不过很遗憾的是 `cloudflare` 会校验SNI，所以以失败告终。最后只能写这篇文章了。

> 2020/01/12 更新
> 
> 后来发现，虽然CF会检查SNI，但是似乎不填SNI信息就行了。



[pic1]: ../res/006/1.jpg
[pic2]: ../res/006/2.jpg
[v2ray]: https://github.com/v2ray/v2ray-core/releases	"V2Ray Releases"
[ref1]: https://docs.google.com/document/d/1lanYeQbELX7pytehvXO8SndZ0iGyivc2XopkMV5HWW0 "谢谢小薇姐姐"
[psp]: https://github.com/hugefiver/GoPSP