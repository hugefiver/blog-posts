---
title: 申请LE的ECC泛域名ssl证书
date: 2018-07-24 16:07:41
categories: 
    - 技术
tags: 
    - TLS
    - Web
---

之前说要写这么一片文章来着，结果事情太多就一直没写。最近发现新博客系统的编写过程遇到了瓶颈，就过来水一篇博文吧。其实也就是两行代码的事。

<!-- more -->

### 日常的写在前面

众所周知，我们访问网站的时候主要用的就是`http`和`https`两种协议。而`https`的加密和完整的特性使得我们的站免受劫持或植入小广告。然而启用`https`需要ssl证书，一般来说申请ssl证书都很贵。当然也有免费的证书可以签，例如 `Let's Encrypt`就是一家签免费ssl证书的机构。我们可以通过`certbot`或者`acme.sh`签证书，这里我选择`certbot`。

### 普通的签证书过程

首先就得安装`certbot`。对于CertOS和Ubuntu等用户可以选择直接使用包管理。

```bash
# Ubuntu
apt install certbot

# CentOS
yum install epel-release
yum update
yum install certbot
```

当然也可以直接从github下载（此时可执行文件为`certbot-auto`）：

```bash
git clone --depth=1 https://github.com/certbot/certbot.git
```

安装完成之后就可以签证书了

```bash
certbot certonly --standalone -d yourdomain.com -d a.yourdomain.com
```

这个过程中需要开放80端口进行验证，所以请把网页服务器暂时停掉。

签完之后我发现我的Nginx的配置文件已经被修改了，省得我改配置文件了（虽然我后来还是改了一通）。

### 签ECC泛域名证书

Certbot目前并没有集成签EC证书和泛域名证书的功能。当然对于免费的服务我们也不能要求太高对吧。这一步需要自己生成秘钥，以及通过`Let's Encrypt`的api签证书。

首先生成使用ECC算法的秘钥

```bash
openssl ecparam -genkey -name secp384r1 > ec.key
```

然后先自己生成一个证书。因为要签泛域名证书，而openssl的交互操作过程不支持多域名，所以要写一个配置文件。下载[这个模板](https://gist.github.com/hugefiver/0d57aea5da9b0941bcc9fbbab98a83d0) ([备用](https://resource.rurilove.moe/text/openssl.cnf))，然后把最后的`DNS.* =`后面的域名换成自己的。保存后运行以下命令

```bash
openssl req -new -sha384 -key ec.key -out ec.csr -outform der -config openssl.cnf
```

然后使用certbot签ssl证书

```bash
./certbot-auto --server https://acme-v02.api.letsencrypt.org/directory --manual --preferred-challenges dns-01 certonly --csr ec.csr \
 -d yourdomain.com -d *.yourdomain.com -d yourdomain1.com -d *.yourdomain.com
```

这个过程中会要求通过添加TXT记录验证DNS。然后当前目录会生成两个文件，其中`*-cert.pem`是我们需要的证书，秘钥就是我们此前生成的`ec.key`文件。将这两个文件填进Nginx等的配置然后reload就行了。
