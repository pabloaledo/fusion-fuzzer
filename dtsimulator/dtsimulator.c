#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_LINE_LENGTH 1024

void execute_command(char* command) {
    printf("Executing command: %s\n", command);
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
        if (timestamp_ms == 0) {
            printf("Error: invalid timestamp\n");
            continue;
        }

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
