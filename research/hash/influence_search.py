"""Exact necessary coordinate-influence invariants for first-MAD synthesis."""
import json


def floor_sum(n, mod, a, b):
    answer = 0
    while True:
        if a >= mod:
            answer += n*(n-1)*(a//mod)//2
            a %= mod
        if b >= mod:
            answer += n*(b//mod)
            b %= mod
        ymax = a*n+b
        if ymax < mod:
            return answer
        n, b = divmod(ymax, mod)
        a, mod = mod, a


def ones_half(mul, constant, bit):
    n = 1 << bit
    return floor_sum(n,n,mul,constant)-2*floor_sum(n,2*n,mul,constant)


def active_edges(mul, constant, bit, width=20):
    period = 1 << (width-bit)
    reduced = mul % period
    distance = min(reduced, period-reduced)
    sign = 1 if reduced < period//2 else -1
    return (1 << bit)*(distance-sign)+2*sign*ones_half(mul,constant,bit)


def search(width=20, original_mul=4097, original_constant=0x7ed55d16):
    n = 1 << width
    target = [active_edges(original_mul,original_constant,i,width) for i in range(width-1)]
    print('target', target, flush=True)
    results = {}
    for mul in sorted({v % n for v in (4095,4097,-4095,-4097)}):
        choices = [0]
        for bit in range(width-1):
            choices = [c for lo in choices for c in (lo,lo+(1<<bit))
                       if active_edges(mul,c,bit,width) == target[bit]]
            print('mul',hex(mul),'bits',bit+1,'choices',len(choices),flush=True)
            if not choices:
                break
        results[str(mul)] = choices
    print(json.dumps(results), flush=True)
    return results


if __name__ == '__main__':
    for width in range(3,8):
        n = 1 << width
        for mul in range(1,n,2):
            for constant in range(n):
                for bit in range(width-1):
                    brute = sum((((mul*x+constant)%n) >> (width-1)) != (((mul*(x^(1<<bit))+constant)%n) >> (width-1))
                                for x in range(n) if x & (1<<bit) == 0)
                    assert brute == active_edges(mul,constant,bit,width), (width,mul,constant,bit,brute,active_edges(mul,constant,bit,width))
    print('All small-width coordinate influence formulas verified.',flush=True)
    result = search()
    with open('influence_constants.json','w') as output:
        json.dump(result, output)
