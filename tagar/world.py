#!/usr/bin/python3.4
from time import monotonic
from agarnet.buffer import BufferStruct
import agarnet.world


class Cell(agarnet.world.Cell):
    def __init__(self, *args, **kwargs):
        super(Cell, self).__init__(*args, **kwargs)
        self.last_update_time = monotonic()

    def update(self, cid=-1, x=0, y=0, size=0, name='',
               color=(1, 0, 1), is_virus=False, is_agitated=False, cell=None):
        super(Cell, self).update(cid, x, y, size, name, color, is_virus, is_agitated, cell)
        self.last_update_time = monotonic()

    def pack_cell_update(self, buf=BufferStruct()):
        buf.push_uint32(self.cid)
        buf.push_float32(self.pos.x)
        buf.push_float32(self.pos.y)
        buf.push_float32(self.size)
        buf.push_len_str16(self.name)
        tuple(map(lambda rgb: buf.push_uint8(int(rgb * 255.0)), self.color))
        buf.push_bool(self.is_virus)
        buf.push_bool(self.is_agitated)
        return buf

    def unpack_cell_update(self, buf):
        cid = buf.pop_uint32()
        x = buf.pop_float32()
        y = buf.pop_float32()
        size = buf.pop_float32()
        name = buf.pop_len_str16()
        color = (buf.pop_uint8(), buf.pop_uint8(), buf.pop_uint8())
        is_virus = buf.pop_bool()
        is_agitated = buf.pop_bool()
        self.update(cid, x, y, size, name, color, is_virus, is_agitated)
        return buf


class World:
    def __init__(self):
        self.cells = {}
        self.added_cells = []
        self.updated_cells = []
        self.removed_cells = []
        self.last_update_time = monotonic()

    def reset(self):
        self.cells = {}
        self.last_update_time = monotonic()

    def has_update(self):
        return self.added_cells or self.updated_cells or self.removed_cells

    def update_cell(self, cell):
        # check for added cells
        if cell.cid not in self.cells:
            self.cells[cell.cid] = Cell()
            self.cells[cell.cid].update(cell=cell)
            self.added_cells.append(cell.cid)
            return

        # check for updated cells (updated only once per cycle!)
        if cell.cid not in self.updated_cells:
            if self.cells[cell.cid].pos.x != cell.pos.x or self.cells[cell.cid].pos.y != cell.pos.y or self.cells[cell.cid].size != cell.size:
                self.cells[cell.cid].update(cell=cell)
                self.updated_cells.append(cell.cid)

    def remove_cell(self, cid):
        if cid in self.cells:
            del self.cells[cid]
            self.removed_cells.append(cid)

    def remove_cells(self, cid_list):
        for cid in cid_list:
            self.remove_cell(cid)

    def pre_update_world(self):
        self.added_cells = []
        self.updated_cells = []
        self.removed_cells = []

    def update_world(self, cells):
        # remove old cells
        self.remove_cells([cid for cid in self.cells.keys() if cid not in cells])

        # update cells
        for cell in cells.values():
            if cell.cid > 0:
                self.update_cell(cell)

        self.last_update_time = monotonic()

    def parse_world_update(self, buf):
        self.pre_update_world()
        self.unpack_world_update(buf)
        self.last_update_time = monotonic()

    def pack_world_update(self, buf=BufferStruct()):
        # pack added cells
        buf.push_uint32(len(self.added_cells))
        for cid in self.added_cells:
            self.cells[cid].pack_cell_update(buf)

        # pack updated cells
        buf.push_uint32(len(self.updated_cells))
        for cid in self.updated_cells:
            self.cells[cid].pack_cell_update(buf)

        # pack removed cells
        buf.push_uint32(len(self.removed_cells))
        for cid in self.removed_cells:
            buf.push_uint32(cid)

        return buf

    def unpack_world_update(self, buf):
        # unpack added cells
        for i in range(0, buf.pop_uint32()):
            c = Cell()
            c.unpack_cell_update(buf)
            self.update_cell(c)

        # unpack updated cells
        for i in range(0, buf.pop_uint32()):
            c = Cell()
            c.unpack_cell_update(buf)
            self.update_cell(c)

        # unpack removed cells
        for i in range(0, buf.pop_uint32()):
            self.remove_cell(buf.pop_uint32())
        return buf
