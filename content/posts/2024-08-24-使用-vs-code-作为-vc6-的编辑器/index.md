---
title: 使用 VS Code 作为 Visual C++ 6.0 (VC6) 的编辑器
description: 由于一些众所周知的原因，我们不得不使用过时的 VC++ 6.0 来学习 C 语言，那我们就只使用它的编译器吧！
date: 2024-08-24T11:16:25.678Z
tags:
    - Visual Studio
    - C++
categories:
    - 编程语言
draft: false
lightgallery: true
---

## 为什么呢

由于一些众所周知的原因，我们不得不使用~~经典~~（过时）的比我们年龄还大的已有 25 年历史的 VC++ 6.0 来学习 C 语言。而对于现在来说，这个经典的 IDE 过于简陋，并且早已不兼容新的操作系统，用它学习早已成为一种折磨。但现代的 C 语言编译环境又无法兼容某些教材或考试的语言逻辑。那…我们就只使用它的编译器吧！

## 安置 VC98 编译器工具

> - 预制的工具链打包贴在了文章末尾，可以直接下载使用。
> - 工具链文件从 [Visual Studio 6.0 Enterprise (6.00.8168)](https://winworldpc.com/product/microsoft-visual-stu/60) 中提取，提取步骤放在文章末尾。

将编译器文件放置到一个**没有中文和空格的路径**，这里我的路径是 `E:/Library/VC98`。

{{< image src="assets/Snipaste_2024-08-24_19-33-08.png" caption="工具链目录" >}}

## 配置 VS Code 编辑器环境

1. 安装 C/C++ 插件。

    {{< image src="assets/Snipaste_2024-08-24_19-37-10.png" caption="C/C++ 插件" >}}

2. 安装 Code Runner 插件。

    {{< image src="assets/Snipaste_2024-08-24_19-38-35.png" caption="Code Runner 插件" >}}

3. 在~~自己的项目目录~~（想放哪就放哪qwq）建立一个新目录作为工作区存放需要用 VC6 编译的 C 语言文件，这里我放在了桌面 `D:\Desktop\VC6_C`。

    {{< image src="assets/Snipaste_2024-08-24_19-45-15.png" caption="项目目录" >}}

4. 在工作区中新建 `.vscode` 目录，并在其中新建 `settings.json`，内容为：

    ```json
    {
        "C_Cpp.default.includePath": [
            // VC98编译器所在路径/INCLUDE
            "E:/Library/VC98/INCLUDE"
        ],
        "code-runner.executorMap": {
            // VC98编译器所在路径/VC98.BAT
            "c": "cd $dir && E:/Library/VC98/VC98.BAT CL $fileName /nologo && $dir$fileNameWithoutExt",
            // VC98编译器所在路径/VC98.BAT
            "cpp": "cd $dir && E:/Library/VC98/VC98.BAT CL $fileName /nologo && $dir$fileNameWithoutExt"
        }
    }
    ```

5. 在工作区中新建一个测试 C 文件，右键 `Run Code` 运行。

    {{< image src="assets/Snipaste_2024-08-24_19-48-39.png" caption="右键运行" >}}

6. 运行结果在底部终端窗口显示。

    {{< image src="assets/Snipaste_2024-08-24_19-42-31.png" caption="运行结果" >}}

## 提取和制作 VC98 编译器工具（如果你感兴趣）

### 提取编译器文件

1. 下载 [Visual Studio 6.0 Enterprise (6.00.8168)](https://winworldpc.com/product/microsoft-visual-stu/60)，得到 `Visual Studio 6.0 Enterprise (6.00.8168).7z` 并解压出其中的 `VSE600ENU1.ISO` 文件。
2. 解压出 `VSE600ENU1.ISO` 中的 `VC98\BIN`，`VC98\INCLUDE`，`VC98\LIB` 目录和 `COMMON\MSDEV98\BIN\MSPDB60.DLL` 文件。
3. 将 `MSPDB60.DLL` 文件复制到解压出的 `VC98\BIN` 中。
4. 现在我们得到了以下目录

    ```txt
    VC98
    ├───BIN
    ├───INCLUDE
    └───LIB
    ```

### 编写编译脚本

这里直接使用 `BIN` 下的编译器是找不到头文件和库文件的，因为原始的 VC++ 6.0 软件在调用编译器时会设置 `INCLUDE` 和 `LIB` 环境变量，所以我们通过脚本包装编译命令。

- `VC98.BAT <编译工具> [参数]`

    ```bat
    @ECHO OFF
    
    SET INCLUDE=%~DP0INCLUDE
    SET LIB=%~DP0LIB
    
    FOR /F "TOKENS=1* DELIMS= " %%I IN ("%*") DO "%~DP0BIN\%%I" %%J
    ```

## 资源下载

- [预制工具链下载（密码：YUKI）](https://wwjz.lanzoul.com/iK02X28ajoyd)
