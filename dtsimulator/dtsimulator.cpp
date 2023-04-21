#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <fcntl.h>
#include <unistd.h>

#include <sys/stat.h>
#include <utime.h>

#define MAX_LINE_LENGTH 1024

int file_descriptor[100];

void execute_command(char* command) {
    printf("Executing command: %s\n", command);
    int operation, transaction;
    sscanf(command, "%d%d", &operation, &transaction);

    switch (operation) {
        case 1:
            printf("open %d\n", transaction);

            file_descriptor[transaction] = open("file.txt", O_RDWR | O_CREAT, 0666);

            break;
        
        case 2:
            printf("write %d\n", transaction);

            char data[100];
            write(file_descriptor[transaction], data, 100);

            break;

        case 3:
            printf("close %d\n", transaction);

            close(file_descriptor[transaction]);

            break;

        case 4:
            printf("delete %d\n", transaction);

            remove("file.txt");

            break;
        
        case 5:
            printf("read %d\n", transaction);

            char data2[100];
            read(file_descriptor[transaction], data2, 100);

            break;

        case 6:
            printf("seek %d\n", transaction);

            lseek(file_descriptor[transaction], 0, SEEK_SET);

            break;
        
        case 7:
            printf("truncate %d\n", transaction);

            ftruncate(file_descriptor[transaction], 0);

            break;
        
        case 8:
            printf("sync %d\n", transaction);

            fsync(file_descriptor[transaction]);

            break;


        case 9:
            printf("rename %d\n", transaction);

            rename("file.txt", "file2.txt");

            break;

        case 10:
            printf("link %d\n", transaction);

            link("file.txt", "file2.txt");

            break;

        case 11:
            printf("unlink %d\n", transaction);

            unlink("file2.txt");

            break;

        case 12:
            printf("mkdir %d\n", transaction);

            mkdir("dir", 0777);

            break;

        case 13:
            printf("rmdir %d\n", transaction);

            rmdir("dir");

            break;

        case 14:
            printf("chdir %d\n", transaction);

            chdir("dir");

            break;

        case 15:
            printf("chmod %d\n", transaction);

            chmod("file.txt", 0777);

            break;

        case 16:
            printf("chown %d\n", transaction);

            chown("file.txt", 1000, 1000);

            break;
        
        case 17:
            printf("utime %d\n", transaction);

            struct utimbuf time;
            time.actime = 1000;
            time.modtime = 1000;
            utime("file.txt", &time);

            break;
        
        case 18:
            printf("stat %d\n", transaction);

            struct stat buf;
            stat("file.txt", &buf);

            break;

        case 19:
            printf("lstat %d\n", transaction);

            struct stat buf2;
            lstat("file.txt", &buf2);

            break;

        case 20:
            printf("access %d\n", transaction);

            access("file.txt", F_OK);

            break;
        case 21:
            printf("dup %d\n", transaction);

            dup(file_descriptor[transaction]);

            break;

        case 22:
            printf("dup2 %d\n", transaction);

            dup2(file_descriptor[transaction], 0);

            break;


    }
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        printf("Usage: %s input_file\n", argv[0]);
        return 1;
    }

    FILE* input_file = fopen(argv[1], "r");
    if (input_file == NULL) {
        printf("Error: could not open input file %s\n", argv[1]);
        return 1;
    }

    char line[MAX_LINE_LENGTH];

    time_t start_time = time(0);

    while (fgets(line, MAX_LINE_LENGTH, input_file) != NULL) {
        char* timestamp_str = strtok(line, " ");
        char* command = strtok(NULL, "\n");
        if (timestamp_str == NULL || command == NULL) {
            printf("Error: invalid input line\n");
            continue;
        }
        long long timestamp_ms = strtoll(timestamp_str, NULL, 10);

        time_t current_time = time(0);
        long elapsed_time = difftime(current_time, start_time) * 1000;
        long ms_to_wait = timestamp_ms - elapsed_time;

        if (ms_to_wait > 0) {
            printf("Waiting for %ld milliseconds...\n", ms_to_wait);
            usleep((unsigned int)(ms_to_wait * 1000));
        }
        execute_command(command);
    }

    fclose(input_file);
    return 0;
}
