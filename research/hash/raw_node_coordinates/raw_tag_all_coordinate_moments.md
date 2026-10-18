# Exact stratified ANF moments for every raw-node output coordinate

## Result and purpose

The collector evaluated every one of the 4,294,967,296 possible 32-bit inputs
to the original six-stage hash. It retained 31 packed coefficients in each
of the four cosets determined by raw input bits30 and31. Runtime in the
functions JavaScript environment was 1,118.663 seconds.

These moments are the full-domain input to the independently implemented
251-component classifier and verifier in the accompanying
fresh_architecture checkpoint. That classification has no surviving
component or direction. Its precise consequence is:

For independently chosen invertible maps
E_in(x)=x XOR J_in(x>>30) and E_out(x)=x XOR J_out(x>>30),
every coordinate of E_out composed with H composed with E_in inverse,
and also the XOR of its coordinates0 and1, has no affine derivative
along any nonzero encoded input direction.

This statement allows nonlinear two-bit tag corrections and independent
input/output representations. It is a scoped architectural obstruction;
it does not assert a global lower bound on the kernel's cycle count.

## Coefficient definition and packing

For each raw top-two-bit tag t, let h_t be the restriction of H to the
30 remaining input variables. The stored total is the XOR of its packed
output over every input in that coset. Its selected bit is the ANF
coefficient of the full degree30 monomial.

Stored missing[i] is the XOR over the inputs in that coset whose raw bit i
is zero. Its selected bit is the ANF coefficient of the degree29 monomial
containing every low variable except i, for i=0,...,29.

Output bits1 through31 store the corresponding H bits. Packed bit0 stores
Q=H30*H31 over GF(2), replacing H0. This loses no needed leading coefficient:
H0 XOR H16 equals F0 plus a constant, and F0 depends only on raw input
bits0 through19. Its restricted degree29 and30 coefficients vanish.
Therefore the leading coefficients of H0 equal those of H16.

The target list comprises H_k XOR T(H30,H31), k=0,...,29, for all eight
two-variable truth tables up to complementation; the three nonzero
linear forms of H30,H31; and H0 XOR H1 XOR T for all eight tables up to
complementation. There are 240+3+8=251 cases. A balanced component of an
invertible permutation of two bits is always a nonzero linear form up
to a constant, so these three top-coordinate cases are complete.

## Exact streaming computation

Each coset is split into blocks of 2^16 consecutive low inputs.
A block stores the packed original six-stage hash values in a Uint32Array.
For bit i below16, pairwise XOR folding combines the two adjacent blocks
that differ in that input bit. XORing the right elements before folding
gives the contribution from inputs having that bit equal to one.
After16 folds the remaining word is the block total.

For bits16 through29, the bit is constant throughout a block, so the
block total contributes to its upper-half moment exactly when that
input bit is one. Finally missing[i]=total XOR upper[i].

All hash arithmetic uses the original 32-bit wrapping additions, shifts,
and XORs. The largest ordinary integer intermediate is exactly representable
in JavaScript; the independent checker uses the separately fused hash with
Math.imul. No floating approximation, random estimate, or domain subsampling
appears in the full pass.

## Independent checks and recovered global coefficients

The default command runs 1,024 hash inputs over four restricted cosets,
computes all coefficients by direct restricted-domain XOR sums using the
fused hash, and compares them with the collector's folding implementation.
All comparisons passed.

For any selected output component, write c_t for its stored total bit
and v_t[i] for its missing bit. Its global degree31 coefficient vector a is

- a_i = XOR over t of v_t[i], for i<30;
- a_30 = c_0 XOR c_2;
- a_31 = c_0 XOR c_1.

Recovering four previously computed independent full32 vectors gave exact
agreement:

| Component | Degree31 vector |
| --- | --- |
| H1 | 0x72a80000 |
| H30 | 0x9f504000 |
| H31 | 0x1985e000 |
| H30*H31 | 0x64727000 |

The four row lengths are30. Their unsigned XOR checksums, excluding total,
are respectively3391992364,849320606,2097792264,93801879.
These checksums were also used to validate transport to the independent
classifier.

## Why the stratification closes high input directions

A nonzero encoded top-two-bit direction pairs the four raw tags in one
of three perfect matchings. Within each paired pair, the input map is
a low30 XOR translation. An affine derivative would therefore make
the paired restricted functions equal, after translation, up to an affine
function of the low inputs.

The full degree30 coefficients must agree in each pair. If both are zero,
their degree29 vectors must agree. If both are one, translation by delta
changes the degree29 vector by delta, so the only possible translation is
delta=v_t XOR v_u. The classifier evaluates that unique translated
difference, reconstructs its affine coefficients from zero and the30
unit vectors, and uses an explicit additional input to refute affinity.

The companion classifier and independently coded verifier rejected all
251 components. Verification counted188 immediate low-direction exclusions,
63 low-direction affine-plus-tag-product contradictions,1,162 high-pair
degree mismatches,344 high-pair affine contradictions, and12,806 fitted
basis values. Every candidate high pairing fails; no unbounded search
or assumption about unknown translations remains.

The low-direction certificate uses the global nonzero degree31 vector:
the leading derivative equations force any possible nonzero direction
to equal that vector. The permitted raw right-hand side is an arbitrary
affine function plus the common input-top-bit product; exact witnesses
exclude all remaining candidates. The companion note states this proof
and the even/odd tail corollaries in full.

## Reproduction

Run the small independent collector check:

```sh
node raw_tag_all_coordinate_moments.mjs
```

Recompute all full32 coefficients:

```sh
node raw_tag_all_coordinate_moments.mjs --full32 --output=recomputed_moments.json
```

The recorded rows, excluding runtime metadata, must match exactly.
The classifier and its independent verifier consume the recorded rows;
they do not need another full-domain pass. No kernel, benchmark, simulator,
or frozen test source was changed by this research.
