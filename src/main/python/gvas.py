"""
Lossless reader/writer for Unreal Engine "GVAS" save files (as used by DRG).

The save is a tree of tagged properties. Every container property stores its own
byte size, so the tree is re-serialized (sizes are recomputed) instead of patching
bytes at fixed offsets. dumps(loads(data)) returns the original bytes.
"""
import struct

# structs whose payload is not a tagged property list, and their payload size in bytes
NATIVE_STRUCTS = {
    "Guid": 16,
    "DateTime": 8,
    "Timespan": 8,
    "Vector": 12,
    "Rotator": 12,
    "Quat": 16,
    "LinearColor": 16,
    "Vector2D": 8,
    "IntPoint": 8,
}

SIMPLE_TYPES = {
    "IntProperty": "<i",
    "UInt32Property": "<I",
    "Int64Property": "<q",
    "FloatProperty": "<f",
    "DoubleProperty": "<d",
}
STRING_TYPES = ("StrProperty", "NameProperty", "ObjectProperty", "SoftObjectProperty")


class Reader(object):
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def unpack(self, fmt):
        size = struct.calcsize(fmt)
        value = struct.unpack_from(fmt, self.data, self.pos)[0]
        self.pos += size
        return value

    def raw(self, n):
        value = self.data[self.pos : self.pos + n]
        if len(value) != n:
            raise ValueError("unexpected end of save data at %d" % self.pos)
        self.pos += n
        return value

    def fstr(self):
        n = self.unpack("<i")
        if n == 0:
            return ""
        if n < 0:
            return self.raw(-n * 2)[:-2].decode("utf-16-le")
        return self.raw(n)[:-1].decode("latin-1")


def pack_fstr(s):
    if s == "":
        return struct.pack("<i", 0)
    try:
        b = s.encode("latin-1") + b"\x00"
        return struct.pack("<i", len(b)) + b
    except UnicodeEncodeError:
        b = s.encode("utf-16-le") + b"\x00\x00"
        return struct.pack("<i", -(len(b) // 2)) + b


class Prop(object):
    """
    One tagged property.

    value by type:
      Int/UInt32/Int64/Float/Double  number
      Bool                           bool
      Str/Name/Object/SoftObject     str
      Byte / Enum                    int (byte, enum_name "None") or str (enum value)
      Struct                         list of Prop, or for native structs a Guid hex str / raw bytes
      Array                          list of element values (struct arrays: list of Prop lists / Guid str)
      Set                            list of element values
      Map                            list of (key, value) tuples
      *DelegateProperty              raw bytes
    meta holds everything needed to write the property back out exactly.
    """

    def __init__(self, name, type_, value, **meta):
        self.name = name
        self.type = type_
        self.value = value
        self.meta = meta

    def __repr__(self):
        return "Prop(%r, %r, %r)" % (self.name, self.type, self.value)

    # convenience constructors for building new properties
    @classmethod
    def int_(cls, name, value):
        return cls(name, "IntProperty", value, pguid=None)

    @classmethod
    def guid(cls, name, hex_guid):
        return cls(
            name,
            "StructProperty",
            hex_guid.upper(),
            struct="Guid",
            sguid=b"\x00" * 16,
            pguid=None,
        )

    @classmethod
    def guid_array(cls, name, hex_guids):
        return cls(
            name,
            "ArrayProperty",
            [g.upper() for g in hex_guids],
            inner="StructProperty",
            pguid=None,
            inner_name=name,
            inner_type="StructProperty",
            struct="Guid",
            sguid=b"\x00" * 16,
            inner_pguid=None,
        )


class PropList(list):
    """Ordered list of Prop with lookup by name."""

    def get(self, name, default=None):
        for p in self:
            if p.name == name:
                return p
        return default

    def __getitem__(self, key):
        if isinstance(key, str):
            p = self.get(key)
            if p is None:
                raise KeyError(key)
            return p
        return list.__getitem__(self, key)

    def remove_named(self, name):
        for i, p in enumerate(self):
            if p.name == name:
                del self[i]
                return True
        return False


class SaveFile(object):
    def __init__(self, header, props, trailer):
        self.header = header  # raw bytes up to and including the save class name
        self.props = props
        self.trailer = trailer  # bytes after the terminating "None"

    def find(self, *path):
        """save.find('CampaignSave', 'ActiveCampaign') -> Prop (or None if absent)"""
        props = self.props
        prop = None
        for name in path:
            prop = props.get(name)
            if prop is None:
                return None
            props = prop.value if isinstance(prop.value, list) else None
        return prop


# ---------------------------------------------------------------- reading


def loads(data):
    r = Reader(data)
    if r.raw(4) != b"GVAS":
        raise ValueError("not a GVAS save file")
    r.unpack("<i")  # save game version
    r.unpack("<i")  # package version
    r.raw(6)  # engine version major/minor/patch
    r.unpack("<I")  # engine build
    r.fstr()  # engine branch
    r.unpack("<i")  # custom version format
    for _ in range(r.unpack("<i")):
        r.raw(20)  # custom version guid + version
    r.fstr()  # save game class
    header = data[: r.pos]
    props = read_props(r)
    return SaveFile(header, props, data[r.pos :])


def read_props(r):
    props = PropList()
    while True:
        name = r.fstr()
        if name == "None":
            return props
        type_ = r.fstr()
        size = r.unpack("<q")
        props.append(read_prop(r, name, type_, size))


def read_prop_guid(r):
    return r.raw(16) if r.raw(1) != b"\x00" else None


def read_prop(r, name, type_, size):
    if type_ in SIMPLE_TYPES:
        pguid = read_prop_guid(r)
        return Prop(name, type_, r.unpack(SIMPLE_TYPES[type_]), pguid=pguid)
    if type_ == "BoolProperty":
        value = r.unpack("<B") != 0
        return Prop(name, type_, value, pguid=read_prop_guid(r))
    if type_ in STRING_TYPES:
        pguid = read_prop_guid(r)
        return Prop(name, type_, r.fstr(), pguid=pguid)
    if type_ in ("ByteProperty", "EnumProperty"):
        enum = r.fstr()
        pguid = read_prop_guid(r)
        if type_ == "ByteProperty" and enum == "None":
            value = r.unpack("<B")
        else:
            value = r.fstr()
        return Prop(name, type_, value, enum=enum, pguid=pguid)
    if type_ == "StructProperty":
        struct_name = r.fstr()
        sguid = r.raw(16)
        pguid = read_prop_guid(r)
        return Prop(
            name,
            type_,
            read_struct(r, struct_name),
            struct=struct_name,
            sguid=sguid,
            pguid=pguid,
        )
    if type_ == "ArrayProperty":
        inner = r.fstr()
        pguid = read_prop_guid(r)
        count = r.unpack("<i")
        if inner == "StructProperty":
            inner_name = r.fstr()
            inner_type = r.fstr()
            r.unpack("<q")  # element bytes, recomputed on write
            struct_name = r.fstr()
            sguid = r.raw(16)
            inner_pguid = read_prop_guid(r)
            values = [read_struct(r, struct_name) for _ in range(count)]
            return Prop(
                name,
                type_,
                values,
                inner=inner,
                pguid=pguid,
                inner_name=inner_name,
                inner_type=inner_type,
                struct=struct_name,
                sguid=sguid,
                inner_pguid=inner_pguid,
            )
        if inner == "ByteProperty":
            return Prop(name, type_, r.raw(count), inner=inner, pguid=pguid)
        values = [read_simple(r, inner) for _ in range(count)]
        return Prop(name, type_, values, inner=inner, pguid=pguid)
    if type_ == "SetProperty":
        inner = r.fstr()
        pguid = read_prop_guid(r)
        removed = r.unpack("<i")
        if removed != 0:
            raise ValueError("set with removed elements is not supported")
        count = r.unpack("<i")
        values = [read_set_elem(r, inner) for _ in range(count)]
        return Prop(name, type_, values, inner=inner, pguid=pguid)
    if type_ == "MapProperty":
        key_type = r.fstr()
        value_type = r.fstr()
        pguid = read_prop_guid(r)
        removed = r.unpack("<i")
        if removed != 0:
            raise ValueError("map with removed elements is not supported")
        count = r.unpack("<i")
        items = []
        for _ in range(count):
            key = read_map_elem(r, key_type, True)
            value = read_map_elem(r, value_type, False)
            items.append((key, value))
        return Prop(
            name, type_, items, key_type=key_type, value_type=value_type, pguid=pguid
        )
    if type_.endswith("DelegateProperty"):
        pguid = read_prop_guid(r)
        return Prop(name, type_, r.raw(size), pguid=pguid)
    raise ValueError("unsupported property type %s (%s)" % (type_, name))


def read_struct(r, struct_name):
    if struct_name == "Guid":
        return r.raw(16).hex().upper()
    if struct_name in NATIVE_STRUCTS:
        return r.raw(NATIVE_STRUCTS[struct_name])
    return read_props(r)


def read_simple(r, type_):
    if type_ in SIMPLE_TYPES:
        return r.unpack(SIMPLE_TYPES[type_])
    if type_ == "BoolProperty":
        return r.unpack("<B") != 0
    if type_ in STRING_TYPES or type_ == "EnumProperty":
        return r.fstr()
    if type_ == "ByteProperty":
        return r.unpack("<B")
    raise ValueError("unsupported array element type %s" % type_)


def read_set_elem(r, type_):
    if type_ == "StructProperty":
        return r.raw(16).hex().upper()  # sets in DRG saves only hold Guids
    return read_simple(r, type_)


def read_map_elem(r, type_, is_key):
    if type_ == "StructProperty":
        return r.raw(16).hex().upper() if is_key else read_props(r)
    return read_simple(r, type_)


# ---------------------------------------------------------------- writing


def dumps(save):
    return save.header + write_props(save.props) + save.trailer


def write_props(props):
    out = []
    for p in props:
        payload, extra = write_prop_body(p)
        out.append(pack_fstr(p.name))
        out.append(pack_fstr(p.type))
        out.append(struct.pack("<q", len(payload)))
        out.append(extra)
        out.append(payload)
    out.append(pack_fstr("None"))
    return b"".join(out)


def pack_prop_guid(pguid):
    return b"\x00" if pguid is None else b"\x01" + pguid


def write_prop_body(p):
    """returns (payload, bytes that sit between the size field and the payload)"""
    t, v, m = p.type, p.value, p.meta
    pg = pack_prop_guid(m.get("pguid"))
    if t in SIMPLE_TYPES:
        return struct.pack(SIMPLE_TYPES[t], v), pg
    if t == "BoolProperty":
        return b"", struct.pack("<B", 1 if v else 0) + pg
    if t in STRING_TYPES:
        return pack_fstr(v), pg
    if t in ("ByteProperty", "EnumProperty"):
        payload = struct.pack("<B", v) if m["enum"] == "None" and t == "ByteProperty" else pack_fstr(v)
        return payload, pack_fstr(m["enum"]) + pg
    if t == "StructProperty":
        return (
            write_struct(v, m["struct"]),
            pack_fstr(m["struct"]) + m["sguid"] + pg,
        )
    if t == "ArrayProperty":
        inner = m["inner"]
        if inner == "StructProperty":
            elems = b"".join(write_struct(e, m["struct"]) for e in v)
            payload = (
                struct.pack("<i", len(v))
                + pack_fstr(m["inner_name"])
                + pack_fstr(m["inner_type"])
                + struct.pack("<q", len(elems))
                + pack_fstr(m["struct"])
                + m["sguid"]
                + pack_prop_guid(m["inner_pguid"])
                + elems
            )
        elif inner == "ByteProperty":
            payload = struct.pack("<i", len(v)) + bytes(v)
        else:
            payload = struct.pack("<i", len(v)) + b"".join(
                write_simple(e, inner) for e in v
            )
        return payload, pack_fstr(inner) + pg
    if t == "SetProperty":
        inner = m["inner"]
        payload = struct.pack("<ii", 0, len(v)) + b"".join(
            bytes.fromhex(e) if inner == "StructProperty" else write_simple(e, inner)
            for e in v
        )
        return payload, pack_fstr(inner) + pg
    if t == "MapProperty":
        parts = [struct.pack("<ii", 0, len(v))]
        for key, value in v:
            parts.append(write_map_elem(key, m["key_type"], True))
            parts.append(write_map_elem(value, m["value_type"], False))
        return b"".join(parts), pack_fstr(m["key_type"]) + pack_fstr(m["value_type"]) + pg
    if t.endswith("DelegateProperty"):
        return v, pg
    raise ValueError("unsupported property type %s (%s)" % (t, p.name))


def write_struct(value, struct_name):
    if struct_name == "Guid":
        return bytes.fromhex(value)
    if struct_name in NATIVE_STRUCTS:
        return value
    return write_props(value)


def write_simple(value, type_):
    if type_ in SIMPLE_TYPES:
        return struct.pack(SIMPLE_TYPES[type_], value)
    if type_ == "BoolProperty":
        return struct.pack("<B", 1 if value else 0)
    if type_ in STRING_TYPES or type_ == "EnumProperty":
        return pack_fstr(value)
    if type_ == "ByteProperty":
        return struct.pack("<B", value)
    raise ValueError("unsupported element type %s" % type_)


def write_map_elem(value, type_, is_key):
    if type_ == "StructProperty":
        return bytes.fromhex(value) if is_key else write_props(value)
    return write_simple(value, type_)
