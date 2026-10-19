/* Test-only SDL input, local to the Hatari child. Does not patch Atari RAM. */
#include <SDL.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
static void *input(void *unused)
{
    const char *path = getenv("FSEL_INPUT_PIPE");
    FILE *f;
    char cmd;
    int x, y;
    (void)unused;
    if (!path || !(f = fopen(path, "r+"))) return 0;
    while (fscanf(f, " %c %d %d", &cmd, &x, &y) == 3)
    {
        SDL_Event e = {0};
        if (cmd == 'm') {
            e.type = SDL_MOUSEMOTION; e.motion.xrel = x; e.motion.yrel = y;
        } else {
            e.type = x ? SDL_MOUSEBUTTONDOWN : SDL_MOUSEBUTTONUP;
            e.button.button = SDL_BUTTON_LEFT;
            e.button.state = x ? SDL_PRESSED : SDL_RELEASED;
        }
        SDL_PushEvent(&e);
    }
    fclose(f);
    return 0;
}
__attribute__((constructor)) static void init(void)
{
    pthread_t thread;
    pthread_create(&thread, 0, input, 0);
    pthread_detach(thread);
}
