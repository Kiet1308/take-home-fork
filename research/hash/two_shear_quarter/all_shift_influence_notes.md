# Complete input-31 influence classification, gamma=1 only

This is a separate necessary-condition classification for

    b=T_s(m1*(x XOR Ki)+C1) XOR K
    f=b0 XOR bit_t(m2*b+C2) XOR constant,

with odd MAD coefficients and s,t in 1..31. Its 143 passing pairs are exact influence witnesses, not solutions of the full low-bit identity. The quarter-orbit theorem in all_shift_quarter_exclusion.md subsequently excludes all 961 pairs.

The exact result is 818 EXCLUDED, 143 PASSES_INFLUENCE, and zero unresolved. The algorithm examines 97,052 circular windows, with maximum profile modulus 16,384. Every profile is independently checked by a modular-inverse rolling recurrence. Every witness is independently evaluated by an exact BigInt floor sum.

## Reduction

Set T=1,295,908,864=9887*2^17, U=2^31-T=6497*2^17, and j=31-s. An input-31 flip maps b to b XOR e31 XOR ej. If j>=t the candidate derivative is constant. Otherwise the affine coordinate-j edge count, on its 2^(t+1)-element active domain, must equal

    I=L*2^(t-14),

where L=6497 if exactly one of j=0 or t=31 holds, and L=9887 otherwise. The required full count is U in the former case and T in the latter. Every active-domain edge repeats 2^(31-t) times.

For t<14, I is nonintegral. At t=14 it is odd, whereas every odd-affine non-top coordinate edge count is even. All remaining cases have t>=15.

Put

    H=2^j, Nlow=2H, P=2^(t+1-j), E=t-14-j,
    r=m2 mod P, d=min(r,P-r),
    W=#{0<=z<H : bit_j(m2*z+C2)=1}.

For a positive residue r=d,

    I=H*(d-1)+2*W.

For a negative residue r=P-d, I=H*(d+1)-2W. Negating the affine word as -(m2*b+C2)-1 complements the output bit and leaves all influence counts unchanged, so it is sufficient to classify the positive residue. The edge identity is proved in the quarter-orbit note.

## E>0: endpoint congruences

Here R=I/H=L*2^E is even. Since d is odd and |R-d|<=1, only d=R-1 or R+1 is possible; respectively W=H or W=0.

A half-domain count W in {0,H} forces m2 congruent to +1 or -1 modulo Nlow. Indeed the affine selected bit is then z_j plus a constant on its entire domain, so its coordinate-zero edge count is zero. The exact coordinate-zero edge formula forces coefficient distance one.

Conversely those coefficients provide the necessary constant half profile:

- m2=+1 modulo Nlow: C2=0 gives W=0 and C2=H gives W=H.
- m2=-1 modulo Nlow: C2=H-1 gives W=0 and C2=Nlow-1 gives W=H.

The classifier checks compatibility of m2=d modulo P with these two residues modulo Nlow. Since both moduli are powers of two this is exact. It records 86 passing pairs and excludes 67 incompatible pairs.

## E=0: a balanced half profile

Here d=L and W=H/2. Choose

    m2=L,
    C2=(m2-1-H)/2 modulo H.

Reflection z to H-1-z complements the affine word modulo 2H, so every reflected pair contributes one selected bit. All 17 such pairs pass.

## E<0: a small fixed residue

Write k=-E, so 1<=k<=13. Then

    P=2^(15-k),
    d=2*floor(L/2^(k+1))+1,
    W/H=(L mod 2^(k+1))/2^(k+1).

If Nlow<P, the coefficient modulo Nlow is fixed by d. The algorithm enumerates the complete circular profile over all C2 modulo Nlow. This modulus is at most 16,384.

If Nlow>=P, put delta=Nlow/P and split z=a+delta*u. For each a the coarse word runs through a half-domain profile of multiplier d modulo P. Consequently

    delta*min(W_P(d,*)) <= W <= delta*max(W_P(d,*)).

Only the small profile P<=16,384 must be enumerated.

The sole remaining extremal obstruction is (s,t)=(9,31). Here j=22, P=1024, d=203, delta=8192, and W/H=33/64. The small profile reaches its maximum 264 only at bases 611 and 615. For a and a+delta/2, the coarse bases differ by one of 101,102,613,614 modulo 1024, using the two possible coefficient lifts modulo 2048. None is a difference of two members of {611,615}. Both fibers cannot be maximal, so this pair is excluded.

For every other pair whose projection bound survives, the small representative m2=d has an exact base witness. The algorithm finds C2 between 0 and H by sign-bracket bisection of the exact floor-sum count. Monotonicity is not assumed: changing C2 by one changes W by at most one, so an integer sign bracket always retains a root. Every returned root is checked by the independent exact edge formula.

## Top-middle survivors of this invariant

At t=31 the 13 survivors are

    s={1,2,3,14,23,24,25,26,27,28,29,30,31}.

The other 130 passing pairs have t<=30. All are subsequently excluded by quarter-orbit statistics.

Run all_shift_influence.js to regenerate the complete 961-row JSON, coefficient/base witnesses, reasons and profile bounds. No solver is used.
