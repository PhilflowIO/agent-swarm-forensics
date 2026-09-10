// Unabhängige Reproduktion des Agenten-Scans: CPython random.Random(seed).randrange(204)
// für alle 32-Bit-Seeds; zählt Seeds, deren erste 3 bzw. 4 Ziehungen 44,1,46,(13) sind.
// CPython-Semantik: seed(int) -> init_by_array([seed]) ; getrandbits(8) = genrand_uint32()>>24 ;
// _randbelow(204): k=8 Bit, Verwerfen wenn r>=204.
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define N 624
#define M 397
#define NOUT 12
static uint32_t base[N];
static void init_genrand(uint32_t *mt, uint32_t s){ mt[0]=s; for(int i=1;i<N;i++) mt[i]=1812433253U*(mt[i-1]^(mt[i-1]>>30))+i; }
static inline int scan_seed(uint32_t seed, int n, const int *target, int tlen, uint32_t *mt){
    memcpy(mt, base, sizeof(uint32_t)*N);
    int i=1, j=0; uint32_t key=seed; int keylen=1; int k=N;
    for(;k;k--){ mt[i]=(mt[i]^((mt[i-1]^(mt[i-1]>>30))*1664525U))+key+j; i++; j++; if(i>=N){mt[0]=mt[N-1]; i=1;} if(j>=keylen) j=0; }
    for(k=N-1;k;k--){ mt[i]=(mt[i]^((mt[i-1]^(mt[i-1]>>30))*1566083941U))-i; i++; if(i>=N){mt[0]=mt[N-1]; i=1;} }
    mt[0]=0x80000000U;
    // Twist nur für die ersten NOUT Wörter (brauchen mt[kk], mt[kk+1], mt[kk+M])
    int matched=0;
    for(int kk=0; kk<NOUT; kk++){
        uint32_t y=(mt[kk]&0x80000000U)|(mt[kk+1]&0x7fffffffU);
        uint32_t v=mt[kk+M]^(y>>1)^((y&1U)?0x9908b0dfU:0U);
        v^=(v>>11); v^=(v<<7)&0x9d2c5680U; v^=(v<<15)&0xefc60000U; v^=(v>>18);
        int r=v>>24;
        if(r>=n) continue;
        if(r!=target[matched]) return matched;
        matched++; if(matched==tlen) return matched;
    }
    return matched;
}
int main(int argc,char**argv){
    int n = argc>1? atoi(argv[1]):204;
    int target[4]={44,1,46,13};
    init_genrand(base,19650218U);
    // Selbsttest
    uint32_t mt[N]; int m=scan_seed(1646124819U,n,target,4,mt);
    printf("selftest seed 1646124819 matched=%d\n",m); fflush(stdout);
    if(argc>2 && !strcmp(argv[2],"selftest")) return 0;
    long long c3=0,c4=0; 
    #pragma omp parallel
    {
        uint32_t mtl[N]; long long l3=0,l4=0;
        #pragma omp for schedule(dynamic,1<<20)
        for(long long s=0; s<(1LL<<32); s++){
            int r=scan_seed((uint32_t)s,n,target,4,mtl);
            if(r>=3){ l3++; if(r==4){ l4++; 
                #pragma omp critical
                printf("MATCH4 seed=%lld\n",s); fflush(stdout);} }
        }
        #pragma omp atomic
        c3+=l3;
        #pragma omp atomic
        c4+=l4;
    }
    printf("n=%d matched_first3=%lld matched_first4=%lld\n",n,c3,c4);
    return 0;
}
