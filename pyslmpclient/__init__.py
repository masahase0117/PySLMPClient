#!/usr/bin/python
# -*- coding: utf-8 -*-
from array import array
import logging
import socket
import struct
import threading
import time
from typing import Dict
from typing import Optional
from typing import Tuple  # noqa
from typing import List  # noqa

from pyslmpclient import const
from pyslmpclient import util

VERSION = "0.0.1"


class SLMPClient(object):
    def __init__(self, addr, port=5000, binary=True, ver=4, tcp=False):
        """SLMPによりPLCとやり取りする

        :param str addr: 接続するPLCのIPアドレス
        :param int port: 接続先のポート番号
        :param bool binary: 交信コードとしてバイナリを使用するかどうか
        :param int ver: 使用するフレームのバージョン 4 or 3
        :param bool tcp: TCPで通信するかどうか
        """
        assert 0 < port, port
        self.addr = (addr, port)
        assert ver in (3, 4), ver
        self.protocol = (binary, ver, tcp)
        self.__socket = None  # type: Optional[socket.socket]
        self.__seq = 0  # type: int
        self.__recv_queue = (
            dict()
        )  # type: Dict[int, (int, int, int, int, int, bytes)]
        self.__lock = threading.Lock()
        self.target = util.Target()
        self.__rest = b""
        self.logger = logging.getLogger(__name__).getChild(
            self.__class__.__name__
        )

        self.__recv_thread = threading.Thread(
            target=self.__worker, daemon=True
        )
        self.__ctx_cnt = 0
        self.__monitor_device_num = (0, 0)  # type: (int, int)

    def __worker(self):
        while self.__socket:
            try:
                self.__recv()
            except RuntimeError as e:
                self.logger.error(e)

    def open(self):
        with self.__lock:
            self.__ctx_cnt += 1
        if self.__socket:
            return
        with self.__lock:
            if self.__socket:
                return
            if self.protocol[2]:
                self.__socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM
                )
            else:
                self.__socket = socket.socket(
                    socket.AF_INET, socket.SOCK_DGRAM
                )
            self.__socket.connect(self.addr)
            self.__socket.settimeout(1)
            self.__recv_thread.start()

    def close(self):
        with self.__lock:
            self.__ctx_cnt -= 1
        if self.__socket and self.__ctx_cnt == 0:
            with self.__lock:
                try:
                    self.__socket.shutdown(socket.SHUT_RDWR)
                finally:
                    self.__socket.close()
                    self.__socket = None
                self.__recv_thread = threading.Thread(
                    target=self.__worker, daemon=True
                )

    def __cmd_format(self, timeout, cmd, sub_cmd, data):
        """コマンドにヘッダを加え送信する

        :param int timeout: 監視タイマ 250msec単位
        :param cmd: コマンド
        :type cmd: SLMPCommand
        :param int sub_cmd: サブコマンド
        :param bytes data: データ
        :return: 送信時に付加したシリアル番号、3Eフレーム選択時は常に0
        :rtype: int
        """
        with self.__lock:
            if self.__seq > 0xFF:
                self.__seq = 0
        if not isinstance(cmd, const.SLMPCommand):
            raise ValueError(cmd)
        if self.protocol[0]:  # バイナリ
            make_frame = util.make_binary_frame
        else:  # ASCII
            make_frame = util.make_ascii_frame
        with self.__lock:
            buf = make_frame(
                self.__seq,
                self.target,
                timeout,
                cmd,
                sub_cmd,
                data,
                self.protocol[1],
            )
            self.__socket.sendall(buf)
            if self.protocol[1] == 4:  # 4Eフレーム
                self.__seq += 1
                return self.__seq - 1
            elif self.protocol[1] == 3:  # 3Eフレーム
                return 0
            else:
                raise RuntimeError(self.protocol[1])

    def __recv(self):
        if not self.__socket:
            return
        with self.__lock:
            if not self.__socket:
                return
            try:
                self.__socket.settimeout(0)
                buf = self.__socket.recv(512)
                self.__socket.settimeout(1)
            except socket.timeout and BlockingIOError:
                return
            buf = self.__rest + buf
            self.__rest = b""
        if not buf:
            return False
        if len(buf) < 11:
            with self.__lock:
                self.__rest = buf
            return
        seq = 0
        if buf[0] == ord("D"):  # ASCII
            if len(buf) < 22:
                with self.__lock:
                    self.__rest = buf
                return
            if buf[1] == ord("0"):  # 3E
                buf = buf[4:]
            elif buf[1] == ord("4"):  # 4E
                seq = int(buf[4:8].decode("ascii"))
                buf = buf[12:]
            else:
                RuntimeError(buf)
            if len(buf) < 18:
                with self.__lock:
                    self.__rest = buf
                return
            network_num = int(buf[0:2].decode("ascii"), base=16)
            pc_num = int(buf[2:4].decode("ascii"), base=16)
            io_num = int(buf[4:8].decode("ascii"), base=16)
            m_drop_num = int(buf[8:10].decode("ascii"), base=16)
            length = int(buf[10:14].decode("ascii"), base=16)
            term_code = int(buf[14:18].decode("ascii"), base=16)
            if len(buf) < length + 14:
                with self.__lock:
                    self.__rest = buf
                return
            data = buf[18:]
            new_length = length - 4
            data = data[:new_length]
            with self.__lock:
                self.__rest = data[new_length:]
            data = data.decode("ascii")
            assert len(data) == length - 4, (len(data), length)
        elif buf[0] in (0xD0, 0xD4):  # Binary
            if buf[0] == 0xD0:  # 3E Binary
                assert buf[1] == 0x00, buf[:2]
                buf = buf[2:]
            elif buf[0] == 0xD4:  # 4E Binary
                assert buf[:2] == b"\xd4\x00", buf[:2]
                (seq,) = struct.unpack("<H", buf[2:4])
                assert buf[4:6] == b"\x00\x00", buf[:6]
                buf = buf[6:]
            if len(buf) < 9:
                with self.__lock:
                    self.__rest = buf
                return
            tmp = struct.unpack("<BBHBHH", buf[:9])
            network_num, pc_num, io_num, m_drop_num, length, term_code = tmp
            if len(buf) < length + 7:
                with self.__lock:
                    self.__rest = buf
                return
            data = buf[9:]
            new_length = length - 2
            data = data[:new_length]
            with self.__lock:
                self.__rest = data[new_length:]
            assert len(data) == length - 2, (len(data), length)
        else:
            raise RuntimeError(buf)
        with self.__lock:
            self.__recv_queue[seq] = (
                network_num,
                pc_num,
                io_num,
                m_drop_num,
                term_code,
                data,
            )
        return True

    def __enter__(self):
        """コンテキスト構文用

        :return: 自身
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキスト構文用

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self.close()
        return False

    def __del__(self):
        self.close()

    def __recv_loop(self, seq: int, timeout: int):
        timeout *= 0.25
        if timeout == 0:
            timeout = 100
        start = time.monotonic()
        while seq not in self.__recv_queue.keys():
            end = time.monotonic()
            if end - start > timeout:
                break
        if seq not in self.__recv_queue.keys():
            raise TimeoutError()
        data = self.__recv_queue[seq]
        with self.__lock:
            del self.__recv_queue[seq]
        end_code = util.EndCode(data[4])
        if end_code != util.EndCode.Success:
            raise util.SLMPCommunicationError(end_code)
        return data

    def __read_devices(self, device_code, start_num, count, timeout, sub_cmd):
        cmd = const.SLMPCommand.Device_Read
        if not isinstance(device_code, const.DeviceCode):
            raise ValueError(device_code)
        assert 0 < start_num < 0xFFF, start_num
        assert 0 < count < 3584, count
        if self.protocol[0]:
            cmd_text = struct.pack("<I", start_num)[:-1]
            cmd_text += struct.pack("<B", device_code.value)
            cmd_text += struct.pack("<H", count)
        else:
            cmd_text = b"%s" % device_code.name.encode("ascii")
            if len(cmd_text) == 1:
                cmd_text += b"*"
            if device_code in const.D_ADDR_16:
                cmd_text += b"%06X%04d" % (start_num, count)
            else:
                cmd_text += b"%06d%04d" % (start_num, count)
        seq = self.__cmd_format(timeout, cmd, sub_cmd, cmd_text)
        try:
            data = self.__recv_loop(seq, timeout)
        except TimeoutError as e:
            raise TimeoutError(device_code, start_num, count) from e
        return data

    def read_bit_devices(self, device_code, start_num, count, timeout=0):
        """デバイスコードで指定したビットデバイスを開始アドレスから指定の個数分だけ読み取る。

        :param device_code: デバイスコード
        :type device_code: const.DeviceCode
        :param int start_num: 開始アドレス
        :param int count: 個数
        :param int timeout: 監視時間, 250msec単位
        :return: デバイスの値
        :rtype: Tuple[bool]
        """
        data = self.__read_devices(
            device_code, start_num, count, timeout, 0x0001
        )

        if isinstance(data[5], str):
            ret = tuple(x == "1" for x in data[5])
        else:
            ret = tuple(x == 1 for x in util.decode_bcd(list(data[5])))
            if count % 2 == 1:
                ret = ret[:-1]
        assert len(ret) == count, len(ret)
        return ret

    def read_word_devices(self, device_code, start_num, count, timeout=0):
        """デバイスコードで指定したワードデバイスを開始アドレスから指定の個数分だけ読み取る。

        :param device_code: デバイスコード
        :type device_code: const.DeviceCode
        :param int start_num: 開始アドレス
        :param int count: 個数
        :param int timeout: 監視時間, 250msec単位
        :return: デバイスの値
        :rtype: Tuple[bytes]
        """
        data = self.__read_devices(
            device_code, start_num, count, timeout, 0x0000
        )
        if isinstance(data[5], str):
            ret = array(
                "H",
                [
                    int(data[5][x:][:4], base=16)
                    for x in range(0, len(data[5]), 4)
                ],
            )
        else:
            ret = array("H", data[5])
        return ret

    def __write_devices(self, dc2, start_num, data, timeout, sub_cmd):
        """デバイス書き込み

        :param dc2:
        :type dc2: const.DeviceCode
        :param int start_num:
        :param data:
        :type data: List[int]
        :param int timeout:
        :param int sub_cmd:
        :return:
        """
        cmd = const.SLMPCommand.Device_Write
        if not isinstance(dc2, const.DeviceCode):
            raise ValueError(dc2)
        assert 0 < start_num < 0xFFF, start_num
        if self.protocol[0]:  # Binary
            buf = struct.pack("<I", start_num)[:-1]
            buf += struct.pack("<BH", dc2.value, len(data))
            if sub_cmd & 0x01:  # ビット
                for i in range(0, len(data), 2):
                    tmp = data[i:][:2]
                    if len(tmp) == 2:
                        if tmp[0]:
                            if tmp[1]:
                                buf += b"\x11"
                            else:
                                buf += b"\x10"
                        else:
                            if tmp[1]:
                                buf += b"\x01"
                            else:
                                buf += b"\x00"
                    else:
                        if tmp[0]:
                            buf += b"\x10"
                        else:
                            buf += b"\x00"
            else:
                buf += array("H", data).tobytes()
        else:  # ASCII
            buf = b"%s" % dc2.name.encode("ascii")
            if len(buf) == 1:
                buf += b"*"
            if dc2 in const.D_ADDR_16:
                buf += b"%06X%04d" % (start_num, len(data))
            else:
                buf += b"%06d%04d" % (start_num, len(data))
            if sub_cmd & 0x01:  # ビット
                for v in data:
                    buf += b"1" if v else b"0"
            else:
                for v in data:
                    buf += b"%04X" % v
        self.__cmd_format(timeout, cmd, sub_cmd, buf)

    def write_bit_devices(self, dc2, start_num, data, timeout=0):
        """デバイスコードで指定したビットデバイスを開始アドレスから指定したデータで書き換える。

        :param dc2: デバイスコード
        :type dc2: const.DeviceCode
        :param int start_num: 開始アドレス
        :param data: 書き込むデータ
        :type data: List[int]
        :param timeout: タイムアウト、250msec単位
        :return:
        """
        self.__write_devices(dc2, start_num, data, timeout, 0x01)

    def write_word_devices(self, dc2, start_num, data, timeout=0):
        """デバイスコードで指定したワードデバイスを開始アドレスから指定したデータで書き換える。

        :param dc2: デバイスコード
        :type dc2: const.DeviceCode
        :param int start_num: 開始アドレス
        :param data: 書き込むデータ
        :type data: List[int]
        :param timeout: タイムアウト、250msec単位
        :return:
        """
        self.__write_devices(dc2, start_num, data, timeout, 0x00)

    def __format_device_list(self, word_list, dword_list):
        """デバイスリストを要求電文としてフォーマットする

        :param word_list: ワードアクセスするデバイスのリスト
        :type word_list: List[(const.DeviceCode, int)]
        :param dword_list: ダブルワードアクセスするデバイスのリスト
        :type dword_list: List[(const.DeviceCode, int)]
        :return: 要求電文の形式となったデバイスリスト
        :rtype: bytes
        """
        if self.protocol[0]:  # Binary
            buf = struct.pack("<BB", len(word_list), len(dword_list))
            for dc, addr in word_list:
                buf += struct.pack("<I", addr)[:-1]
                buf += struct.pack("<B", dc.value)
            for dc, addr in dword_list:
                buf += struct.pack("<I", addr)[:-1]
                buf += struct.pack("<B", dc.value)
        else:  # ASCII
            buf = b"%02X%02X" % (len(word_list), len(dword_list))
            for dc, addr in word_list:
                buf += dc.name.encode("ascii")
                if len(dc.name) == 1:
                    buf += b"*"
                if dc in const.D_ADDR_16:
                    buf += b"%06X" % addr
                else:
                    buf += b"%06d" % addr
            for dc, addr in dword_list:
                buf += dc.name.encode("ascii")
                if len(dc.name) == 1:
                    buf += b"*"
                if dc in const.D_ADDR_16:
                    buf += b"%06X" % addr
                else:
                    buf += b"%06d" % addr
        return buf

    def read_random_devices(self, word_list, dword_list, timeout=0):
        """指定した連続していないデバイスのデータを読む

        :param word_list: ワードアクセスするデバイスのリスト
        :type word_list: List[(const.DeviceCode, int)]
        :param dword_list: ダブルワードアクセスするデバイスのリスト
        :type dword_list: List[(const.DeviceCode, int)]
        :param int timeout: タイムアウト、250msec単位
        :return: デバイスに入っていたデータ(ワードアクセス分のリスト,
         ダブルワードアクセス分のリスト)
        :rtype: (List[int], List[bytes])
        """
        cmd = const.SLMPCommand.Device_ReadRandom
        sub_cmd = 0x0000
        buf = self.__format_device_list(word_list, dword_list)
        seq = self.__cmd_format(timeout, cmd, sub_cmd, buf)
        try:
            data = self.__recv_loop(seq, timeout)
        except TimeoutError as e:
            raise TimeoutError(word_list, dword_list) from e
        buf = data[5]
        if isinstance(buf, str):  # ASCII
            bytes_buf = util.str2bytes_buf(buf)
            bytes_buf.reverse()
            word_data = list()
            dword_data = list()
            for _ in range(len(word_list)):
                d1 = bytes_buf.pop()
                d2 = bytes_buf.pop()
                word_data.append(bytes([d2, d1]))
            for _ in range(len(dword_list)):
                d1 = bytes_buf.pop()
                d2 = bytes_buf.pop()
                d3 = bytes_buf.pop()
                d4 = bytes_buf.pop()
                dword_data.append(bytes([d4, d3, d2, d1]))
        else:
            split_pos = len(word_list) * 2
            dword_data, word_data = util.extracts_word_dword_data(
                buf, split_pos
            )
        return word_data, dword_data

    def write_random_bit_devices(self, device_list, timeout=0):
        """連続していないビットデバイスに書き込む

        :param device_list: 書き込むデバイスと値のリスト(デバイス種別、アドレス、値)
        :type device_list: List[(const.DeviceCode, int, bool)]
        :param int timeout: タイムアウト、250msec単位
        :return: None
        """
        cmd = const.SLMPCommand.Device_WriteRandom
        sub_cmd = 0x01
        if self.protocol[0]:  # Binary
            buf = struct.pack("<B", len(device_list))
            for v in device_list:
                buf += struct.pack("<I", v[1])[:-1]
                buf += struct.pack("<BB", v[0].value, v[2])
        else:  # ASCII
            buf = b"%02X" % len(device_list)
            for v in device_list:
                buf += util.device2ascii(v[0], v[1])
                if v[2]:
                    buf += b"01"
                else:
                    buf += b"00"
        self.__cmd_format(timeout, cmd, sub_cmd, buf)

    def write_random_word_devices(self, word_list, dword_list, timeout=0):
        """連続していないワードデバイスに書き込む

        :param word_list: ワード単位でアクセスするデバイス
        :type word_list: List[(const.DeviceCode, int, bytes)]
        :param dword_list: ダブルワード単位でアクセスするデバイス
        :type dword_list: List[(const.DeviceCode, int, bytes)]
        :param int timeout: タイムアウト、250msec単位
        :return: None
        """
        if self.protocol[0]:  # Binary
            buf = struct.pack("<BB", len(word_list), len(dword_list))
            for v in word_list:
                buf += struct.pack("<I", v[1])[:-1]
                buf += struct.pack("<B", v[0].value)
                byte_buf = v[2][:]
                while len(byte_buf) < 2:
                    byte_buf += b"\x00"
                buf += byte_buf[:2]
            for v in dword_list:
                buf += struct.pack("<I", v[1])[:-1]
                buf += struct.pack("<B", v[0].value)
                byte_buf = v[2][:]
                while len(byte_buf) < 4:
                    byte_buf += b"\x00"
                buf += byte_buf[:4]
        else:
            buf = b"%02X%02X" % (len(word_list), len(dword_list))
            for v in word_list:
                buf += util.device2ascii(v[0], v[1])
                tmp = v[2][:]
                while len(tmp) < 2:
                    tmp += b"\x00"
                buf += b"%02X%02X" % (tmp[1], tmp[0])
            for v in dword_list:
                buf += util.device2ascii(v[0], v[1])
                tmp = v[2][:]
                while len(tmp) < 4:
                    tmp += b"\x00"
                buf += b"%02X%02X%02X%02X" % (tmp[3], tmp[2], tmp[1], tmp[0])
        self.__cmd_format(
            timeout, const.SLMPCommand.Device_WriteRandom, 0x0, buf
        )

    def entry_monitor_device(self, word_list, dword_list, timeout=0):
        """モニタするデバイスの登録

        :param word_list: ワード単位でアクセスするデバイスのリスト
        :type word_list: List[(const.DeviceCode, int)]
        :param dword_list: ダブルワード単位でアクセスするデバイスのリスト
        :type dword_list: List[(const.DeviceCode, int)]
        :param int timeout: タイムアウト、250msec単位
        :return: None
        """
        cmd = const.SLMPCommand.Device_EntryMonitorDevice
        sub_cmd = 0x0000
        assert 1 < len(word_list) + len(dword_list) <= 192, (
            len(word_list),
            len(dword_list),
        )
        buf = self.__format_device_list(word_list, dword_list)
        self.__cmd_format(timeout, cmd, sub_cmd, buf)
        with self.__lock:
            self.__monitor_device_num = (len(word_list), len(dword_list))

    def execute_monitor(self, timeout=0):
        """モニタ登録したデバイスのデータを読み取る

        :param int timeout: タイムアウト、250msec単位
        :return: デバイスに入っていたデータ(ワードアクセス分のリスト,
         ダブルワードアクセス分のリスト)
        :rtype: (List[int], List[bytes])
        """
        cmd = const.SLMPCommand.Device_ExecuteMonitor
        sub_cmd = 0x00
        if (
            self.__monitor_device_num[0] == 0
            and self.__monitor_device_num[1] == 0
        ):
            raise RuntimeError("モニタデバイス未登録")
        seq = self.__cmd_format(timeout, cmd, sub_cmd, b"")
        try:
            data = self.__recv_loop(seq, timeout)
        except TimeoutError as e:
            raise TimeoutError() from e
        buf = data[5]
        if isinstance(buf, str):  # ASCII
            bytes_buf = util.str2bytes_buf(buf)
            bytes_buf.reverse()
            word_data = list()
            dword_data = list()
            for _ in range(self.__monitor_device_num[0]):
                d1 = bytes_buf.pop()
                d2 = bytes_buf.pop()
                word_data.append(bytes([d2, d1]))
            for _ in range(self.__monitor_device_num[1]):
                d1 = bytes_buf.pop()
                d2 = bytes_buf.pop()
                d3 = bytes_buf.pop()
                d4 = bytes_buf.pop()
                dword_data.append(bytes([d4, d3, d2, d1]))
        else:
            split_pos = self.__monitor_device_num[0] * 2
            dword_data, word_data = util.extracts_word_dword_data(
                buf, split_pos
            )
        return word_data, dword_data

    def read_block(self, word_list, bit_list, timeout=0):
        """ブロックで読み出す

        :param word_list: ワード単位でアクセスするデバイスブロックのリスト
        (デバイスコード, アドレス, 点数)
        :type word_list: List[(const.DeviceCode, int, int)]
        :param bit_list: ビット単位でアクセスするデバイスブロックのリスト
        (デバイスコード, アドレス, 点数)
        :type bit_list: List[(const.DeviceCode, int, int)]
        :param int timeout: タイムアウト、250msec単位
        :return: デバイスに入っていたデータ(ワードアクセス分のリスト,
         ビットアクセス分のリスト)
        :rtype: (List[List[int]], List[List[bool])
        """
        cmd = const.SLMPCommand.Device_ReadBlock
        sub_smd = 0x00
        if self.protocol[0]:  # Binary
            buf = struct.pack("<BB", len(word_list), len(bit_list))
            for dc, addr, num in word_list + bit_list:
                buf += struct.pack("<I", addr)[:-1]
                buf += struct.pack("<BH", dc.value, num)
        else:  # ASCII
            buf = b"%02X%02X" % (len(word_list), len(bit_list))
            for dc, addr, num in word_list + bit_list:
                buf += dc.name.encode("ascii")
                if len(dc.name) == 1:
                    buf += b"*"
                if dc in const.D_ADDR_16:
                    buf += b"%06X%04X" % (addr, num)
                else:
                    buf += b"%06d%04X" % (addr, num)
        seq = self.__cmd_format(timeout, cmd, sub_smd, buf)
        try:
            data = self.__recv_loop(seq, timeout)
        except TimeoutError as e:
            raise TimeoutError() from e
        buf = data[5]
        if isinstance(buf, str):  # ASCII
            bytes_buf = util.str2bytes_buf(buf)
            a_flag = True
        else:
            bytes_buf = bytearray(buf[:])
            a_flag = False
        bytes_buf.reverse()
        word_data = list()
        bit_data = list()
        for dc1, addr1, num1 in word_list:
            tmp_buf = list()
            for _ in range(num1):
                d1 = bytes_buf.pop()
                d2 = bytes_buf.pop()
                if a_flag:
                    d2, d1 = d1, d2
                tmp_buf.append(bytes([d1, d2]))
            word_data.append(tmp_buf)
        for dc1, addr1, num1 in bit_list:
            tmp_buf = list()
            for _ in range(num1):
                d1 = bytes_buf.pop()
                d2 = bytes_buf.pop()
                if a_flag:
                    d2, d1 = d1, d2
                tmp_buf.extend(util.unpack_bits([d1, d2]))
            bit_data.append(tmp_buf)
        return word_data, bit_data

    def write_block(self, word_list, bit_list, timeout=0):
        """ブロックでの書き込み

        :param word_list: ワードアクセスするデバイスと書き込むデータのリスト
        (デバイス種別, 先頭アドレス, デバイス点数, 書き込みデータ)
        :type word_list: List[(const.DeviceCode, int, int, List[int])]
        :param bit_list: ビットアクセスするデバイスと書き込むデータのリスト
        (デバイス種別, 先頭アドレス, デバイス点数, 書き込みデータ)
        :type bit_list: List[(const.DeviceCode, int, int, List[bool])]
        :param int timeout: タイムアウト、250msec単位
        :return: None
        """
        cmd = const.SLMPCommand.Device_WriteBlock
        sub_cmd = 0x00
        if len(word_list) + len(bit_list) > 120:
            raise RuntimeError("書き込みブロック数超過")
        if self.protocol[0]:  # Binary
            buf = struct.pack("<BB", len(word_list), len(bit_list))
            for dc, addr, num, w_data in word_list:
                buf += struct.pack("<I", addr)[:-1]
                buf += struct.pack("<BH", dc.value, num)
                assert len(w_data) == num, (len(w_data), num)
                for v in w_data:
                    buf += struct.pack("<H", v)
            for dc, addr, num, w_data in bit_list:
                buf += struct.pack("<I", addr)[:-1]
                buf += struct.pack("<BH", dc.value, num)
                assert len(w_data) == num * 16, (len(w_data), num)
                p_data = util.pack_bits(w_data)
                assert len(p_data) == num * 2, (len(p_data), num)
                for v in p_data:
                    buf += struct.pack("<B", v)
        else:
            buf = b"%02X%02X" % (len(word_list), len(bit_list))
            for dc, addr, num, w_data in word_list:
                buf += dc.name.encode("ascii")
                if len(dc.name) == 1:
                    buf += b"*"
                if dc in const.D_ADDR_16:
                    buf += b"%06X%04X" % (addr, num)
                else:
                    buf += b"%06d%04X" % (addr, num)
                assert len(w_data) == num, (len(w_data), num)
                for v in w_data:
                    buf += b"%04X" % v
            for dc, addr, num, w_data in bit_list:
                buf += dc.name.encode("ascii")
                if len(dc.name) == 1:
                    buf += b"*"
                if dc in const.D_ADDR_16:
                    buf += b"%06X%04X" % (addr, num)
                else:
                    buf += b"%06d%04X" % (addr, num)
                assert len(w_data) == num * 16, (len(w_data), num)
                p_data = util.pack_bits(w_data)
                tmp_buf = b""
                for v in p_data:
                    if not tmp_buf:
                        tmp_buf = b"%02X" % v
                    else:
                        buf += b"%02X" % v + tmp_buf
                        tmp_buf = b""
        self.__cmd_format(timeout, cmd, sub_cmd, buf)

    def read_type_name(self, timeout=0):
        """アクセス先のユニットの形名および形名コードを読み出す

        :param int timeout: タイムアウト、250msec単位
        :return: (形名, 形名コード)
        :rtype: (string, SLMPTypeCode)
        """
        seq = self.__cmd_format(
            timeout, const.SLMPCommand.RemoteControl_ReadTypeName, 0x00, b""
        )
        try:
            data = self.__recv_loop(seq, timeout)
        except TimeoutError as e:
            raise TimeoutError() from e
        buf = data[5]
        if isinstance(buf, str):
            return buf[:16].strip(), const.TypeCode(int(buf[16:], base=16))
        else:
            (code,) = struct.unpack("<H", buf[16:])
            return buf[:16].decode("ascii").strip(), const.TypeCode(code)

    def self_test(self, data=None, timeout=0):
        """通信が正常に行えているかテストする

        :param str data: 通信テストで送る文字列、16進表現[0-9][A-F]のみ
        :param int timeout: タイムアウト、250msec単位
        :return: 正常に通信できているかどうか
        :rtype: bool
        """
        if data is None:
            data = time.strftime("%Y%m%d%H%M%S")
        assert int(data, base=16), data
        assert len(data) < 960, data
        if self.protocol[0]:  # Binary
            body = struct.pack("<H", len(data))
        else:
            body = b"%04X" % len(data)
        body += data.encode("ascii")
        seq = self.__cmd_format(
            timeout, const.SLMPCommand.SelfTest, 0x00, body
        )
        try:
            ret = self.__recv_loop(seq, timeout)
        except TimeoutError as e:
            raise TimeoutError() from e
        buf = ret[5]
        if isinstance(buf, str):
            return int(buf[:4], base=16) == len(data) and buf[4:] == data
        else:
            (length,) = struct.unpack("<H", buf[:2])
            body = buf[2:]
            return length == len(data) and body == data.encode("ascii")

    def clear_error(self, timeout=0):
        """エラーをクリア

        :param int timeout: タイムアウト、250msec単位
        :return: None
        """
        self.__cmd_format(timeout, const.SLMPCommand.ClearError, 0x00, b"")

    def check_on_demand_data(self):
        """オンデマンド送信データを受け取っていないか確認する

        :return: 受信していた場合そのデータ、受信していない場合はNone
        :rtype: Optional[bytes]
        """
        if not self.__recv_queue:
            return
        for k in self.__recv_queue.keys():
            buf = self.__recv_queue[k][5]
            if isinstance(buf, str):  # ASCII
                if buf[:8] == "21010000":
                    end_code = util.EndCode(self.__recv_queue[k][4])
                    with self.__lock:
                        del self.__recv_queue[k]
                    if end_code != util.EndCode.Success:
                        raise util.SLMPCommunicationError(end_code)
                    return b"%s" % buf[8:]
            else:
                if buf[:4] == b"\x01\x21\x00\x00":
                    end_code = util.EndCode(self.__recv_queue[k][4])
                    with self.__lock:
                        del self.__recv_queue[k]
                    if end_code != util.EndCode.Success:
                        raise util.SLMPCommunicationError(end_code)
                    return buf[4:]

    def memory_read(self, addr, length, timeout=0):
        """自局のメモリを読み取る

        :param int addr: 先頭アドレス
        :param int length: ワード長
        :param int timeout: タイムアウト、250msec単位
        :return: 読みだしたデータ
        :rtype: List[bytes]
        """
        cmd = const.SLMPCommand.Memory_Read
        sub_cmd = 0x00
        assert 0 < length <= 480, length
        if self.protocol[0]:  # Binary
            buf = struct.pack("<IH", addr, length)
        else:
            buf = b"%08X%04X" % (addr, length)
        seq = self.__cmd_format(timeout, cmd, sub_cmd, buf)
        try:
            ret = self.__recv_loop(seq, timeout)
        except TimeoutError as e:
            raise TimeoutError() from e
        buf = ret[5]
        ret = list()
        if isinstance(buf, str):
            buf = list(buf)
            buf.reverse()
            while buf:
                d1 = buf.pop()
                d2 = buf.pop()
                d3 = buf.pop()
                d4 = buf.pop()
                ret.append(
                    bytes([int(d3 + d4, base=16), int(d1 + d2, base=16)])
                )
        else:
            buf = list(buf)
            buf.reverse()
            while buf:
                d1 = buf.pop()
                d2 = buf.pop()
                ret.append(bytes([d1, d2]))
        return ret

    def memory_write(self, addr, data, timeout=0):
        """自局のメモリに書き込む

        :param int addr: 先頭アドレス
        :param data: 書き込みデータ
        :type data: List[bytes]
        :param int timeout: タイムアウト、250msec単位
        :return: None
        :rtype: None
        """
        cmd = const.SLMPCommand.Memory_Write
        sub_cmd = 0x00
        assert 0 < len(data) <= 480, len(data)
        if self.protocol[0]:  # Binary
            buf = struct.pack("<IH", addr, len(data))
            for v in data:
                buf += v
        else:
            buf = b"%08X%04X" % (addr, len(data))
            for v in data:
                buf += b"%02X%02X" %(v[1], v[0])
        self.__cmd_format(timeout, cmd, sub_cmd, buf)

