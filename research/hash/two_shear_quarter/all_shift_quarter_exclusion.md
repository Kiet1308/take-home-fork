# All first/right-middle shift pairs: quarter-orbit obstruction

## Result and precise scope

Let arithmetic be modulo N=2^32, with unsigned logical right shifts and bit numbering starting at zero. Write

    a = m1 * (x XOR Ki) + C1
    b = a XOR (a >> s) XOR K
    f(x) = gamma * b0 XOR bit_t(m2*b + C2) XOR c.

For every odd m1, all word constants Ki,C1,K,C2, both gamma in {0,1}, and all s,t in 1..31, f cannot equal bit 1 of the reference hash H. The result also includes even m2 by an exact reduction at the end of this note.

This excludes the necessary low-bit identity of the two-right-shear/free-parity hash topology

    c = m2*b+C2
    d = c XOR(c>>t)
    e = m3*d+C3
    q = e>>31
    y = 2*u*e+q,

where the multipliers needed for bijectivity are odd. Here y1=e0=b0 XOR c_t XOR a constant, so gamma=1 applies. The gamma=0 result also covers extracting the middle quotient bit without adding b0. The theorem concerns raw or constant-XOR input/output gauges and a downstream computation whose first prefix retains only b. Original-input bypasses and general linear or nonlinear encodings require their own analysis.

The proof below closes all 961 shift pairs directly. It does not depend on a solver timeout or on the larger influence-only classification supplied as a separate reusable certificate.

## 1. Two exact reference statistics

After the reference first prefix, the remaining triangular word map is

    G(b) = 9 * ((33*b + 0xe9f8cc1d)
                XOR (16896*b + 0xaccf6200)) + 0xfd7046c5.

The relevant reference bit is h(b)=G1(b) XOR G17(b), a function of the low 18 bits. The verifier compares this fused expression with the independent original stages on every one of the 262,144 low-domain inputs:

    c = 33*b + 0x165667b1
    d = (c + 0xd3a2646c) XOR (c<<9)
    G = 9*d + 0xfd7046c5.

Flipping raw input bit 31 flips b12 (and b31, which h does not use). On the 18-bit domain the active coordinate-12 edge count is 79,096. Each such edge repeats 16,384 times in the full word domain, giving

    T = 79,096 * 16,384 = 1,295,908,864
    U = 2^31 - T = 851,574,784 = 6497 * 2^17.

An edge is counted once, using the input whose flipped coordinate is zero.

Now group the raw inputs into cyclic quarter orbits

    {x, x+Q, x+2Q, x+3Q}, Q=2^30.

The six dihedral classes of four binary outputs are, in order:

1. weight 0;
2. weight 1;
3. two adjacent ones;
4. two opposite ones, 0101 or 1010;
5. weight 3;
6. weight 4.

The low-18-bit orbit histogram, grouping b11 and b12, is exactly

    [2693, 16308, 23240, 4294, 16308, 2693].

There are 65,536 such low-domain orbits; every count repeats 16,384 times at full width. In particular both constant and opposite patterns occur. Their union occupies

    (2693+4294+2693)/65536 = 9680/65536 = 605/4096

of all quarter orbits. Complementing the target preserves the statistics used in this proof.

## 2. Why every first coefficient, base and constant XOR disappear

An odd first MAD maps quarter orbits bijectively to quarter orbits. Within an orbit its top two-bit coordinate changes by multiplication by an odd number modulo 4, followed by a translation: a rotation or reflection of the four positions.

XOR by an arbitrary word constant also permutes the orbits and acts dihedrally on their top two positions. The right shear T_s(a)=a XOR(a>>s) is an invertible binary-linear map, so

    T_s(a) XOR K = T_s(a XOR T_s^-1(K)).

Consequently the complete six-class histogram is independent of m1,C1,Ki and K. We may compute it on b=T_s(a), taking a itself uniformly through the word domain.

There is an equally simple invariant for a single input-31 flip. For every odd m1,

    b(x XOR 2^31) = b(x) XOR 2^31 XOR 2^(31-s).

Let j=31-s. Uniformity and edge pairing make the resulting active-edge count independent of the first parameters.

## 3. All middle shifts t<=30

First take 2<=s<=30, set l=2^(30-s), and write a=A+Qv with A<Q and v in {0,1,2,3}. Put B=T_s(A); B is a permutation of the low 30-bit words. Since A>>s<l, the two bits at l and 2l agree in A and B. Write

    B = B0 + k*l,

where those two bits of B0 are cleared and k is in {0,1,2,3}. Reorder the orbit by u=k XOR v. This is dihedral. The four b values become

    B0 + l*u + Q*(k XOR u).

For k even this is an arithmetic progression with step l+Q; for k odd its step is l-Q. The bases differ, which is harmless. Modulo 2^(t+1), the two steps coincide whenever t<=30, because their difference is 2^31. After the second MAD there is therefore one fixed modular step for every orbit.

For a fixed step r on a circle of even length M, four samples of the top bit at B,B+r,B+2r,B+3r cannot admit both a constant pattern and an opposite pattern as B varies. To see this, replace r by its circular distance d<=M/2 and reverse the order if needed. A constant pattern means the four points fit in a half-open semicircle. If d<=M/3, their gaps are d,d,d,M-3d, so this requires d<M/6. If d>=M/3, their sorted gaps are 3d-M,M-2d,d,M-2d, all at most M/2, so a constant pattern is impossible. When d<M/6, the three successive steps span less than a semicircle and cannot cross three alternating bit boundaries; hence an opposite pattern is impossible.

The b0 term is constant within the orbit for s<30. For s=30 it is u0, which swaps constant and opposite patterns. A constant term can only complement a pattern. Thus neither gamma value can supply both pattern types, contradicting the reference histogram.

The endpoints are immediate. For s=1 and t<=30, the input-31 derivative is constant: j=30 is at or above the selected bit. For s=31 and t<=29, each quarter pattern depends only on v1 and has no opposite pattern. For s=31,t=30, the v0 coefficient is one, so no quarter is constant. This closes all 930 pairs with t<=30.

## 4. A necessary coefficient distance when t=31

For now let 2<=s<=30, so j=31-s>0. Flipping b31 complements bit31 of an odd affine map, while b0 does not change. Thus matching the input-31 count requires the affine coordinate-j edge count to equal U.

Put

    H=2^j, P=2^(32-j)=2^(s+1),
    r=m2 mod P, d_m=min(r,P-r),
    epsilon=+1 if r<P/2, and -1 otherwise,
    W=#{0<=z<H : bit_j(m2*z+C2)=1}.

Then the exact affine edge count is

    I_j = H*(d_m-epsilon)+2*epsilon*W.

For completeness, partition inputs with bit j zero as z+2Hk. For fixed z, the coarse affine words run once through all P/2 residues of one parity. The active intervals for a positive odd distance d_m contain d_m-1 even starts and d_m+1 odd starts; a negative distance reverses these counts. The parity of the coarse base is bit_j(m2*z+C2), giving the formula.

In particular,

    |I_j/H-d_m| <= 1
    d_m <= 6497*2^(s-14)+1.

The exact formula, including its endpoint signs, is checked separately on 24,512 small-word coefficient/base/coordinate cases.

## 5. The top-middle quarter mixture

Continue with 2<=s<=30. Let M=N/l=2^(s+2). The two full-word steps l+Q and l-Q differ by N/2 after an odd second multiplication. They no longer coincide at t=31: changing between them XORs the four-bit pattern by u0. The correct invariant here is the UNION of constant and opposite patterns, which that change preserves.

For each B0, the four k cases can therefore be counted using the single step m2*(l+Q), at bases

    m2*B0+C2+k*m2*Q, k=0,1,2,3.

The b0 contribution also preserves this union for either gamma. Write

    B0=z+4*l*w,
    0<=z<l, 0<=w<M/16,
    q_z=floor((m2*z+C2)/l) mod 4,
    a=m2*(1+2^s) mod M.

For fixed z, varying w and k covers every coarse base congruent to q_z modulo 4 exactly once. Indeed the variable contribution is

    4*m2*(w+k*M/16),

and m2 is odd.

Let A_r(a) count the bases q modulo M with q congruent to r modulo 4 for which the four top bits at q,q+a,q+2a,q+3a are constant or opposite. The exact full-word union count is

    sum_{0<=z<l} A_(q_z)(a).

There are l*M/4=Q total orbits.

Reduce a by a sign and a multiple of M/2; both operations preserve this union up to translating the base. Its effective distance is

    d = distance(a,{0,M/2}) = 2^s-d_m.

The constant-or-opposite base set is two circular intervals, each of integer length

    L = max(M/2-3*d,0) = max(3*d_m-2^s,0).

Hence, in every residue class modulo 4,

    A_r <= 2*ceil(L/4).

These intervals can also be computed exactly from at most eight boundary points. The executable certificate checks 65,528 odd-step profiles, plus 33,024 full direct mixture cases. It uses exact modular multiplication; for large s the step is evaluated as m2+(m2 mod4)*2^s modulo M, avoiding floating-point multiplication beyond 2^53.

### Generic range s>=6

The coefficient bound gives

    L <= (3107/16384)*2^s+3,

so the union fraction is at most

    3107/32768 + 3/2^s.

Its largest value on s>=6 is

    4643/32768 < 4840/32768 = 605/4096,

the reference union fraction. This closes every s in 6..30 at t=31.

### The four small shifts

The exact edge formula leaves one odd distance for each of s=2,3,4,5:

| s | d_m | L | Obstruction |
|---|---:|---:|---|
| 2 | 1 | 0 | No constant-or-opposite orbit |
| 3 | 3 | 1 | Union fraction at most 1/8 |
| 4 | 7 | 5 | Projected input-31 count impossible |
| 5 | 13 | 7 | Every A_r<=4; union fraction at most 1/8 |

For s=3, M=32 and m2 is congruent to +3 or -3 modulo 16. The interval support has two singleton bases, in one residue class modulo 4. Write z=z0+(l/4)*u with 0<=u<4. The q_z classes come from four points congruent to a translate of {0,3,6,9} or its negative modulo 16. Any cyclic interval of four residues contains at most two points. Consequently any one q_z class has at most l/2 members, and the union count is at most 2*(l/2)=l. Since Q=8l, its fraction is at most 1/8.

For s=4 the exact edge formula requires W/H to be 353/2048 for r=7, or 1695/2048 for r=25 modulo 32. On the 32-element profile, every base gives between 6 and 10 ones among 16 consecutive input indices, for both coefficients 7 and 25. Project the full interval by writing z=z0+delta*u, delta=2H/32, 0<=u<16. Each z0 fiber is one of those profiles. Therefore W/H must lie in [6/16,10/16]=[3/8,5/8], contradicting both required fractions. The verifier prints all 32 profile values for both coefficients.

## 6. The two endpoint first shifts at t=31

For s=1, retain the top three bits of b. If p=A29 and v=(v0,v1) is the quarter coordinate, their word is

    (p XOR v0)+2*(v0 XOR v1)+4*v1.

The four words are [0,3,6,5] for p=0 and [1,2,7,4] for p=1. Lower b bits only change the affine base. The 64 exact cases comprise four odd coefficients modulo 8, two p values, and eight bases. Coefficients 1 or 7 never have a constant pattern; coefficients 3 or 5 never have an opposite pattern. The b0 term is constant within these orbits. Both gamma values are excluded.

For s=31, write epsilon=+1 for A0=0 and -1 for A0=1. After removing an irrelevant common output constant, the gamma=1 quarter pattern is the top bit at

    [B, B+d, B+epsilon*m2, B+epsilon*m2+d],
    d=m2*Q mod N = +Q or -Q.

For each output value, the starts of constant pairs separated by d form one length-Q interval. The two intervals for output zero and one differ by 2Q.

With gamma=1, a constant quadruple requires its two pair starts in the SAME interval. This requires circular coefficient distance min(m2,N-m2)<Q. But the input-31 count is the affine coordinate-zero count, so that distance is T-1 or T+1, both greater than Q.

With gamma=0, the second pair in the displayed rectangle is complemented. A constant quadruple therefore requires starts in the OPPOSITE intervals, which requires coefficient distance>Q. Now the input-31 count forces the affine coordinate-zero count to be U, giving distance U-1 or U+1, both less than Q. Again no constant quarter can occur.

The interval conditions are strict because the intervals contain Q integer points and opposite boundaries cannot both be included. This closes s=t=31 for both gamma values.

## 7. Even second coefficients and two-bit bypasses

If m2=2^v*mu with mu odd, then for t>=v,

    bit_t(m2*b+C2)
      = bit_(t-v)(mu*b+floor(C2/2^v)).

Bits below v are constant. At t=v the result is b0 plus a constant. Every nontrivial case with t>v reduces to the theorem for an odd coefficient and an effective shift at least one. A zero coefficient is constant.

A constant or b0 itself cannot match the reference, since its input-31 derivative is constant and the reference count is strictly between zero and 2^31.

For an odd coefficient and an effective selected bit at least one, the pair (b0,q0) is uniform on its four Boolean values. A balanced Boolean function of two bits is one of b0, q0, b0 XOR q0, or their complements. Thus the same theorem covers any balanced low-bit bypass using only these two low sources. If the first MAD is even and all later values descend only from b, the full word computation loses information and cannot equal the bijective reference hash.

## 8. A forbidden simplification, verification and companion evidence

The t=31 sign variation must not be discarded. There is a concrete counterexample to extending the fixed-step argument from t<=30 without the union mixture:

    word width n=5, s=2, t=4, m2=3, C2=3,
    b=a XOR(a>>2), f=b0 XOR bit4(3*b+3).

The orbit with low part A=1 gives 1111, while A=2 gives 0101. Thus one candidate can contain both constant and opposite patterns. The union argument above accounts for precisely this effect.

The standalone all_shift_quarter_verify.js prints a deterministic JSON certificate. Its checks are safeguards for the identities and small finite endpoint tables; the preceding algebra supplies the full-width proof.

| Check | Cases |
|---|---:|
| Reference fused/original core agreement | 262,144 words |
| Affine coordinate-distance formula | 24,512 |
| Fixed-step constant/opposite lemma | 4,092 |
| Exact union interval profiles | 65,528 |
| Direct mixtures, both gamma values | 33,024 |
| Full histograms under arbitrary first parameters and constant XOR gauges | 768 |
| s=1 endpoint table | 64 |
| Final endpoint constant-pair inequalities | 174,720 |

A separately written peer checker passed another 41,184 direct mixtures and 1,120 first-parameter/gauge cases. Its source is maintained by the parent agent as an independent certificate.

The companion all_shift_influence.js classifies only the original gamma=1 input-31 invariant. It excludes 818 pairs and gives explicit odd coefficient/base witnesses for all 143 passing pairs, with zero unresolved pairs, using 97,052 exact circular windows of maximum modulus 16,384. These are influence witnesses, not full hash candidates. The quarter proof subsequently excludes every pair, including all those witnesses.

Earlier bounded SMT UNKNOWN results remain timeout observations. No positive full-word candidate or cycle improvement is claimed by this mathematical checkpoint.
