/* Standalone scrypt block hash for InfiniteRicks — no Boost dependency */
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <openssl/sha.h>

typedef struct HMAC_SHA256Context {
    SHA256_CTX ictx;
    SHA256_CTX octx;
} HMAC_SHA256_CTX;

static inline uint32_t be32enc_val(uint32_t x) {
    return ((x & 0xff) << 24) | ((x & 0xff00) << 8) | ((x & 0xff0000) >> 8) | ((x & 0xff000000) >> 24);
}

static void HMAC_SHA256_Init(HMAC_SHA256_CTX *ctx, const void *_K, size_t Klen) {
    unsigned char pad[64];
    unsigned char khash[32];
    const unsigned char *K = (const unsigned char *)_K;
    if (Klen > 64) {
        SHA256(K, Klen, khash);
        K = khash;
        Klen = 32;
    }
    SHA256_Init(&ctx->ictx);
    memset(pad, 0x36, 64);
    for (size_t i = 0; i < Klen; i++) pad[i] ^= K[i];
    SHA256_Update(&ctx->ictx, pad, 64);
    SHA256_Init(&ctx->octx);
    memset(pad, 0x5c, 64);
    for (size_t i = 0; i < Klen; i++) pad[i] ^= K[i];
    SHA256_Update(&ctx->octx, pad, 64);
    memset(khash, 0, 32);
}

static void HMAC_SHA256_Update(HMAC_SHA256_CTX *ctx, const void *in, size_t len) {
    SHA256_Update(&ctx->ictx, in, len);
}

static void HMAC_SHA256_Final(unsigned char digest[32], HMAC_SHA256_CTX *ctx) {
    unsigned char ihash[32];
    SHA256_Final(ihash, &ctx->ictx);
    SHA256_Update(&ctx->octx, ihash, 32);
    SHA256_Final(digest, &ctx->octx);
    memset(ihash, 0, 32);
}

static void PBKDF2_SHA256(const uint8_t *passwd, size_t passwdlen, const uint8_t *salt,
    size_t saltlen, uint64_t c, uint8_t *buf, size_t dkLen) {
    HMAC_SHA256_CTX PShctx, hctx;
    uint8_t ivec[4];
    uint8_t U[32], T[32];
    for (size_t i = 0; i * 32 < dkLen; i++) {
        uint32_t iv = be32enc_val((uint32_t)(i + 1));
        memcpy(ivec, &iv, 4);
        memcpy(&hctx, &PShctx, sizeof(HMAC_SHA256_CTX));
        HMAC_SHA256_Init(&PShctx, passwd, passwdlen);
        HMAC_SHA256_Update(&PShctx, salt, saltlen);
        memcpy(&hctx, &PShctx, sizeof(HMAC_SHA256_CTX));
        HMAC_SHA256_Update(&hctx, ivec, 4);
        HMAC_SHA256_Final(U, &hctx);
        memcpy(T, U, 32);
        for (uint64_t j = 2; j <= c; j++) {
            HMAC_SHA256_Init(&hctx, passwd, passwdlen);
            HMAC_SHA256_Update(&hctx, U, 32);
            HMAC_SHA256_Final(U, &hctx);
            for (int k = 0; k < 32; k++) T[k] ^= U[k];
        }
        size_t clen = dkLen - i * 32;
        if (clen > 32) clen = 32;
        memcpy(&buf[i * 32], T, clen);
    }
    memset(&PShctx, 0, sizeof(PShctx));
}

#define ROTL32(x,n) (((x)<<(n))|((x)>>(32-(n))))

static inline void xor_salsa8(unsigned int B[16], const unsigned int Bx[16]) {
    unsigned int x00,x01,x02,x03,x04,x05,x06,x07,x08,x09,x10,x11,x12,x13,x14,x15;
    x00 = (B[0] ^= Bx[0]); x01 = (B[1] ^= Bx[1]); x02 = (B[2] ^= Bx[2]); x03 = (B[3] ^= Bx[3]);
    x04 = (B[4] ^= Bx[4]); x05 = (B[5] ^= Bx[5]); x06 = (B[6] ^= Bx[6]); x07 = (B[7] ^= Bx[7]);
    x08 = (B[8] ^= Bx[8]); x09 = (B[9] ^= Bx[9]); x10 = (B[10] ^= Bx[10]); x11 = (B[11] ^= Bx[11]);
    x12 = (B[12] ^= Bx[12]); x13 = (B[13] ^= Bx[13]); x14 = (B[14] ^= Bx[14]); x15 = (B[15] ^= Bx[15]);
    for (int i = 0; i < 8; i += 2) {
        x04 ^= ROTL32(x00+x12,7); x09 ^= ROTL32(x05+x01,7); x14 ^= ROTL32(x10+x06,7); x03 ^= ROTL32(x15+x11,7);
        x08 ^= ROTL32(x04+x00,9); x13 ^= ROTL32(x09+x05,9); x02 ^= ROTL32(x14+x10,9); x07 ^= ROTL32(x03+x15,9);
        x12 ^= ROTL32(x08+x04,13); x01 ^= ROTL32(x13+x09,13); x06 ^= ROTL32(x02+x14,13); x11 ^= ROTL32(x07+x03,13);
        x00 ^= ROTL32(x12+x08,18); x05 ^= ROTL32(x01+x13,18); x10 ^= ROTL32(x06+x02,18); x15 ^= ROTL32(x11+x07,18);
        x01 ^= ROTL32(x00+x03,7); x06 ^= ROTL32(x05+x04,7); x11 ^= ROTL32(x10+x09,7); x12 ^= ROTL32(x15+x14,7);
        x02 ^= ROTL32(x01+x00,9); x07 ^= ROTL32(x06+x05,9); x08 ^= ROTL32(x11+x10,9); x13 ^= ROTL32(x12+x15,9);
        x03 ^= ROTL32(x02+x01,13); x04 ^= ROTL32(x07+x06,13); x09 ^= ROTL32(x08+x11,13); x14 ^= ROTL32(x13+x12,13);
        x00 ^= ROTL32(x03+x02,18); x05 ^= ROTL32(x04+x07,18); x10 ^= ROTL32(x09+x08,18); x15 ^= ROTL32(x14+x13,18);
    }
    B[0]+=x00; B[1]+=x01; B[2]+=x02; B[3]+=x03; B[4]+=x04; B[5]+=x05; B[6]+=x06; B[7]+=x07;
    B[8]+=x08; B[9]+=x09; B[10]+=x10; B[11]+=x11; B[12]+=x12; B[13]+=x13; B[14]+=x14; B[15]+=x15;
}

static void scrypt_core(unsigned int *X, unsigned int *V) {
    for (int i = 0; i < 1024; i++) {
        memcpy(&V[i * 32], X, 128);
        xor_salsa8(&X[0], &X[16]);
        xor_salsa8(&X[16], &X[0]);
    }
    for (int i = 0; i < 1024; i++) {
        int j = 32 * (X[16] & 1023);
        for (int k = 0; k < 32; k++) X[k] ^= V[j + k];
        xor_salsa8(&X[0], &X[16]);
        xor_salsa8(&X[16], &X[0]);
    }
}

void scrypt_blockhash(const void* input, unsigned char result[32]) {
    unsigned int X[32];
    unsigned int V[1024 * 32];
    unsigned char xbuf[128];
    PBKDF2_SHA256((const uint8_t*)input, 80, (const uint8_t*)input, 80, 1, xbuf, 128);
    memcpy(X, xbuf, 128);
    scrypt_core(X, V);
    memcpy(xbuf, X, 128);
    PBKDF2_SHA256((const uint8_t*)input, 80, xbuf, 128, 1, result, 32);
}

#ifdef STANDALONE_TEST
int main() {
    unsigned char header[80] = {0};
    uint32_t nVersion = 1;
    memcpy(header, &nVersion, 4);
    unsigned char merkle[32];
    for (int i=0;i<32;i++) {
        sscanf("63f41eb2a1ad819aace407b1694e05e09cc6503fea38dc7a9302ce07bbba4c07"+i*2, "%2hhx", &merkle[i]);
    }
    memcpy(header+36, merkle, 32);
    uint32_t nTime=1585247880, nBits=0x1e0fffff, nNonce=1125206;
    memcpy(header+68, &nTime, 4);
    memcpy(header+72, &nBits, 4);
    memcpy(header+76, &nNonce, 4);
    unsigned char result[32];
    scrypt_blockhash(header, result);
    for (int i=31;i>=0;i--) printf("%02x", result[i]);
    printf("\n");
    return 0;
}
#endif
