#include <iostream>
#include <string>
#include <stdlib.h>

// This program can be compiled with make and gcc

int main(){
    // Demonstration of integrating python command-line app into C++
    // program.

    std::cout << "Demonstrating C++ wrapper" << std::endl;

    std::string app_directory = "/home/spruce/repos/bugtracker/apps/";
    std::string chdir_command = "cd " + app_directory;
    std::string sample_calib = "~/miniconda3/envs/bugtracker/bin/python calib.py 201806121500 xam";
    std::string full_command = chdir_command + "; " + sample_calib;

    const char * full_cmd = full_command.c_str();

    system(full_cmd);

    return 0;
}