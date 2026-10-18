// Necessary invariance of bit31(m*x+C) under input bits20..29.
// With m odd, exact top-cube constancy first gives m = +/-1 mod4096.
// For each low input z, the high-input orbit has step +/-2^20 and
// length1024.  Its bit31 can be constant only when m*z+C mod2^31
// lies in a circular interval of W=2^30+2^20 consecutive words.
// For all z in [0,2^20), this is possible iff the largest circular gap
// of {m*z mod2^31} is at least 2^31-W+1.  Every loop below is exact.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <vector>

void run(unsigned shift) {
    uint32_t n = 1u << shift;
    constexpr uint32_t p = 1u << 20;
    uint32_t small_n = 1u << (shift - 20 + 1);
    std::vector<uint32_t> small_residues;
    std::vector<uint32_t> high_points(1024);
    for (uint32_t m=1; m<small_n; m+=2) {
        for (uint32_t h=0;h<1024;++h) high_points[h] = (m*h) & (small_n-1);
        std::sort(high_points.begin(), high_points.end());
        uint32_t gap=small_n-high_points.back();
        for (size_t j=1;j<high_points.size();++j)
            gap=std::max(gap, high_points[j]-high_points[j-1]);
        if (gap >= small_n/2+1) small_residues.push_back(m);
    }
    std::cout << "{\"shift\":" << shift << ",\"high_cube_modulus\":" << small_n << ",\"high_cube_residues\":[";
    for (size_t j=0;j<small_residues.size();++j) std::cout << (j ? "," : "") << small_residues[j];
    std::cout << "]}" << std::endl;
    if (small_residues != std::vector<uint32_t>({1, small_n-1})) {
        std::cerr << "Unexpected high-cube residues; the following interval reduction would need revision." << std::endl;
        std::exit(1);
    }
    uint32_t w = n - 1023*p;
    uint32_t required = n - w + 1;
    std::vector<uint32_t> candidates;
    for (uint32_t r : small_residues)
        for (uint32_t m = r; m < n; m += small_n) candidates.push_back(m);
    auto start = std::chrono::steady_clock::now();
    for (uint32_t count = 4; count <= p; count *= 2) {
        std::vector<uint32_t> kept;
        std::vector<uint32_t> points(count);
        for (uint32_t m : candidates) {
            uint32_t x = 0;
            for (uint32_t j = 0; j < count; ++j) {
                points[j] = x;
                x = (x + m) & (n-1);
            }
            std::sort(points.begin(), points.end());
            uint32_t gap = n - points.back();
            for (uint32_t j = 1; j < count; ++j)
                gap = std::max(gap, points[j] - points[j-1]);
            if (gap >= required) kept.push_back(m);
        }
        candidates.swap(kept);
        double sec = std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
        std::cout << "{\"shift\":" << shift << ",\"prefix\":" << count << ",\"surviving\":" << candidates.size()
                  << ",\"seconds\":" << sec << "}" << std::endl;
    }
    std::cout << "{\"shift\":" << shift << ",\"final_m_residues\":[";
    for (size_t j=0;j<candidates.size();++j) std::cout << (j ? "," : "") << candidates[j];
    std::cout << "]}" << std::endl;
}

int main() { run(30); run(31); }
