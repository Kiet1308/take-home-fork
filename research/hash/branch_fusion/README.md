# Parity-consumer and compact-state audit

This investigation targets the validated 865-cycle kernel. It does not produce
a faster kernel. The requested target below 850 remains open.

## Existing flags

There are 448 eight-lane flags, costing 3,584 scalar-equivalent arithmetic
operations: 32 vector flags in each of rounds 0 through 9 and 11 through 14.
The flags at depths 2 and 4 already use `h | 0xfffffffe` to produce the signed
digits -2 and -1 directly. That accounts for 96 vectors; the other 352 use `% 2`.
No flag is emitted after the wrap round 10 or the final round 15.

Every retained flag reaches a real node-selection condition or a bounded
address calculation. An ordinary `vselect` tests a whole word for nonzero;
passing the unmasked hash word therefore does not implement parity selection.
At depth 9 the two operations `p = h % 2` and `address = MAD(parent, 2, p)`
already combine extraction with the sole necessary pointer update as far as
the current representation permits. An OR formulation still needs two ops.
These observations concern the current graph, not every possible program.

## Exact two-operation branch extraction

Let all arithmetic wrap at 32 bits, and let the final hash words be

```
e = 9*d + 0xfd7046c5
h = e XOR (e >> 16)          # encoded output; raw output adds C5 by XOR
```

Then the encoded branch is exactly

```
p = MAD(d, 0x80048000, 0xa3628000) >> 31
```

The raw branch uses `0x23628000` as the additive constant. To see the identity,
multiply `e` by `0x80008000`. Only `e[16]` and `e[0]` contribute to output bit
31, and their modulo-two sum is their XOR. Composing with `9*d + C4` gives
the stated multiplier and constants.

This takes two ordinary operations. Alongside the unchanged value tail it
costs one more operation than extracting the flag from the already computed
hash. Its shorter dependency path is a separate scheduling question.

## Valid 31-bit encoding and exact costs

There is a valid compact encoding

```
S(h) = (T16(h)) >> 1 = e >> 1
```

where `T16(x) = x XOR (x >> 16)` is its own inverse. Unlike losing the top
bit of `e`, this loses exactly the `h[0]` kernel direction. The pair `(S,p)` is
injective. Its explicit reconstruction is

```
e0 = p XOR ((S >> 15) & 1)
e = (S << 1) | e0
h = e XOR (e >> 16)
```

Full reconstruction is unnecessary when the next node path already carries
the missing input parity. The next 31-bit hash input can be formed by

```
z = S XOR (S >> 16) XOR ((node XOR C5) >> 1)
a = MAD(z, 8194, C0 + 4097*q)
```

Here `q = raw_previous_h[0] XOR raw_node[0]`; the previous branch is identified
by the selected node's left/right position. The `C0 + 4097*q` word still has to
be selected or prepared for the node. It is not a compile-time constant for a
runtime random tree.

The exact arithmetic counts, excluding the existing one node XOR and pointer
work from every row, are:

| Representation | Prefix through `d` | Value tail | Branch | Next input conversion | Total |
|---|---:|---:|---:|---:|---:|
| Ordinary encoded `h` | 7 | 3 | 1 | 0 | 11 |
| `h >> 1`, using the ordinary `h` and flag | 7 | 4 | 1 | 0 | 12 |
| `e >> 1` | 7 | 2 | 2 | 2 | 13 |

For `h >> 1`, first compute the ordinary three-op value tail, then `h >> 1`
and `h & 1`. This costs five tail/flag operations, for twelve operations in
total. Computing the half-value directly with `e = MAD(...)`, `e >> 1`,
`e >> 17`, and XOR plus the separate two-op branch would instead cost thirteen
operations; it is not the cheapest obvious implementation.
For `e >> 1`, the next input conversion is the two-op `S XOR (S >> 16)`.
The two-op branch above is used in that row. Converting the first MAD to an
even multiplier accounts for the path-carried input bit but does not remove
the additional operations.

Node preparation adds costs beyond the table. A straightforward prepared
record needs `(node XOR C5) >> 1` (two scalar ops instead of the existing one
XOR), plus the parity-dependent first-MAD bias. In a perfectly aligned vector
batch the bias costs parity extraction plus one vector MAD; a scalar version
requires extraction, multiplication, and addition because there is no scalar
MAD. The sign and additive constant of the MAD can absorb the known parent
branch. It also needs an extra metadata field and a way to
align/select that field with each walker's node. The compact encodings are
already worse before charging these costs.

## More path history is not automatically a free bit

The current node encodes all earlier branch choices. A general compressed
state could use that information, so requiring only `(encoded_h, current_p)`
to be injective would be too strong for every conceivable architecture.

For example, given the parity `q` of the current hash input, the ordinary
first prefix satisfies `q = b[0] XOR b[19] XOR C1[0] XOR C1[19]`.
Thus `b[19]` is redundant if the rest of `b` and `q` are retained. The odd
triangular middle permutation also means that toggling `e[19]` always toggles
the inverse input parity. Omitting `e[19]` could in principle be repaired from
that parity, but extracting the remaining bits and recovering the nonlinear
inverse relation is additional work. Omitting `b[31]` or `e[31]` has no such
repair from `q`, since the inverse input parity is insensitive to those bits.
No cheaper executable tail follows from this observation here.

## Reproduction

Run `python audit.py /absolute/path/to/take-home-fork`, or omit the path when
the script is inside the repository or beside a `take-home-fork` checkout.
It compiles the
unchanged kernel, counts the retained IR consumers, and verifies the branch
and compact-state identities on edge cases and 100,000 independently sampled
32-bit words. It does not alter tests or simulator semantics. Algebra above
establishes the identities beyond the finite verification sample.
