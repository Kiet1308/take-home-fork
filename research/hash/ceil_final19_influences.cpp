// Exact coordinate influence exclusion for the only nonzero-correlation tail.
// Reference edge counts are independently enumerated by final19_edges.cpp.
// Candidate: z=x XOR ceil((m*(x XOR Ki)+C mod2^32)/D), m odd.
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <map>
#include <set>
#include <unordered_map>
#include <vector>
using u64=uint64_t;using i64=int64_t;
constexpr u64 N=1ull<<32,L=N/2;
constexpr i64 edge0=1068417854,edge1=1074013576;
using Boundary=std::pair<u64,int>;

static int bit(u64 x,u64 d) {return int(((x+d-1)/d)&1);}
static std::vector<Boundary> bounds(u64 d,int parity) {
    std::vector<Boundary> b;
    int initial=bit(parity,d),last=bit(N-2+parity,d);
    if(initial!=last)b.emplace_back(0,initial-last);
    for(u64 j=0;j*d+1<N;++j) {
        u64 t=(j*d+2-parity)/2;if(t==0 || t>=L)continue;
        int jump=bit(2*t+parity,d)-bit(2*(t-1)+parity,d);
        if(jump)b.emplace_back(t,jump);
    }
    return b;
}
static i64 correlation(u64 d,u64 r,const std::vector<Boundary>& a,const std::vector<Boundary>&b) {
    std::vector<u64> stops{0,L};
    for(auto [p,s]:a)stops.push_back(p);
    for(auto [p,s]:b)stops.push_back((p+L-r)%L);
    std::sort(stops.begin(),stops.end());i64 result=0;
    for(size_t j=1;j<stops.size();++j) {
        u64 lo=stops[j-1],hi=stops[j];if(lo==hi)continue;
        if(bit(2*lo,d)!=bit(2*((lo+r)%L)+1,d))result+=hi-lo;
    }
    return result;
}
static std::set<u64> multipliers(u64 d,bool& flat) {
    auto a=bounds(d,0),b=bounds(d,1);
    std::unordered_map<u64,i64> changes;changes.reserve((a.size()+b.size())*8);
    for(auto [u,su]:a)for(auto [v,sv]:b)changes[(v+L-u)%L]+=2*su*sv;
    std::map<u64,i64> events;
    for(auto [p,v]:changes)if(p && v)events[p]=v;
    events[L]=0;
    i64 value=correlation(d,0,a,b),slope=0;u64 start=0;
    for(auto [v,sv]:b)slope+=sv*(1-2*bit(2*((v+L-1)%L),d));
    assert(correlation(d,1,a,b)-value==slope);
    std::set<u64> roots;
    for(auto [end,change]:events) {
        if(slope) {
            i64 num=edge0-value;
            if(num%slope==0) {
                i64 offset=num/slope;
                if(offset>=0 && u64(offset)<end-start) {
                    u64 r=start+offset;roots.insert(2*r+1);roots.insert(N-(2*r+1));
                    assert(correlation(d,r,a,b)==edge0);
                }
            }
        } else if(value==edge0) {
            std::cout<<"UNRESOLVED flat interval "<<start<<" "<<end<<"\n";flat=true;
        }
        value+=slope*(end-start);slope+=change;start=end;
    }
    assert(value==correlation(d,0,a,b));return roots;
}
static std::array<u64,4> second_counts(u64 d,u64 delta) {
    std::vector<u64> stops{0,N};
    if(bit(N-1,d)!=bit(0,d))stops.push_back((N-delta)%N);
    for(u64 j=0;j*d+1<N;++j) {
        u64 p=j*d+1;stops.push_back(p);stops.push_back((p+N-delta)%N);
    }
    std::sort(stops.begin(),stops.end());std::array<u64,4> counts{};
    for(size_t j=1;j<stops.size();++j) {
        u64 lo=stops[j-1],hi=stops[j];if(lo==hi)continue;
        if(bit(lo,d)==bit((lo+delta)%N,d))continue;
        for(u64 r=0;r<4;++r)counts[r]+=(hi+3-r)/4-(lo+3-r)/4;
    }
    return counts;
}

int main() {
    // Balance: |1-distance(N-1,2D*Z)|=1343488; D>=1343489.
    std::set<u64> ds;
    for(u64 value:{(N-1343488-2)/2,(N+1343488)/2})
        for(u64 i=1;i*i<=value;++i)if(value%i==0)
            for(u64 d:{i,value/i})if(d>=1343489)ds.insert(d);
    u64 survived=0;bool flat=false;
    for(auto d:ds) {
        auto roots=multipliers(d,flat);u64 keep=0;
        for(auto m:roots) {
            auto counts=second_counts(d,(2*m)%N);
            for(uint32_t r=0;r<4;++r)if(counts[r]+counts[(r+1)&3]==edge1) {
                std::cout<<"survivor D "<<d<<" m "<<m<<" residues "<<r<<"\n";++keep;
            }
        }
        survived+=keep;std::cout<<"D "<<d<<" first-edge multipliers "<<roots.size()<<" second-edge survivors "<<keep<<"\n";
    }
    std::cout<<"TOTAL divisors "<<ds.size()<<" survivors "<<survived<<" unresolved_flat "<<flat<<"\n";
}
