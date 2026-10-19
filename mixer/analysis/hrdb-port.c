/* Keep this profiling session off the shared HRDB port used by other tasks.
 * DYLD interposition affects only the emulator process launched by profile.py.
 * The emulator binary and other running instances are untouched.
 */
#include <sys/socket.h>
#include <netinet/in.h>
#include <string.h>
static int amixer_profile_bind(int fd,const struct sockaddr *addr,socklen_t size)
{
    if(size>=sizeof(struct sockaddr_in) && addr->sa_family==AF_INET){
        struct sockaddr_in local;
        memcpy(&local,addr,sizeof(local));
        if(ntohs(local.sin_port)==56001){
            local.sin_port=htons(56129);
            return bind(fd,(const struct sockaddr*)&local,sizeof(local));
        }
    }
    return bind(fd,addr,size);
}
__attribute__((used)) static const struct {const void *replacement;const void *original;}
amixer_profile_interpose __attribute__((section("__DATA,__interpose")))={
    (const void*)amixer_profile_bind,(const void*)bind
};
