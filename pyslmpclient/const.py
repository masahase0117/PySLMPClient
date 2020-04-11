#!/usr/bin/python
# -*- coding: utf-8 -*-

import enum


class SLMPCommand(enum.Enum):
    Device_Read = 0x0401
    Device_Write = 0x1401
    Device_ReadRandom = 0x0403
    Device_WriteRandom = 0x1402
    Device_EntryMonitorDevice = 0x0801
    Device_ExecuteMonitor = 0x0802
    Device_ReadBlock = 0x0406
    Device_WriteBlock = 0x1406
    Label_ArrayLabelRead = 0x041A
    Label_ArrayLabelWrite = 0x141A
    Label_LabelReadRandom = 0x041C
    Label_LabelWriteRandom = 0x141B
    Memory_Read = 0x0613
    Memory_Write = 0x1613
    ExtendUnit_Read = 0x0601
    ExtendUnit_Write = 0x1601
    RemoteControl_RemoteRun = 0x1001
    RemoteControl_RemoteStop = 0x1002
    RemoteControl_RemotePause = 0x1003
    RemoteControl_RemoteLatchClear = 0x1005
    RemoteControl_RemoteReset = 0x1006
    RemoteControl_ReadTypeName = 0x0101
    RemotePassword_Lock = 0x1631
    RemotePassword_Unlock = 0x1630
    File_ReadDir = 0x1810
    File_SearchDir = 0x1811
    File_NewFile = 0x1820
    File_DeleteFile = 0x1822
    File_CopyFIle = 0x1824
    File_ChangeFileState = 0x1825
    File_ChangeFileDate = 0x1826
    File_OpenFile = 0x1827
    File_ReadFile = 0x1828
    File_WriteFile = 0x1829
    File_CloseFile = 0x182A
    SelfTest = 0x0619
    ClearError = 0x1617
    OnDemand = 0x2101


class DeviceCode2(enum.Enum):
    SM = 0x91
    SD = 0xA9
    X = 0x9C
    Y = 0x9D
    M = 0x90
    L = 0x92
    F = 0x93
    V = 0x94
    B = 0xA0
    D = 0xA8
    W = 0xB4
    TS = 0xC1
    TC = 0xC0
    TN = 0xC2
    SS = 0xC7
    SC = 0xC6
    SN = 0xC8
    CS = 0xC4
    CC = 0xC3
    CN = 0xC5
    SB = 0xA1
    SW = 0xB5
    DX = 0xA2
    DY = 0xA3
    Z = 0xCC
    R = 0xAF
    ZR = 0xB0


# アドレス表現が16進数のデバイスの一覧
D_ADDR_16 = (
    DeviceCode2.X,
    DeviceCode2.Y,
    DeviceCode2.B,
    DeviceCode2.W,
    DeviceCode2.SB,
    DeviceCode2.SW,
    DeviceCode2.DX,
    DeviceCode2.DY,
    DeviceCode2.ZR,
    DeviceCode2.W,
)


class TypeCode(enum.Enum):
    Q00JCPU = 0x250
    Q00CPU = 0x251
    Q01CPU = 0x252
    Q02CPU = 0x41
    Q06HCPU = 0x42
    Q12HCPU = 0x43
    Q25HCPU = 0x44
    Q12PRHCPU = 0x4B
    Q25PRHCPU = 0x4C
    Q00UJCPU = 0x260
    Q00UCPU = 0x261
    Q01UCPU = 0x262
    Q02UCPU = 0x263
    Q03UDCPU = 0x268
    Q03UDVCPU = 0x366
    Q04UDHCPU = 0x269
    Q04UDVCPU = 0x367
    Q06UDHCPU = 0x26A
    Q06UDVCPU = 0x368
    Q10UDHCPU = 0x266
    Q13UDHCPU = 0x26B
    Q13UDVCPU = 0x36A
    Q20UDHCPU = 0x267
    Q26UDHCPU = 0x26C
    Q26UDVCPU = 0x36C
    Q50UDEHCPU = 0x26D
    Q100UDEHCPU = 0x26E
    QS001CPU = 0x230
    L02SCPU = 0x543
    L02CPU = 0x541
    L06CPU = 0x544
    L26CPU = 0x545
    L26CPU_BT = 0x542
    L04HCPU = 0x48C0
    L08HCPU = 0x48C1
    L16HCPU = 0x48C2
    LJ72GF15_T2 = 0x0641
    R00CPU = 0x48A0
    R01CPU = 0x48A1
    R02CPU = 0x48A2
    R04CPU = 0x4800
    R04ENCPU = 0x4805
    R08CPU = 0x4801
    R08ENCPU = 0x4806
    R08PCPU = 0x4841
    R08PSFCPU = 0x4851
    R08SFCPU = 0x4891
    R16CPU = 0x4802
    R16ENCPU = 0x4807
    R16PCPU = 0x4842
    R16PSFCPU = 0x4852
    R16SFCPU = 0x4892
    R32CPU = 0x4803
    R32ENCPU = 0x4808
    R32PCPU = 0x4843
    R32PSFCPU = 0x4853
    R32SFCPU = 0x4893
    R120CPU = 0x4804
    R120ENCPU = 0x4809
    R120PCPU = 0x4844
    R120PSFCPU = 0x4854
    R120SFCPU = 0x4894
    R12CCPU_V = 0x4820
    MI5122_VW = 0x4E01
    RJ72GF15_T2 = 0x4860
    RJ72GF15_T2_D1 = 0x4861
    RJ72GF15_T2_D2 = 0x4862
    NZ2GF_ETB = 0x0642
