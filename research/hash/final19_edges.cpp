// Exact first two coordinate influences of the parity before a final T19.
#include <cstdint>
#include <iostream>
#include <chrono>
static uint32_t bit(uint32_t a) {
    uint32_t b=a^(a>>19)^0xc761c23cu;
    uint32_t e=9u*((33u*b+0xe9f8cc1du)^(16896u*b+0xaccf6200u))+0xfd7046c5u;
    return (e^(e>>16)^(e>>19))&1u;
}
int main() {
    auto start=std::chrono::steady_clock::now();uint64_t edge0=0,edge1=0;
    for(uint64_t i=0;i<(1ull<<30);++i) {
        uint32_t a=0x7ed55d16u+uint32_t(i)*16388u;
        uint32_t p0=bit(a),p1=bit(a+4097u)^1,p2=bit(a+8194u),p3=bit(a+12291u)^1;
        edge0+=(p0^p1)+(p2^p3);edge1+=(p0^p2)+(p1^p3);
    }
    std::cout<<"edge0 "<<edge0<<" edge1 "<<edge1<<" seconds "
             <<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<"\n";
}
