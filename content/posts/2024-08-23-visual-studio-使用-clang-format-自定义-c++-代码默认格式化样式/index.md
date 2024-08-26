---
title: Visual Studio 使用 clang-format 自定义 C++ 代码默认格式化样式
description: 让 Visual Studio 默认使用我们自定义的 C/C++ 代码格式化样式，而不需要在项目中创建 .clang-format 文件。
date: 2024-08-23T10:28:12.728Z
draft: false
tags:
    - clang-format
    - Visual Studio
    - C++
categories:
    - 编程语言
lightgallery: true
---

## 问题描述

Visual Studio 的 C++ 代码格式化可选使用 clang-format，但它只提供默认样式，如果想使用自定义样式则需要在每个项目目录下放一个 `.clang-format` 或 `_clang-format` 文件，没有对全部项目通用的可自定义样式。

## 解决方法

这里发现 Visual Studio 的格式设置中有一个**使用自定义 clang-format.exe 文件**选项，所以这里尝试制做一个 clang-format 的包装程序让 VS 使用（~~来骗~~）。

包装程序通过其同级目录下的 `rules.txt` 文件来设置自定义的默认样式，具体设置参照 [**Clang-Format 官方文档**](https://clang.llvm.org/docs/ClangFormatStyleOptions.html)，也可以使用 [**Clang-Format 交互式构建器**](https://zed0.co.uk/clang-format-configurator/)。启用这个包装程序后， Visual Studio 内置的**默认格式设置样式**选项将会失效。

> - 预编译的包装程序和 `clang-format.exe` 一起打包贴在了文章末尾，可以直接下载使用。
> - 包装程序的代码贴在了文章末尾，如有需要在 Visual Studio 中使用 Std C++17 编译即可。
> - `clang-format.exe` 可以在 `%VS安装目录%\VC\Tools\Llvm\x64\bin` 目录中找到，也可以在 [LLVM 发布页](https://github.com/llvm/llvm-project/releases/latest) 下载。

这里贴上作者习惯使用的代码格式化样式（Java 代码的习惯样式），以下是 `rules.txt` 内容：

```yaml
# 基于GNU格式
BasedOnStyle: GNU
# 使用支持的最新标准
Standard: Latest
# 行不限制长度
ColumnLimit: 0
# 缩进4个空格
IndentWidth: 4
# 左花括号在名称之后
BreakBeforeBraces: Attach
# 函数参数的小括号与函数名间不空格, 控制语句的小括号与语句间空格
SpaceBeforeParens: ControlStatements
# 换行时将二元运算符置后
BreakBeforeBinaryOperators: None
# 允许空的花括号在一行上
AllowShortBlocksOnASingleLine: Empty
# 函数返回值与函数在同一行
AlwaysBreakAfterDefinitionReturnType: None
AlwaysBreakAfterReturnType: None
# 指针符号贴在类型边
PointerAlignment: Left
# 访问修饰符贴在左边
AccessModifierOffset: -4
# case和default之前缩进
IndentCaseLabels: true
# C式类型转换中间留空格
SpaceAfterCStyleCast: true
# 类继承冒号之前不留空格
SpaceBeforeInheritanceColon: false
# 构造函数初始化冒号之前不留空格
SpaceBeforeCtorInitializerColon: false
# 命名空间全部缩进
NamespaceIndentation: All
# 不排序头文件引用
SortIncludes: Never
# C++11式初始化对象花括号前留空格
SpaceBeforeCpp11BracedList: true
```

## 使用之前（二选一）

1. 确保 `clang-format.exe` 在 `PATH` 中并且可访问。

    {{< image src="assets/Snipaste_2024-08-21_21-06-49.png" caption="PATH 中可访问的 clang-format" >}}

2. 确保 `clang-format.exe` 位于 `clang-format-wrapper.exe` 的同级目录下。

    {{< image src="assets/Snipaste_2024-08-21_21-09-39.png" caption="同级目录下的 clang-format" >}}

## 使用方法

1. **启用 ClangFormat 支持**并**使用自定义 clang-format.exe 文件**，选择上一步的 `clang-format-wrapper.exe` 并确定。

    {{< image src="assets/Snipaste_2024-08-21_21-03-09.png" caption="配置选项" >}}

2. 现在可以回到编辑器测试一下了，默认格式化快捷键是 `Ctrl + K + D`。

## 包装程序的代码

```cpp
#include <filesystem>
#include <optional>
#include <string>

#include <process.h>

namespace fs = std::filesystem;

const wchar_t* clang_format_path = L"clang-format.exe";
const wchar_t* rule_text_path = L"rules.txt";

int wmain(int argc, wchar_t** argv) {
    std::optional<std::wstring> args;
    fs::path path = fs::absolute(argv[0]);
    path.replace_filename(clang_format_path);
    if (fs::exists(path)) {
        args = path.wstring();
    } else {
        args = std::wstring(clang_format_path, 16);
    }
    args->push_back(L' ');
    for (int i = 1; i < argc; i++) {
        if (!wcsstr(argv[i], L"-style=")) {
            args->append(argv[i]);
            args->push_back(L' ');
        }
    }
    args->append(L"-fallback-style=none -style=file:");
    args->append(path.replace_filename(rule_text_path));
    return _wsystem(args->data());
}
```

## 资源下载

> 由于 `clang-format.exe` 和 `clang-format-wrapper.exe` 依赖 VC++ 140 运行库，如果无法运行请先安装运行库。

- [运行库合集下载（密码：YUKI）](https://wwjz.lanzoul.com/i3wpJ27uk4la)
- [预编译程序下载（密码：YUKI）](https://wwjz.lanzoul.com/in53Z282jopg)
