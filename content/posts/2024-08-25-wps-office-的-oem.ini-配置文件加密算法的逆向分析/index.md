---
title: WPS Office 的 OEM.INI 配置文件加密算法的逆向分析
description: 从某个版本开始，WPS Office 的 OEM.INI 中所有的配置项都被加密了，本文尝试通过逆向安装程序解析配置项的加密方式。
date: 2024-08-24T19:55:59.078Z
tags:
    - C++
    - ASM
categories:
    - 逆向破解
draft: false
lightgallery: true
---

## 本文简介

众所周知，WPS Office 的安装包是一种套娃结构，从官网下载的安装包经过解压缩会得到一个真正的安装程序和一个 OEM.INI 配置文件，通过修改这个配置文件，我们可以对 WPS 做一些定制并重新封包，但是从某个版本开始，OEM.INI 中所有的配置项都被加密了，所以本文尝试通过逆向安装程序的方式看看它是怎么加密的。

## 动态分析

首先解压出安装程序和配置文件，看了一下是 32 位程序，通过 x32dbg 进行调试。因为配置文件是 INI 格式的，所以我们首先想到，安装程序是否通过 Win32 API 提供的 INI 操作函数读取配置。而 `Kernel32.dll` 的 `GetPrivateProfileStringW` 和 `GetPrivateProfileStringA` 函数可以用来读取配置文件，那么加上断点，运行程序，发现断在了 `GetPrivateProfileStringW` 处。

通过查阅微软文档，我们得知它的第一个参数是节名，第二个参数是键名，最后一个参数是文件名。

```c
DWORD GetPrivateProfileStringW(
    [in]  LPCWSTR lpAppName,
    [in]  LPCWSTR lpKeyName,
    [in]  LPCWSTR lpDefault,
    [out] LPWSTR  lpReturnedString,
    [in]  DWORD   nSize,
    [in]  LPCWSTR lpFileName
);
```

查看栈信息，这正是我们解压出来的 OEM.INI 文件。

{{< image src="assets/Snipaste_2024-08-25_05-00-45.png" caption="断在了 GetPrivateProfileStringW 处" >}}

一路运行到返回，直到回到程序空间，给这个函数打上断点然后重新运行来到函数开头，发现栈里只有明文，看起来加密就是在这个函数里调用的。

{{< image src="assets/Snipaste_2024-08-25_05-01-23.png" caption="回到程序空间" >}}

从头单步调试并观察栈和寄存器信息，直到执行 `call a.551C30` 之后，发现 `eax` 中出现了密文，看来这个函数就是加密函数了，打上断点，进入查看。

{{< image src="assets/Snipaste_2024-08-25_05-02-59.png" caption="总体加密函数" >}}

单步执行并观察这个函数里的调用，发现执行 `call a.551F10` 之后，返回了一串像是密钥一样的东西，先记下来，继续执行。

{{< image src="assets/Snipaste_2024-08-25_05-23-43.png" caption="密钥获取函数" >}}

而这个密钥和明文一起被传入了下一个调用中，这看起来就是加密函数本体了。

{{< image src="assets/Snipaste_2024-08-25_05-24-23.png" caption="加密函数" >}}

继续单步，直到执行 `call a.692D60` 之后，`esi` 中出现了类似配置文件中的形似 Base64 的密文。

{{< image src="assets/Snipaste_2024-08-25_05-24-38.png" caption="编码函数" >}}

最后，执行过几个符号替换之后，密文变成了配置文件中的样子。

{{< image src="assets/Snipaste_2024-08-25_05-21-50.png" caption="符号替换" >}}

现在，该静态分析出手了，看看这个加密是用的什么算法吧。

## 静态分析

用 IDA32 打开安装程序，定位到动态调试发现的总体加密函数。

{{< image src="assets/Snipaste_2024-08-26_01-52-42.png" caption="总体加密函数" >}}

首先看一下获取密钥的函数 `sub_441F10`，注意这里的 `_Init_thread_header` 和结尾的 `_Init_thread_footer`，这种结构意味着这是一个函数内的静态变量。

{{< image src="assets/Snipaste_2024-08-26_01-58-59.png" caption="静态变量结构" >}}

看起来是把一些硬编码的数据进行一些简单转换，但我们已经通过动态调试得到了密钥，就不再分析了。

{{< image src="assets/Snipaste_2024-08-26_01-56-55.png" caption="一些简单转换" >}}

接下来是加密算法部分，我们注意到它先对字符串做了 16 字节对齐，然后对 `16 - (str_len & 0xF)` 也就是 16 字节对齐后空余的部分全部填充了 `aligned_str_len - str_len` 空余大小作为内容，这种行为与 PKCS5 和 PKCS7 吻合。

{{< image src="assets/Snipaste_2024-08-26_02-02-44.png" caption="加密部分" >}}

继续深入查看，这里有两个函数调用。

{{< image src="assets/Snipaste_2024-08-26_02-07-27.png" caption="加密部分函数调用" >}}

到了最深处，这就是加密算法了，这里最初判断算法类型的时候用了 GPT，丢给它算法的关键部分，便可判断出这是 AES 算法，而考虑到配置文件的明文和密文是一一对应的，就初步判断这是 ECB 算法了，因为也没看见 IV 相关的参数。

{{< image src="assets/Snipaste_2024-08-26_02-09-10.png" caption="加密算法" >}}

接下来是编码函数，进入编码函数后看见有码表，打开一看，便猜测这是标准 Base64 编码。

{{< image src="assets/Snipaste_2024-08-26_02-14-26.png" caption="Base64 码表" >}}

现在可以验证猜想了，我们使用 [CyberChef](https://cyberchef.org/) 网站，添加一个 AES 加密和 Base64 编码，与动态调试的明文和密文做比对，发现结果一致。

{{< image src="assets/Snipaste_2024-08-26_02-19-54.png" caption="尝试加密" >}}

现在就只剩最后一步了，这里看到程序替换掉了 Base64 中的三个符号。

{{< image src="assets/Snipaste_2024-08-26_02-21-10.png" caption="符号替换" >}}

这样我们就完整的知道 WPS 的安装程序是如何对配置文件加解密的了，现在只需要写一个转换程序，就可以实现对明文和密文 INI 的转换了。

## 后记

这是我的第一次逆向实战，成功了，很开心。没遇到任何加壳、反调试等措施，加密算法也比较简单，但即使是这样，能成功也有一定的运气因素，不了解的东西实在是太多了呢...
