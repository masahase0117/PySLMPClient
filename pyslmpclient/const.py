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
    RemoteControl_NodeIndication = 0x3070
    Drive_ReadDiskState = 0x0205
    Drive_Defrag = 0x1207
    RemotePassword_Lock = 0x1631
    RemotePassword_Unlock = 0x1630
    File_ReadFileInfo = 0x0201
    File_ReadFileInfoWithTitle = 0x0202
    File_ReadFileNoInfo = 0x0204
    File_ChangeFileInfo = 0x1204
    File_Search = 0x0203
    File_Read = 0x0206
    File_Write = 0x1203
    File_FileLock = 0x0808
    File_Copy = 0x1206
    File_Delete = 0x1205
    File_ReadDir = 0x1810
    File_SearchDir = 0x1811
    File_NewFileA = 0x1202
    File_NewFileB = 0x1820
    File_DeleteFile = 0x1822
    File_CopyFile = 0x1824
    File_ChangeFileState = 0x1825
    File_ChangeFileDate = 0x1826
    File_OpenFile = 0x1827
    File_ReadFile = 0x1828
    File_WriteFile = 0x1829
    File_CloseFile = 0x182A
    SelfTest = 0x0619
    ClearError_Code = 0x1617
    ClearError_History = 0x1619
    OnDemand = 0x2101
    DataCollection_Auth = 0x4000
    DataCollection_KeepAlive = 0x4001
    DataCollection_GetData = 0x4002
    DataCollection_Distribute = 0x4003
    NodeConnection_NodeSearch = 0x0E30
    NodeConnection_IPAddressSet = 0x0E31
    ParameterSetting_DeviceInfoCompare = 0x0E32
    ParameterSetting_ParameterGet = 0x0E33
    ParameterSetting_ParameterUpdate = 0x0E34
    ParameterSetting_ParameterSetStart = 0x0E35
    ParameterSetting_ParameterSetEnd = 0x0E36
    ParameterSetting_ParameterSetCancel = 0x0E3A
    ParameterSetting_DeviceIdentificationInfoGet = 0x0E28
    ParameterSetting_CommunicationSpeed = 0x3072
    NodeMonitoring_StatusRead = 0xE44
    NodeMonitoring_StatusRead2 = 0xE53
    NodeMonitoring_ConnectionSettingGet = 0xE45
    NodeMonitoring_DataMonitoring = 0x0E29
    Other_CAN = 0x4020
    Other_IOLInk = 0x5000
    Other_ModbusTCP = 0x5001
    Other_ModbusRTU = 0x5002
    CCLinkIEFieldDiagnostics_SelectNodeInfoGet = 0x3119
    CCLinkIEFieldDiagnostics_CommunicationTest = 0x3040
    CCLinkIEFieldDiagnostics_CableTest = 0x3050
    CCLinkIETSNNetworkManagement_NetworkConfig = 0x0E90
    CCLinkIETSNNetworkManagement_MasterConfig = 0x0E91
    CCLinkIETSNNetworkManagement_SlaveConfig = 0x0E92
    CCLinkIETSNNetworkManagement_CyclicConfig = 0x0E93
    CCLinkIETSNNetworkManagement_Notification = 0x0E94
    LinkDeviceParameter_LinkDevicePrmWrite = 0x320A
    LinkDeviceParameter_LinkDevicePrmWriteCheckReq = 0x320B
    LinkDeviceParameter_LinkDevicePrmWriteCheckResp = 0x320C
    EventHistory_GetEventNum = 0x3060
    EventHistory_GetEventHistory = 0x3061
    EventHistory_ClearEventHistory = 0x161A
    EventHistory_ClockOffsetDataSend = 0x3062
    BackupRestore_GetCommunicationSet = 0x0EB0
    BackupRestore_GetStationSubIDList = 0x0EB1
    BackupRestore_GetDeviceInfo = 0x0EB2
    BackupRestore_StartBackup = 0x0EB3
    BackupRestore_EndBackup = 0x0EB4
    BackupRestore_RequestBackup = 0x0EB5
    BackupRestore_GetBackupPrm = 0x0EB6
    BackupRestore_CheckRestore = 0x0EB7
    BackupRestore_StartRestore = 0x0EB8
    BackupRestore_EndRestore = 0x0EB9
    BackupRestore_SetBackupPrm = 0x0EBA
    SlaveStationPrmRestore_CheckPrmDelivery = 0x0EBE
    StartStopCyclic_StopOwnStationCyclic = 0x3206
    StartStopCyclic_StartOwnStationCyclic = 0x3207
    StartStopCyclic_StopOtherStationCyclic = 0x3208
    StartStopCyclic_StartOtherStationCyclic = 0x3209
    ReservedStation_RsvStationConfigTemporaryRelease = 0x320D
    ReservedStation_RsvStationConfig = 0x320E
    WatchdogCounter_SetWatchdogCounterInfo = 0x3210
    WatchdogCounter_WatchdogCounterOffsetConfig = 0x3211


class DeviceCode(enum.Enum):
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
    LTS = 0x51
    LTC = 0x50
    LTN = 0x52
    SS = 0xC7
    SC = 0xC6
    SN = 0xC8
    LSTS = 0x59
    LSTC = 0x58
    LSTN = 0x5A
    CS = 0xC4
    CC = 0xC3
    CN = 0xC5
    SB = 0xA1
    SW = 0xB5
    DX = 0xA2
    DY = 0xA3
    Z = 0xCC
    LZ = 0x62
    R = 0xAF
    ZR = 0xB0
    RD = 0x2C
    LCS = 0x55
    LCC = 0x54
    LCN = 0x56


# アドレス表現が16進数のデバイスの一覧
D_ADDR_16 = (
    DeviceCode.X,
    DeviceCode.Y,
    DeviceCode.B,
    DeviceCode.W,
    DeviceCode.SB,
    DeviceCode.SW,
    DeviceCode.DX,
    DeviceCode.DY,
    DeviceCode.ZR,
    DeviceCode.W,
)
# 4バイトアドレスでしかアクセスできないデバイスの一覧
D_ADDR_4BYTE = (
    DeviceCode.LTS,
    DeviceCode.LTC,
    DeviceCode.LTN,
    DeviceCode.LSTS,
    DeviceCode.LSTC,
    DeviceCode.LSTN,
    DeviceCode.LCS,
    DeviceCode.LCC,
    DeviceCode.LCN,
    DeviceCode.LZ,
    DeviceCode.RD,
)
# 4バイトアドレスと2バイトアドレスで名前の違うデバイス
D_STRANGE_NAME = {DeviceCode.SS, DeviceCode.SC, DeviceCode.SN}


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


class PDU(enum.Enum):
    rdReqST = 1
    wrReqST = 2
    rdResST = 3
    wrResST = 4
    rdErrST = 5
    wrErrST = 6
    odReqST = 7
    rdReqMT = 8
    wrReqMT = 9
    rdResMT = 10
    wrResMT = 11
    rdErrMT = 12
    wrErrMT = 13
    odReqMT = 14
    reqEMT = 15
    resEMT = 16
    pushEMT = 17
    reqLMT = 18
    resLMT = 19
    errLMT = 20


ST_PDU = (
    PDU.rdReqST,
    PDU.wrReqST,
    PDU.rdResST,
    PDU.wrResST,
    PDU.rdErrST,
    PDU.wrErrST,
    PDU.odReqST,
)
MT_PDU = (
    PDU.rdReqMT,
    PDU.wrReqMT,
    PDU.rdResMT,
    PDU.wrResMT,
    PDU.rdErrMT,
    PDU.wrErrMT,
    PDU.odReqMT,
)
EMT_PDU = (PDU.reqEMT, PDU.resEMT, PDU.pushEMT)
LMT_PDU = (PDU.reqLMT, PDU.resLMT, PDU.errLMT)


class EndCode(enum.Enum):
    Success = 0x00
    WrongCommand = 0xC059
    WrongFormat = 0xC05C
    WrongLength = 0xC061
    Busy = 0xCEE0
    ExceedReqLength = 0xCEE1
    ExceedRespLength = 0xCEE2
    ServerNotFound = 0xCF10
    WrongConfigItem = 0xCF20
    PrmIDNotFound = 0xCF30
    NotStartExclusiveWrite = 0xCF31
    RelayFailure = 0xCF70
    TimeoutError = 0xCF71
    CANAppNotPermittedRead = 0xCCC7
    CANAppWriteOnly = 0xCCC8
    CANAppReadOnly = 0xCCC9
    CANAppUndefinedObjectAccess = 0xCCCA
    CANAppNotPermittedPDOMapping = 0xCCCB
    CANAppExceedPDOMapping = 0xCCCC
    CANAppNotExistSubIndex = 0xCCD3
    CANAppWrongParameter = 0xCCD4
    CANAppMoreOverParameterRange = 0xCCD5
    CANAppLessOverParameterRange = 0xCCD6
    CANAppTransOrStoreError = 0xCCDA
    CANAppOtherError = 0xCCFF
    OtherNetworkError = 0xCF00
    DataFragmentShortage = 0xCF40
    DataFragmentDup = 0xCF41
    DataFragmentLost = 0xCF43
    DataFragmentNotSupport = 0xCF44
