import _socket
from array import array
import io
import struct
import unittest
from unittest import mock


from pyslmpclient.const import DeviceCode
from pyslmpclient.const import TypeCode
from pyslmpclient import SLMPClient
from pyslmpclient.util import Target


class SLMPClientTestCase(unittest.TestCase):
    header_4e_q = (b"540000000000", b"\x54\x00\x00\x00\x00\x00")
    header_4e_r = (b"D40000000000", b"\xD4\x00\x00\x00\x00\x00")
    target_bytes = (b"0101000101", b"\x01\x01\x01\x00\x01")
    term_code = (b"0000", b"\x00\x00")
    target = Target(1, 1, 1, 1)
    header_3e_q = (b"5000", b"\x50\x00")
    header_3e_r = (b"D000", b"\xD0\x00")

    def setUp(self) -> None:
        self.patcher1 = mock.patch("socket.socket")
        self.socket_mock = self.patcher1.start()

    def tearDown(self) -> None:
        self.patcher1.stop()

    def prepare(self, i, f_type, data_body, socket_instance_mock):
        if f_type == "a":
            code = 0
        else:
            code = 1
        header_r = (
            self.header_3e_r[code] if i == 3 else self.header_4e_r[code]
        )
        if f_type == "a":
            length_bytes = b"%04X" % (
                len(self.term_code[code]) + len(data_body)
            )
        else:
            length_bytes = struct.pack(
                "<H", len(self.term_code[code]) + len(data_body)
            )
        socket_instance_mock.recv.side_effect = io.BytesIO(
            header_r
            + self.target_bytes[code]
            + length_bytes
            + self.term_code[code]
            + data_body
        ).read
        self.socket_mock.return_value = socket_instance_mock
        return SLMPClient(
            addr="192.168.0.1", port=5000, binary=(f_type == "b"), ver=i
        )

    def prepare_no_res(self, f_type, i, socket_instance_mock):
        socket_instance_mock.recv.side_effect = io.BytesIO(b"").read
        self.socket_mock.return_value = socket_instance_mock
        a = SLMPClient(
            addr="192.168.0.1", port=5000, binary=(f_type == "b"), ver=i
        )
        return a

    def check_send_data(self, f_type, i, data_body, socket_instance_mock):
        timer_bytes = b"0006" if f_type == "a" else b"\x06\x00"
        if f_type == "a":
            length_bytes = b"%04X" % (len(data_body) + len(timer_bytes))
        else:
            length_bytes = struct.pack(
                "<H", len(data_body) + len(timer_bytes)
            )
        code = 0 if f_type == "a" else 1
        header_q = (
            self.header_3e_q[code] if i == 3 else self.header_4e_q[code]
        )
        target_bytes = self.target_bytes[code]
        socket_instance_mock.sendall.assert_called_with(
            header_q + target_bytes + length_bytes + timer_bytes + data_body
        )


class SLMPClientDeviceTestCase(SLMPClientTestCase):
    def test_read_bit_devices(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        if f_type == "a":
                            data_body = b"00010011"
                        else:
                            data_body = b"\x00\x01\x00\x11"
                        a = self.prepare(
                            i, f_type, data_body, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            b = a.read_bit_devices(
                                DeviceCode.M,
                                start_num=100,
                                count=8,
                                timeout=6,
                            )
                        self.assertTupleEqual(
                            b,
                            (
                                False,
                                False,
                                False,
                                True,
                                False,
                                False,
                                True,
                                True,
                            ),
                        )
                        if f_type == "a":
                            data_body = b"04010001M*0001000008"
                        else:
                            data_body = (
                                b"\x01\x04\x01\x00\x64\x00\x00\x90\x08\x00"
                            )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )

    def test_read_word_devices(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        if f_type == "a":
                            data_body = b"12340002"
                        else:
                            data_body = b"\x34\x12\x02\x00"
                        a = self.prepare(
                            i, f_type, data_body, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            b = a.read_word_devices(
                                DeviceCode.M,
                                start_num=100,
                                count=2,
                                timeout=6,
                            )
                            self.assertSequenceEqual(
                                b, [0x1234, 0x0002], list
                            )
                        if f_type == "a":
                            data_body = b"04010000M*0001000002"
                        else:
                            data_body = (
                                b"\x01\x04\x00\x00\x64\x00\x00\x90\x02\x00"
                            )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )

    def test_read_word_devices_2(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        if f_type == "a":
                            data_body = b"123400021DEF"
                        else:
                            data_body = b"\x34\x12\x02\x00\xEF\x1D"
                        a = self.prepare(
                            i, f_type, data_body, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            b = a.read_word_devices(
                                DeviceCode.TN,
                                start_num=100,
                                count=3,
                                timeout=6,
                            )
                            self.assertSequenceEqual(
                                b, array("H", [0x1234, 0x0002, 0x1DEF]), array
                            )
                        if f_type == "a":
                            data_body = b"04010000TN0001000003"
                        else:
                            data_body = (
                                b"\x01\x04\x00\x00\x64\x00\x00\xC2\x03\x00"
                            )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )

    def test_write_bit_devices(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        a = self.prepare_no_res(
                            f_type, i, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            a.write_bit_devices(
                                DeviceCode.M,
                                100,
                                [1, 1, 0, 0, 1, 1, 0, 0],
                                6,
                            )
                        if f_type == "a":
                            data_body = b"14010001M*000100000811001100"
                        else:
                            data_body = (
                                b"\x01\x14\x01\x00\x64\x00\x00\x90"
                                b"\x08\x00\x11\x00\x11\x00"
                            )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )

    def test_write_word_devices(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        a = self.prepare_no_res(
                            f_type, i, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            a.write_word_devices(
                                DeviceCode.M,
                                start_num=100,
                                data=[0x2347, 0xAB96],
                                timeout=6,
                            )
                        if f_type == "a":
                            data_body = b"14010000M*00010000022347AB96"
                        else:
                            data_body = (
                                b"\x01\x14\x00\x00\x64\x00\x00\x90"
                                b"\x02\x00\x47\x23\x96\xAB"
                            )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )

    def test_write_word_devices_2(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        a = self.prepare_no_res(
                            f_type, i, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            a.write_word_devices(
                                DeviceCode.D,
                                start_num=100,
                                data=[0x1995, 0x1202, 0x1130],
                                timeout=6,
                            )
                        if f_type == "a":
                            data_body = b"14010000D*0001000003199512021130"
                        else:
                            data_body = (
                                b"\x01\x14\x00\x00\x64\x00\x00\xA8\x03"
                                b"\x00\x95\x19\x02\x12\x30\x11"
                            )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )

    def test_read_random(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        if f_type == "a":
                            data_body = (
                                b"19951202203048494C544F4EC3DEB9AFBADDBCB7"
                            )
                        else:
                            data_body = (
                                b"\x95\x19\x02\x12\x30\x20\x49\x48"
                                b"\x4e\x4f\x54\x4c\xaf\xB9\xde\xc3"
                                b"\xb7\xbc\xdd\xba"
                            )
                        a = self.prepare(
                            i, f_type, data_body, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            b = a.read_random_devices(
                                [
                                    (DeviceCode.D, 0),
                                    (DeviceCode.TN, 0),
                                    (DeviceCode.M, 100),
                                    (DeviceCode.X, 0x20),
                                ],
                                [
                                    (DeviceCode.D, 1500),
                                    (DeviceCode.Y, 0x160),
                                    (DeviceCode.M, 1111),
                                ],
                                timeout=6,
                            )
                        self.assertTupleEqual(
                            b,
                            (
                                [
                                    b"\x95\x19",
                                    b"\x02\x12",
                                    b"\x30\x20",
                                    b"\x49\x48",
                                ],
                                [
                                    b"\x4E\x4F\x54\x4C",
                                    b"\xAF\xB9\xDE\xC3",
                                    b"\xB7\xBC\xDD\xBA",
                                ],
                            ),
                        )
                        if f_type == "a":
                            data_body = (
                                b"040300000403D*000000TN000000M*000100"
                                b"X*000020D*001500Y*000160M*001111"
                            )
                        else:
                            data_body = (
                                b"\x03\x04\x00\x00\x04\x03\x00\x00\x00\xa8"
                                b"\x00\x00\x00\xc2\x64\x00\x00\x90\x20\x00"
                                b"\x00\x9c\xdc\x05\x00\xa8\x60\x01\x00\x9d"
                                b"\x57\x04\x00\x90"
                            )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )

    def test_write_random_bit(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        a = self.prepare_no_res(
                            f_type, i, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            a.write_random_bit_devices(
                                [
                                    (DeviceCode.M, 50, False),
                                    (DeviceCode.Y, 0x2F, True),
                                ],
                                timeout=6,
                            )
                        if f_type == "a":
                            data_body = b"1402000102M*00005000Y*00002F01"
                        else:
                            data_body = (
                                b"\x02\x14\x01\x00\x02\x32\x00\x00"
                                b"\x90\x00\x2F\x00\x00\x9D\x01"
                            )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )

    def test_write_random_word(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        a = self.prepare_no_res(
                            f_type, i, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            a.write_random_word_devices(
                                [
                                    (DeviceCode.D, 0, b"\x50\x05"),
                                    (DeviceCode.D, 1, b"\x75\x05"),
                                    (DeviceCode.M, 100, b"\x40\x05"),
                                    (DeviceCode.X, 0x20, b"\x83\x05"),
                                ],
                                [
                                    (
                                        DeviceCode.D,
                                        1500,
                                        b"\x02\x12\x39\x04",
                                    ),
                                    (
                                        DeviceCode.Y,
                                        0x160,
                                        b"\x07\x26\x75\x23",
                                    ),
                                    (
                                        DeviceCode.M,
                                        1111,
                                        b"\x75\x04\x25\x04",
                                    ),
                                ],
                                timeout=6,
                            )
                        if f_type == "a":
                            data_body = (
                                b"140200000403D*0000000550"
                                b"D*0000010575M*0001000540"
                                b"X*0000200583"
                                b"D*00150004391202"
                                b"Y*00016023752607"
                                b"M*00111104250475"
                            )
                        else:
                            data_body = (
                                b"\x02\x14\x00\x00\x04\x03"
                                b"\x00\x00\x00\xA8\x50\x05"
                                b"\x01\x00\x00\xA8\x75\x05"
                                b"\x64\x00\x00\x90\x40\x05"
                                b"\x20\x00\x00\x9C\x83\x05"
                                b"\xDC\x05\x00\xA8\x02\x12\x39\x04"
                                b"\x60\x01\x00\x9D\x07\x26\x75\x23"
                                b"\x57\x04\x00\x90\x75\x04\x25\x04"
                            )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )

    def test_monitor_device(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        if i == 4:
                            self.header_4e_r = (
                                b"D40000010000",
                                b"\xD4\x00\x01\x00\x00\x00",
                            )
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        if f_type == "a":
                            data_body = (
                                b"19951202203048494C544F4EC3DEB9AFBADDBCB7"
                            )
                        else:
                            data_body = (
                                b"\x95\x19\x02\x12\x30\x20\x49\x48"
                                b"\x4e\x4f\x54\x4c\xaf\xb9\xde\xc3"
                                b"\xb7\xbc\xdd\xba"
                            )
                        a = self.prepare(
                            i, f_type, data_body, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            a.entry_monitor_device(
                                [
                                    (DeviceCode.D, 0),
                                    (DeviceCode.TN, 0),
                                    (DeviceCode.M, 100),
                                    (DeviceCode.X, 0x20),
                                ],
                                [
                                    (DeviceCode.D, 1500),
                                    (DeviceCode.Y, 0x160),
                                    (DeviceCode.M, 1111),
                                ],
                                timeout=6,
                            )
                            if f_type == "a":
                                data_body = (
                                    b"080100000403D*000000TN000000M*000100"
                                    b"X*000020D*001500Y*000160M*001111"
                                )
                            else:
                                data_body = (
                                    b"\x01\x08\x00\x00\x04\x03"
                                    b"\x00\x00\x00\xa8\x00\x00\x00\xc2"
                                    b"\x64\x00\x00\x90\x20\x00\x00\x9c"
                                    b"\xdc\x05\x00\xa8\x60\x01\x00\x9d"
                                    b"\x57\x04\x00\x90"
                                )
                            self.check_send_data(
                                f_type, i, data_body, socket_instance_mock
                            )
                            ret = a.execute_monitor(6)
                        self.assertTupleEqual(
                            ret,
                            (
                                [
                                    b"\x95\x19",
                                    b"\x02\x12",
                                    b"\x30\x20",
                                    b"\x49\x48",
                                ],
                                [
                                    b"\x4e\x4f\x54\x4c",
                                    b"\xaf\xb9\xde\xc3",
                                    b"\xb7\xbc\xdd\xba",
                                ],
                            ),
                        )

    def test_read_block(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        if f_type == "a":
                            data_body = (
                                b"0008203015452800"
                                b"09700000000000000000000000000131"
                                b"20304849C3DE28000970B9AFB9AF"
                            )
                        else:
                            data_body = (
                                b"\x08\x00\x30\x20\x45\x15\x00\x28"
                                b"\x70\x09\x00\x00\x00\x00"
                                b"\x00\x00\x00\x00\x00"
                                b"\x00\x00\x00\x31\x01"
                                b"\x30\x20\x49\x48\xde\xc3\x00\x28"
                                b"\x70\x09\xaf\xb9\xaf\xb9"
                            )
                        a = self.prepare(
                            i, f_type, data_body, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            b = a.read_block(
                                [
                                    (DeviceCode.D, 0, 4),
                                    (DeviceCode.W, 0x100, 8),
                                ],
                                [
                                    (DeviceCode.M, 0, 2),
                                    (DeviceCode.M, 128, 2),
                                    (DeviceCode.B, 0x100, 3),
                                ],
                                timeout=6,
                            )
                        self.assertEqual(len(b), 2)
                        self.assertIsInstance(b, tuple)
                        self.assertIsInstance(b[0], list)
                        self.assertIsInstance(b[1], list)
                        self.assertEqual(len(b[0]), 2)
                        self.assertEqual(len(b[1]), 3)
                        self.assertListEqual(
                            b[0][0],
                            [
                                b"\x08\x00",
                                b"\x30\x20",
                                b"\x45\x15",
                                b"\x00\x28",
                            ],
                        )
                        self.assertListEqual(
                            b[0][1],
                            [
                                b"\x70\x09",
                                b"\x00\x00",
                                b"\x00\x00",
                                b"\x00\x00",
                                b"\x00\x00",
                                b"\x00\x00",
                                b"\x00\x00",
                                b"\x31\x01",
                            ],
                        )
                        self.assertListEqual(
                            b[1][0],
                            [
                                0,
                                0,
                                0,
                                0,
                                1,
                                1,
                                0,
                                0,  # 0x30
                                0,
                                0,
                                0,
                                0,
                                0,
                                1,
                                0,
                                0,  # 0x20
                                1,
                                0,
                                0,
                                1,
                                0,
                                0,
                                1,
                                0,  # 0x49
                                0,
                                0,
                                0,
                                1,
                                0,
                                0,
                                1,
                                0,  # 0x48
                            ],
                        )
                        self.assertListEqual(
                            b[1][1],
                            [
                                0,
                                1,
                                1,
                                1,
                                1,
                                0,
                                1,
                                1,  # 0xde
                                1,
                                1,
                                0,
                                0,
                                0,
                                0,
                                1,
                                1,  # 0xc3
                                0,
                                0,
                                0,
                                0,
                                0,
                                0,
                                0,
                                0,  # 0x00
                                0,
                                0,
                                0,
                                1,
                                0,
                                1,
                                0,
                                0,  # 0x28
                            ],
                        )
                        self.assertListEqual(
                            b[1][2],
                            [
                                0,
                                0,
                                0,
                                0,
                                1,
                                1,
                                1,
                                0,  # 0x70
                                1,
                                0,
                                0,
                                1,
                                0,
                                0,
                                0,
                                0,  # 0x09
                                1,
                                1,
                                1,
                                1,
                                0,
                                1,
                                0,
                                1,  # 0xaf
                                1,
                                0,
                                0,
                                1,
                                1,
                                1,
                                0,
                                1,  # 0xb9
                                1,
                                1,
                                1,
                                1,
                                0,
                                1,
                                0,
                                1,  # 0xaf
                                1,
                                0,
                                0,
                                1,
                                1,
                                1,
                                0,
                                1,  # 0xb9
                            ],
                        )
                        if f_type == "a":
                            data_body = (
                                b"040600000203D*0000000004W*0001000008"
                                b"M*0000000002M*0001280002"
                                b"B*0001000003"
                            )
                        else:
                            data_body = (
                                b"\x06\x04\x00\x00\x02\x03"
                                b"\x00\x00\x00\xa8\x04\x00"
                                b"\x00\x01\x00\xb4\x08\x00"
                                b"\x00\x00\x00\x90\x02\x00"
                                b"\x80\x00\x00\x90\x02\x00"
                                b"\x00\x01\x00\xa0\x03\x00"
                            )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )

    def test_write_block(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        a = self.prepare_no_res(
                            f_type, i, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            a.write_block(
                                [
                                    (
                                        DeviceCode.D,
                                        0,
                                        4,
                                        [0x8, 0x00, 0x00, 0x2800],
                                    ),
                                    (
                                        DeviceCode.W,
                                        0x100,
                                        8,
                                        [
                                            0x970,
                                            0x00,
                                            0x00,
                                            0x00,
                                            0x00,
                                            0x00,
                                            0x00,
                                            0x131,
                                        ],
                                    ),
                                ],
                                [
                                    (
                                        DeviceCode.M,
                                        0,
                                        2,
                                        [
                                            0,
                                            0,
                                            0,
                                            0,
                                            1,
                                            1,
                                            0,
                                            0,  # 0x30
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            1,
                                            0,
                                            0,  # 0x20
                                            1,
                                            0,
                                            0,
                                            1,
                                            0,
                                            0,
                                            1,
                                            0,  # 0x49
                                            0,
                                            0,
                                            0,
                                            1,
                                            0,
                                            0,
                                            1,
                                            0,  # 0x48
                                        ],
                                    ),
                                    (
                                        DeviceCode.M,
                                        128,
                                        2,
                                        [
                                            0,
                                            1,
                                            1,
                                            1,
                                            1,
                                            0,
                                            1,
                                            1,  # 0xde
                                            1,
                                            1,
                                            0,
                                            0,
                                            0,
                                            0,
                                            1,
                                            1,  # 0xc3
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,  # 0x00
                                            0,
                                            0,
                                            0,
                                            1,
                                            0,
                                            1,
                                            0,
                                            0,  # 0x28
                                        ],
                                    ),
                                    (
                                        DeviceCode.B,
                                        0x100,
                                        3,
                                        [
                                            0,
                                            0,
                                            0,
                                            0,
                                            1,
                                            1,
                                            1,
                                            0,  # 0x70
                                            1,
                                            0,
                                            0,
                                            1,
                                            0,
                                            0,
                                            0,
                                            0,  # 0x09
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,  # 0x00
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,  # 0x00
                                            1,
                                            1,
                                            1,
                                            1,
                                            0,
                                            1,
                                            0,
                                            1,  # 0xaf
                                            1,
                                            0,
                                            0,
                                            1,
                                            1,
                                            1,
                                            0,
                                            1,  # 0xb9
                                        ],
                                    ),
                                ],
                                timeout=6,
                            )
                        if f_type == "a":
                            data_body = (
                                b"140600000203D*00000000040008000000002800"
                                b"W*00010000080970000000000000000000000000"
                                b"0131"
                                b"M*000000000220304849"
                                b"M*0001280002C3DE2800"
                                b"B*000100000309700000B9AF"
                            )
                        else:
                            data_body = (
                                b"\x06\x14\x00\x00\x02\x03"
                                b"\x00\x00\x00\xa8\x04\x00"
                                b"\x08\x00\x00\x00\x00\x00\x00\x28"
                                b"\x00\x01\x00\xb4\x08\x00"
                                b"\x70\x09\x00\x00\x00\x00\x00\x00\x00\x00"
                                b"\x00\x00\x00\x00\x31\x01"
                                b"\x00\x00\x00\x90\x02\x00\x30\x20\x49\x48"
                                b"\x80\x00\x00\x90\x02\x00\xde\xc3\x00\x28"
                                b"\x00\x01\x00\xa0\x03\x00\x70\x09\x00\x00"
                                b"\xaf\xb9"
                            )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )


class SLMPClientRemoteControlTestCase(SLMPClientTestCase):
    def test_read_type_name(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        if f_type == "a":
                            data_body = b"Q02UCPU         0263"
                        else:
                            data_body = b"Q02UCPU         \x63\x02"
                        a = self.prepare(
                            i, f_type, data_body, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            ret = a.read_type_name(timeout=6)
                        self.assertEqual(ret[0], "Q02UCPU")
                        self.assertEqual(ret[1], TypeCode.Q02UCPU)
                        data_body = (
                            b"01010000"
                            if f_type == "a"
                            else b"\x01\x01\x00\x00"
                        )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )


class SLMPClientOtherTestCase(SLMPClientTestCase):
    def test_self_test(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        if f_type == "a":
                            data_body = b"0005ABCDE"
                        else:
                            data_body = b"\x05\x00ABCDE"
                        a = self.prepare(
                            i, f_type, data_body, socket_instance_mock
                        )
                        a.target = self.target
                        with a:
                            self.assertTrue(a.self_test("ABCDE", timeout=6))
                        data_body = (
                            b"061900000005ABCDE"
                            if f_type == "a"
                            else b"\x19\x06\x00\x00\x05\x00ABCDE"
                        )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )


class SLMPClientMemoryTestCase(SLMPClientTestCase):
    target_bytes = (b"00FF000101", b"\x00\xff\x01\x00\x01")

    def test_read(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        if f_type == "a":
                            data_body = b"050009C100C8"
                        else:
                            data_body = b"\x00\x05\xc1\x09\xc8\x00"
                        a = self.prepare(
                            i, f_type, data_body, socket_instance_mock
                        )
                        a.target.network = 1
                        a.target.node = 0x01
                        a.target.m_drop = 1
                        a.target.dst_proc = 1
                        with self.assertRaises(AssertionError):
                            ret = a.memory_read(0x78, 3, timeout=6)
                        a.target.network = 0
                        with self.assertRaises(AssertionError):
                            ret = a.memory_read(0x78, 3, timeout=6)
                        a.target.network = 1
                        a.target.node = 0xFF
                        with self.assertRaises(AssertionError):
                            ret = a.memory_read(0x78, 3, timeout=6)
                        a.target.network = 0
                        with a:
                            ret = a.memory_read(0x78, 3, timeout=6)
                        self.assertListEqual(
                            ret, [b"\x00\x05", b"\xc1\x09", b"\xc8\x00"]
                        )
                        data_body = (
                            b"06130000000000780003"
                            if f_type == "a"
                            else b"\x13\x06\x00\x00\x78\x00\x00\x00\x03\x00"
                        )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )

    def test_write(self):
        for f_type in ("a", "b"):
            with self.subTest(ftype=f_type):
                for i in (3, 4):
                    with self.subTest(i=i):
                        socket_instance_mock = mock.NonCallableMagicMock(
                            spec=_socket.socket
                        )
                        a = self.prepare_no_res(
                            f_type, i, socket_instance_mock
                        )
                        a.target.network = 1
                        a.target.node = 0x01
                        a.target.m_drop = 1
                        a.target.dst_proc = 1
                        with self.assertRaises(AssertionError):
                            a.memory_write(
                                0x2680, [b"\x00\x20", b"\x00\x00"], timeout=6
                            )
                        a.target.network = 0
                        with self.assertRaises(AssertionError):
                            a.memory_write(
                                0x2680, [b"\x00\x20", b"\x00\x00"], timeout=6
                            )
                        a.target.network = 1
                        a.target.node = 0xFF
                        with self.assertRaises(AssertionError):
                            a.memory_write(
                                0x2680, [b"\x00\x20", b"\x00\x00"], timeout=6
                            )
                        a.target.network = 0
                        with a:
                            a.memory_write(
                                0x2680, [b"\x00\x20", b"\x00\x00"], timeout=6
                            )
                        data_body = (
                            b"1613000000002680000220000000"
                            if f_type == "a"
                            else b"\x13\x16\x00\x00\x80\x26\x00\x00\x02\x00"
                            b"\x00\x20\x00\x00"
                        )
                        self.check_send_data(
                            f_type, i, data_body, socket_instance_mock
                        )


if __name__ == "__main__":
    unittest.main()
