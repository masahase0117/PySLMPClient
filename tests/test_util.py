import unittest

from pyslmpclient.const import SLMPCommand
from pyslmpclient.util import decode_bcd
from pyslmpclient.util import encode_bcd
from pyslmpclient.util import make_ascii_frame
from pyslmpclient.util import make_binary_frame
from pyslmpclient.util import pack_bits
from pyslmpclient.util import Target
from pyslmpclient.util import unpack_bits


class BCDTestCase(unittest.TestCase):
    def test_encode(self):
        a = [1, 2, 3, 4, 5, 6, 7, 8]
        b = encode_bcd(a)
        self.assertIsInstance(b, list)
        self.assertSequenceEqual(b, [0x12, 0x34, 0x56, 0x78], list)
        a = [1, 2, 3, 4, 5, 6, 7]
        b = encode_bcd(a)
        self.assertSequenceEqual(b, [0x12, 0x34, 0x56, 0x70], list)
        a = [1, 2, 3, 4, 5]
        b = encode_bcd(a)
        self.assertSequenceEqual(b, [0x12, 0x34, 0x50], list)

    def test_decode(self):
        a = [0x12, 0x34, 0x56, 0x78]
        b = decode_bcd(a)
        self.assertIsInstance(b, list)
        self.assertSequenceEqual(b, [1, 2, 3, 4, 5, 6, 7, 8], list)

    def test_encode_decode(self):
        a = [1, 2, 3, 4, 5, 6, 7, 8]
        b = encode_bcd(a)
        c = decode_bcd(b)
        self.assertSequenceEqual(a, c, list)


class BitPackTestCase(unittest.TestCase):
    def test_pack_bits(self):
        a = [0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0]
        b = pack_bits(a)
        self.assertIsInstance(b, list)
        self.assertSequenceEqual(b, [0b01001000, 0b00010010], list)
        a = [0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0]
        b = pack_bits(a)
        self.assertSequenceEqual(b, [0b01001000, 0b00000010], list)

    def test_unpack_bits(self):
        a = [0x34, 0x12]
        b = unpack_bits(a)
        self.assertIsInstance(b, list)
        self.assertSequenceEqual(
            b, [0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0], list
        )

    def test_pack_unpack(self):
        a = [0x34, 0x12, 0x02, 0x00]
        b = unpack_bits(a)
        c = pack_bits(b)
        self.assertSequenceEqual(a, c, list)


class MakeFrameTestCase(unittest.TestCase):
    def test_make_binary_frame(self):
        seq = 1
        target = Target(2, 3, 4, 5)
        timeout = 6
        header_3e = b"\x50\x00"
        header_4e = b"\x54\x00\x01\x00\x00\x00"
        target_bytes = b"\x02\x03\x04\x00\x05"
        timer_bytes = b"\x06\x00"
        buf = make_binary_frame(
            seq,
            target,
            timeout,
            SLMPCommand.SelfTest,
            0x0,
            b"\x05\x00ABCDE",
            3,
        )
        cmd_text = b"\x19\x06\x00\x00\x05\x00\x41\x42\x43\x44\x45"
        data_length = b"\x0D\x00"
        self.assertSequenceEqual(
            buf,
            header_3e + target_bytes + data_length + timer_bytes + cmd_text,
            bytes,
        )
        buf = make_binary_frame(
            seq,
            target,
            timeout,
            SLMPCommand.SelfTest,
            0x0,
            b"\x05\x00ABCDE",
            4,
        )
        self.assertSequenceEqual(
            buf,
            header_4e + target_bytes + data_length + timer_bytes + cmd_text,
            bytes,
        )

    def test_make_ascii_frame(self):
        seq = 1
        target = Target(2, 3, 4, 5)
        timeout = 6
        header_3e = b"5000"
        header_4e = b"540000010000"
        target_bytes = b"0203000405"
        timer_bytes = b"0006"
        buf = make_ascii_frame(
            seq, target, timeout, SLMPCommand.SelfTest, 0x0, b"0005ABCDE", 3
        )
        cmd_text = b"061900000005ABCDE"
        data_length = b"0015"
        self.assertSequenceEqual(
            buf,
            header_3e + target_bytes + data_length + timer_bytes + cmd_text,
            bytes,
        )
        buf = make_ascii_frame(
            seq, target, timeout, SLMPCommand.SelfTest, 0x0, b"0005ABCDE", 4
        )
        self.assertSequenceEqual(
            buf,
            header_4e + target_bytes + data_length + timer_bytes + cmd_text,
            bytes,
        )


if __name__ == "__main__":
    unittest.main()
