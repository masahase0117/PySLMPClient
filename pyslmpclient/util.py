#!/usr/bin/python
# -*- coding: utf-8 -*-
import struct
from typing import List  # noqa

import numpy as np

from pyslmpclient.const import D_ADDR_16
from pyslmpclient.const import SLMPCommand


def encode_bcd(data):
    """Encode 4bit BCD array

    [1,2,3,4,...] --> [0x12,0x34,...]
      入力が奇数個の場合は最後の4bitを0埋め

    :param data: エンコード対象
    :type data: List[int]
    :return: 4bit毎にパックされた結果
    :rtype: List[int]
    """
    data = np.asarray(data, dtype=np.uint8)
    bin_array_h = (data[::2] & 0x0F) << 4
    bin_array_l = data[1::2] & 0x0F
    bin_array = np.zeros_like(bin_array_h)

    if data.size % 2 == 0:
        bin_array = bin_array_h | bin_array_l
    else:
        bin_array[:-1] = bin_array_h[:-1] | bin_array_l
        bin_array[-1] = bin_array_h[-1]
    bin_array = list(bin_array)
    return bin_array


def decode_bcd(data):
    """Decode 4bit BCD array

    [0x12,0x34,...] --> [1,2,3,4,...]

    :param data: 4bitにパックされたデータ列
    :type data: List[int]
    :return:
    :rtype: List[int]
    """
    data = np.asarray(data, dtype=np.uint8)
    bin_array_h = (data >> 4) & 0x0F
    bin_array_l = data & 0x0F

    bin_array = np.empty(data.size * 2, "u1")
    bin_array[::2] = bin_array_h
    bin_array[1::2] = bin_array_l

    bin_array = list(bin_array)
    return bin_array


def unpack_bits(data):
    """LSBから順に格納されているビット列を配列に展開する

    [<M107 ... M100>, <M115 ... M108>] -->
        [<M100>, ... ,<M107>, <M108>, ... ,<M115>]

    :param data: パック済みのデータ列
    :type data: List[int]
    :return: 1項目１デバイスとした配列
    :rtype: List[int]
    """
    data = np.asarray(data, dtype=np.uint8)

    # unpack_bits後のデータ順を反転させるために、疑似的に2次元配列として、
    # 1バイトごとにビットデータが格納されるようにする
    #   e.g. [1,2,3] --> [[1],[2],[3]]
    byte_array2d = data.reshape((data.size, 1))

    # ビットデータを展開
    #   e.g. [[1],[2],[3]] -->
    #        [[0,0,0,0,0,0,0,1],[0,0,0,0,0,0,1,0],[0,0,0,0,0,0,1,1]]
    byte_array2d_bin = np.unpackbits(byte_array2d, axis=1)

    # 列方向の順序を反転後、1次元配列に戻す
    return list(byte_array2d_bin[:, ::-1].flatten())


def pack_bits(data):
    """ビットデータの配列をLSBから順に格納されたバイト列にパックする

    [<M100>, ... ,<M107>, <M108>, ... ,<M115>]  -->
        [<M107 ... M100>, <M115 ... M108>]

    :param data: デバイスごとのビットデータの配列
    :type data: List[int]
    :return: パックした配列
    :rtype: List[int]
    """
    data = np.asarray(data, dtype=np.uint8)
    # データ数が8の倍数になるようにする
    size8 = -(-data.size // 8) * 8

    # 最後サイズが足りないところを0埋め
    byte_array_bin = np.zeros(size8, "u1")
    byte_array_bin[:data.size] = data

    # 8bitごとにデータ順を反転させるために2次元配列に変換
    byte_array2d_bin = byte_array_bin.reshape((size8 // 8, 8))

    # ビットデータをパック
    return list(np.packbits(byte_array2d_bin[:, ::-1]))


def device2ascii(device_type, address):
    """ASCII形式時のデバイス表記へ変換する

    :param device_type: デバイス種別
    :type device_type: DeviceCode2
    :param int address: アドレス
    :return: ASCII形式時のデバイス表記
    :rtype: bytes
    """
    buf = device_type.name.encode("ascii")
    if len(device_type.name) == 1:
        buf += b"*"
    if device_type in D_ADDR_16:
        buf += b"%06X" % address
    else:
        buf += b"%06d" % address
    return buf


class Target(object):
    def __init__(self, network_num=0, pc_num=0, io_num=0, m_drop_num=0):
        """SLMPで通信する対象

        :param int network_num: ネットワーク番号
        :param int pc_num: 要求先局番
        :param int io_num: 要求先ユニットIO番号
        :param int m_drop_num: 要求先マルチドロップ局番
        """
        assert 0 <= network_num <= 0xFF, network_num
        assert 0 <= pc_num <= 0xFF, pc_num
        assert 0 <= io_num <= 0xFFFF, io_num
        assert 0 <= m_drop_num <= 0xFF, m_drop_num
        self.__network = network_num
        self.__pc = pc_num
        self.__io = io_num
        self.__m_drop = m_drop_num

    @property
    def network(self):
        return self.__network

    @network.setter
    def network(self, value: int):
        if isinstance(value, int) and 0 <= value <= 0xFF:
            self.__network = value
        else:
            raise ValueError("0 <= value <= 0xFF")

    @property
    def pc(self):
        return self.__pc

    @pc.setter
    def pc(self, value: int):
        if isinstance(value, int) and 0 <= value <= 0xFF:
            self.__pc = value
        else:
            raise ValueError("0 <= value <= 0xFF")

    @property
    def io(self):
        return self.__io

    @io.setter
    def io(self, value: int):
        if isinstance(value, int) and 0 <= value <= 0xFFFF:
            self.__io = value
        else:
            raise ValueError("0 <= value <= 0xFFFF")

    @property
    def m_drop(self):
        return self.__m_drop

    @m_drop.setter
    def m_drop(self, value: int):
        if isinstance(value, int) and 0 <= value <= 0xFF:
            self.__m_drop = value
        else:
            raise ValueError("0 <= value <= 0xFF")


def make_binary_frame(seq, target, timeout, cmd, sub_cmd, data, ver):
    """バイナリモードの場合のコマンドフレームを作成する

    :param int seq: シリアル番号
    :param target: 接続先
    :type target: Target
    :param int timeout: 監視タイマ 250msec単位
    :param cmd: コマンド
    :type cmd: SLMPCommand
    :param int sub_cmd: サブコマンド
    :param bytes data: データ
    :param int ver: 生成するのは4Eなのか3E
    :return: コマンドフレーム
    :rtype: bytes
    """
    assert 0 <= seq <= 0xFF, seq
    assert 0 <= timeout <= 0xFFFF, timeout
    assert 0 <= sub_cmd <= 0xFFFF, sub_cmd

    if not isinstance(cmd, SLMPCommand):
        cmd = SLMPCommand(cmd)
    cmd_text = struct.pack(
        "<BBHBHHHH",
        target.network,
        target.pc,
        target.io,
        target.m_drop,
        len(data) + 6,
        timeout,
        cmd.value,
        sub_cmd,
    )
    if ver == 4:
        buf = struct.pack("<HHH", 0x54, seq, 0x00) + cmd_text
    elif ver == 3:
        buf = b"\x50\x00" + cmd_text
    else:
        raise RuntimeError(ver)
    buf += data
    assert len(buf) < 8194, len(buf)
    return buf


def make_ascii_frame(seq, target, timeout, cmd, sub_cmd, data, ver):
    """ASCIIモードの場合のコマンドフレームを作成する

    :param int seq: シリアル番号
    :param target: 接続先
    :type target: Target
    :param int timeout: 監視タイマ 250msec単位
    :param cmd: コマンド
    :type cmd: SLMPCommand
    :param int sub_cmd: サブコマンド
    :param bytes data: データ
    :param int ver: 生成するのは4Eなのか3E
    :return: コマンドフレーム
    :rtype: bytes
    """
    assert 0 <= seq <= 0xFF, seq
    assert 0 <= timeout <= 0xFFFF, timeout
    assert 0 <= sub_cmd <= 0xFFFF, sub_cmd

    if not isinstance(cmd, SLMPCommand):
        cmd = SLMPCommand(cmd)

    cmd_text = b"%02X%02X%04X%02X%04X%04X%04X%04X" % (
        target.network,
        target.pc,
        target.io,
        target.m_drop,
        len(data) + 12,
        timeout,
        cmd.value,  # noqa
        sub_cmd,
    )
    if ver == 4:
        buf = b"5400%04X0000" % seq + cmd_text + data
    elif ver == 3:
        buf = b"5000" + cmd_text + data
    else:
        raise RuntimeError(ver)
    assert len(buf) < 8194, len(buf)
    return buf


def str2bytes_buf(data):
    """2バイトの16進数が連続した文字列表現から数列へ

    :param str data: 16進表現の連なった文字列
    :return: バイト列
    :rtype: bytearray
    """
    buf = list(data)
    buf.reverse()
    bytes_buf = list()
    while buf:
        s1 = buf.pop()
        s2 = buf.pop()
        bytes_buf.append(int(s1 + s2, base=16))
    return bytearray(bytes_buf)


def extracts_word_dword_data(buf, split_pos):
    """2バイトデータ列と4バイトデータ列を切り分ける

    :param bytes buf: 切り分け元のバイナリデータ
    :param int split_pos: 2バイトデータの数
    :return: 2バイトデータ列と4バイトデータ列
    :rtype: List[bytes], List[bytes]
    """
    word_data = list()
    dword_data = list()
    word_buf = bytearray(buf[:split_pos])
    dword_buf = bytearray(buf[split_pos:])
    word_buf.reverse()
    dword_buf.reverse()
    while word_buf:
        d1 = word_buf.pop()
        d2 = word_buf.pop()
        word_data.append(bytes([d1, d2]))
    while dword_buf:
        d1 = dword_buf.pop()
        d2 = dword_buf.pop()
        d3 = dword_buf.pop()
        d4 = dword_buf.pop()
        dword_data.append(bytes([d1, d2, d3, d4]))
    return dword_data, word_data
