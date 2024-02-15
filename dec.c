typedef unsigned char uint8_t;

void dec(uint8_t *data) {
    if (data[0] == 0x1E) {
        return;
    }
    uint8_t *p = data + 1 + 8*16/2-1, *q = data + 8*16-2;
    for (; q>=data; p--, q-=2) {
        uint8_t lx0 = *p & 3;
        uint8_t hx0 = (*p >> 2) & 3;
        uint8_t lx1 = (*p >> 4) & 3;
        uint8_t hx1 = *p >> 6;

        q[0] = lx0 | (hx0 << 4);
        q[1] = lx1 | (hx1 << 4);
    }
}
