// Exact two-bit contingency invariant for every output XOR mask and first D.
// The final even divisor D2 is supplied as an argument.  Any first affine
// coefficient, input XOR mask and invertible triangular middle core are allowed.
// Build: c++ -O3 -std=c++17 divisor_two_bit.cpp -o divisor_two_bit
#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <map>
#include <set>
#include <vector>

using i64=int64_t;using u64=uint64_t;
constexpr uint32_t size=1u<<21,block=1u<<16,groups=32;
constexpr u64 words=1ull<<32;
using Fingerprint=std::array<u64,9>;
using Matrix=std::array<i64,16>;

static int sign(uint32_t x) {return __builtin_parity(x)?-1:1;}
static void walsh(std::vector<i64>& a) {
    for(uint32_t len=1;len<size;len<<=1)
        for(uint32_t i=0;i<size;i+=len<<1)
            for(uint32_t j=0;j<len;++j) {
                i64 u=a[i+j],v=a[i+j+len];a[i+j]=u+v;a[i+j+len]=u-v;
            }
}

static std::array<std::vector<i64>,3> reference() {
    std::array<std::vector<i64>,3> q;
    for(auto&v:q)v.resize(size);
    for(uint32_t b=0;b<size;++b) {
        uint32_t e=9u*((33u*b+0xe9f8cc1du)^(16896u*b+0xaccf6200u))+0xfd7046c5u;
        uint32_t x=((b^(b>>19)^0xc761c23cu)-0x7ed55d16u)&3u;
        assert(q[0][e&(size-1)]==0);
        for(uint32_t j=1;j<=3;++j)q[j-1][e&(size-1)]=sign(x&j);
    }
    for(auto&v:q)walsh(v);return q;
}

static std::array<std::vector<i64>,3> shear(uint32_t d) {
    constexpr uint32_t stride=block+1;
    std::array<std::vector<i64>,3> diff,s;
    for(auto&v:diff)v.resize(groups*stride);
    for(auto&v:s)v.resize(size);
    for(u64 p=0,lo=0;lo<words;lo+=d,++p) {
        u64 hi=std::min(words,lo+d);uint32_t tp=uint32_t(p)^(uint32_t(p)>>16);
        for(u64 left=lo;left<hi;) {
            uint32_t h=uint32_t(left>>16);u64 right=std::min(hi,(u64(h)+1)<<16);
            uint32_t start=uint32_t(left&(block-1)),finish=uint32_t(right-(u64(h)<<16));
            uint32_t mask=(h^tp)&(block-1),g=((h^(tp>>16))&(groups-1))*stride;
            while(start<finish) {
                uint32_t len=start?(start&-start):block;
                while(len>finish-start)len>>=1;
                uint32_t dest=(start^mask)&~(len-1);
                for(uint32_t j=1;j<=3;++j) {
                    int a=sign(mask&j);diff[j-1][g+dest]+=a;diff[j-1][g+dest+len]-=a;
                }
                start+=len;
            }
            left=right;
        }
    }
    for(uint32_t g=0;g<groups;++g)
        for(uint32_t j=1;j<=3;++j) {
            i64 acc=0;
            for(uint32_t r=0;r<block;++r) {
                acc+=diff[j-1][g*stride+r];s[j-1][g*block+r]=sign(r&j)*acc;
            }
        }
    for(uint32_t seed:{0u,1u,123459u,635183u,891913u,2097151u}) {
        std::array<i64,3> expected{};
        for(uint32_t upper=0;upper<2048;++upper) {
            uint32_t e=seed|(upper<<21),y=e^(e>>16),x=0;
            for(int bit=31;bit>=0;--bit)x|=(((y>>bit)^((x/d)>>bit))&1u)<<bit;
            assert((x^(x/d))==y);
            for(uint32_t j=1;j<=3;++j)expected[j-1]+=sign(x&j);
        }
        for(uint32_t j=0;j<3;++j)assert(s[j][seed]==expected[j]);
    }
    for(auto&v:s)walsh(v);return s;
}

static Matrix first_matrix(uint32_t d) {
    Matrix m{};u64 complete=words/d,remainder=words%d;
    auto add=[&](uint32_t qclass,u64 length,u64 count) {
        uint32_t start=uint32_t(u64(qclass)*d)&3;
        for(uint32_t row=0;row<4;++row) {
            uint32_t offset=(row-start)&3;
            u64 hits=length/4+(offset<length%4);
            m[row*4+(row^qclass)]+=i64(count*hits);
        }
    };
    for(uint32_t q=0;q<4;++q)add(q,d,complete/4+(q<complete%4));
    add(uint32_t(complete)&3,remainder,1);return m;
}

static Fingerprint fingerprint(const std::array<i64,9>& c) {
    Fingerprint f;
    for(uint32_t j=0;j<9;++j)f[j]=std::abs(c[j]);
    // Character1 is fixed up to sign. Characters2 and3 can be swapped.
    if(f[1]>f[2])std::swap(f[1],f[2]);
    if(f[3]>f[6])std::swap(f[3],f[6]);
    std::array<u64,4> sub{f[4],f[5],f[7],f[8]};std::sort(sub.begin(),sub.end());
    f[4]=sub[0];f[5]=sub[1];f[7]=sub[2];f[8]=sub[3];return f;
}
static std::array<i64,9> correlations(const Matrix&m) {
    std::array<i64,9> c{};
    for(uint32_t a=1;a<=3;++a)for(uint32_t b=1;b<=3;++b)
        for(uint32_t x=0;x<4;++x)for(uint32_t y=0;y<4;++y)
            c[(a-1)*3+b-1]+=m[x*4+y]*sign((a&x)^(b&y));
    return c;
}
static Matrix from_correlations(const std::array<i64,9>&c) {
    Matrix m{};
    for(uint32_t x=0;x<4;++x)for(uint32_t y=0;y<4;++y) {
        i64 total=words;
        for(uint32_t a=1;a<=3;++a)for(uint32_t b=1;b<=3;++b)
            total+=c[(a-1)*3+b-1]*sign((a&x)^(b&y));
        assert(total%16==0);m[x*4+y]=total/16;
    }
    return m;
}
static Matrix canonical(const Matrix&m) {
    Matrix best;best.fill(words);
    for(uint32_t a:{1u,3u})for(uint32_t b=0;b<4;++b)
        for(uint32_t c:{1u,3u})for(uint32_t d=0;d<4;++d) {
            Matrix cand;
            for(uint32_t x=0;x<4;++x)for(uint32_t y=0;y<4;++y)
                cand[x*4+y]=m[((a*x+b)&3)*4+((c*y+d)&3)];
            best=std::min(best,cand);
        }
    return best;
}

int main(int argc,char**argv) {
    uint32_t d=argc>1?uint32_t(std::strtoul(argv[1],nullptr,0)):65538;
    if(d<2 || (d&1))return 2;
    auto begin=std::chrono::steady_clock::now();auto q=reference(),s=shear(d);
    std::array<std::vector<i64>,9> c;
    for(uint32_t a=0;a<3;++a)for(uint32_t b=0;b<3;++b) {
        auto&v=c[a*3+b];v.resize(size);
        for(uint32_t j=0;j<size;++j)v[j]=q[a][j]*s[b][j];
        walsh(v);for(auto&x:v){assert(x%size==0);x/=size;}
    }
    q={};s={};
    std::set<u64> deltas;for(auto x:c[0])deltas.insert(std::abs(x));
    std::set<uint32_t> divisors;
    for(u64 delta:deltas) {
        if(delta>=words)continue;
        assert(delta%4==0);
        for(u64 value:{(words+delta)/2,(words-delta)/2})
            for(u64 f=1;f*f<=value;++f)if(value%f==0)
                for(u64 d1:{f,value/f})if(d1>=2 && !(d1&1) && d1>=delta && d1<words)
                    divisors.insert(uint32_t(d1));
    }
    std::map<Fingerprint,std::vector<uint32_t>> candidates;
    std::map<Matrix,std::vector<uint32_t>> canonical_candidates;
    for(auto d1:divisors) {
        auto m=first_matrix(d1);
        candidates[fingerprint(correlations(m))].push_back(d1);
        canonical_candidates[canonical(m)].push_back(d1);
    }
    std::map<Matrix,bool> cached;
    u64 passed_fingerprint=0,passed_exact=0;std::set<uint32_t> surviving_d1;
    for(uint32_t j=0;j<size;++j) {
        std::array<i64,9> corr;for(uint32_t k=0;k<9;++k)corr[k]=c[k][j];
        auto it=candidates.find(fingerprint(corr));if(it==candidates.end())continue;
        ++passed_fingerprint;auto raw=from_correlations(corr);
        auto old=cached.find(raw);bool matched=false;
        if(old!=cached.end())matched=old->second;
        else {
            auto cm=canonical(raw);auto found=canonical_candidates.find(cm);
            if(found!=canonical_candidates.end()) {
                matched=true;
                for(auto d1:found->second)surviving_d1.insert(d1);
            }
            cached[raw]=matched;
        }
        if(matched) {
            ++passed_exact;
            if(passed_exact<=8)std::cout<<"surviving mask "<<std::hex<<j<<std::dec<<" correlation "<<corr[0]<<"\n";
        }
    }
    std::cout<<"D2="<<d<<" deltas="<<deltas.size()<<" candidate D1="<<divisors.size()
             <<" fingerprint masks="<<passed_fingerprint<<" exact masks="<<passed_exact
             <<" / "<<size<<" surviving D1="<<surviving_d1.size()<<"\n";
    if(surviving_d1.size()<64)for(auto d1:surviving_d1)std::cout<<"D1 "<<d1<<"\n";
    std::cout<<"seconds "<<std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count()<<"\n";
}
