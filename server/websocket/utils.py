import struct
import array

def decode(buf):

    result = {'data': '', 'remaining': 0, 'opcode':0}

    hlen = 2
    remaining = len(buf)
    result['remaining'] = remaining
    if remaining < hlen:
        return result

    b1, b2 = struct.unpack_from('>BB', buf)
    result['opcode'] = b1 & 0x0f
    has_mask = (b2 & 0x80) >> 7

    length = b2 & 0x7f
    if length == 126:
        hlen = 4
        if remaining < hlen:
            return result
        (length,) = struct.unpack_from('>xxH', buf)
    elif length == 127:
        hlen = 10
        if remaining < hlen:
            return result
        (length,) = struct.unpack_from('>xxQ', buf)


    full_len = hlen + has_mask * 4 + length

    if len(buf) < full_len:
        return result

    result['remaining'] = len(buf) - full_len

    if has_mask:
        mask = buf[hlen:hlen+4]
        result['data'] = unmask(buf, hlen, length, mask)


    return result



def encode(buf, opcode):

    b1 = 0x80 | (opcode & 0x0f) # FIN + opcode
    length = len(buf)
    if length <= 125:
        header = struct.pack('>BB', b1, length)
    elif length > 125 and payload_len < 65536:
        header = struct.pack('>BBH', b1, 126, length)
    elif length >= 65536:
        header = struct.pack('>BBQ', b1, 127, length)

    return header + buf



def unmask(buf, hlen, length, mask):
    data = array.array('B')
    mask = map(ord, mask)

    start = hlen + 4
    end = start + length
    data.fromstring(buf[start:end])
    for i in xrange(len(data)):
        data[i] ^= mask[i % 4]
    return data.tostring()
