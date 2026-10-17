"""Exact Z4 lemma for the top-two-bit behavior of masked affine feeds.

If t(x+Q)-t(x)=alpha*Q and w(x+Q)-w(x)=beta*Q are constant,
the four outputs of n*(t(x)&K)+w(x) at x+j*Q have this form modulo4:
    n*((alpha*j+A)&k)+beta*j+B.
For every parameter tuple, every permutation of j has a constant odd slope,
and the slope does not depend on A. B has no effect on the slope. Thus a
permutation built this way has a constant quarter increment. OR follows by
t|K = t + K - (t&K). A final constant XOR preserves the invariant.
"""
from itertools import product

permutations=0
for alpha,n,beta,k in product(range(4),repeat=4):
    possible_slopes=set()
    for a in range(4):
        values=[(n*((alpha*j+a)&k)+beta*j)%4 for j in range(4)]
        if len(set(values))!=4:continue
        permutations+=1
        differences={(values[(j+1)%4]-values[j])%4 for j in range(4)}
        assert len(differences)==1,(alpha,n,beta,k,a,values)
        possible_slopes.update(differences)
    assert len(possible_slopes)<=1,(alpha,n,beta,k,possible_slopes)
print('Masked affine quarter lemma verified for all 1024 Z4 parameter tuples;',
      permutations,'permutation cases')

mask=(1<<12)-1
def core(x):
    return (9*(((33*x+0xe9f8cc1d)&mask)^((16896*x+0xaccf6200)&mask))+0xfd7046c5)&mask
increments=[(core(x+1024)-core(x))&mask for x in (0,1)]
assert increments==[1024,3072]
print('Reference core quarter increments at x=0,1:',increments)
