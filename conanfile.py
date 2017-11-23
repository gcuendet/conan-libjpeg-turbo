#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, AutoToolsBuildEnvironment, tools
import os
import shutil


class LibJpegTurboConan(ConanFile):
    name = "libjpeg-turbo"
    version = "1.5.2"
    description = "SIMD-accelerated libjpeg-compatible JPEG codec library"
    generators = "cmake"
    url = "http://github.com/bincrafters/conan-libjpeg-turbo"
    license = "https://raw.githubusercontent.com/libjpeg-turbo/libjpeg-turbo/master/LICENSE.md"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "SSE": [True, False]}
    default_options = "shared=False", "fPIC=True", "SSE=True"
    exports_sources = ["CMakeLists.txt", "LICENSE"]
    install = "libjpeg-turbo-install"
    
    def config(self):
        del self.settings.compiler.libcxx 
        
        if self.settings.os == "Windows":
            self.requires.add("nasm/2.13.01@conan/stable", private=True)
            self.options.remove("fPIC")
       
    def source(self):
        download_url_base = "http://downloads.sourceforge.net/project/libjpeg-turbo"
        archive_prefix = "/" + self.version + "/"
        archive_name = self.name + "-" + self.version
        archive_ext = ".tar.gz"
        download_url = download_url_base + archive_prefix + archive_name + archive_ext
        self.output.info("trying download of url: " + download_url)
        tools.get(download_url)
        os.rename(archive_name, "sources")
        shutil.move(os.path.join("sources", "CMakeLists.txt"),
                    os.path.join("sources", "CMakeLists_original.txt"))
        shutil.move("CMakeLists.txt",
                    os.path.join("sources", "CMakeLists.txt"))

    def build_configure(self):
        prefix = os.path.abspath(self.install)
        with tools.chdir("sources"):
            env_build = AutoToolsBuildEnvironment(self)
            env_build.fpic = self.options.fPIC
            args = ['--prefix=%s' % prefix]
            if self.options.shared:
                args.extend(['--disable-static', '--enable-shared'])
            else:
                args.extend(['--disable-shared', '--enable-static'])

            if self.settings.os == "Macos":
                old_str = r'-install_name \$rpath/\$soname'
                new_str = r'-install_name \$soname'
                tools.replace_in_file("configure", old_str, new_str)

            env_build.configure(args=args)
            env_build.make()
            env_build.make(args=['install'])

    def build_windows(self):
        cmake = CMake(self)
        cmake.definitions['ENABLE_STATIC'] = not self.options.shared
        cmake.definitions['ENABLE_SHARED'] = self.options.shared
        cmake.definitions['WITH_SIMD'] = self.options.SSE
        cmake.configure(source_dir="sources")
        cmake.build()

    def build(self):
        if self.settings.os == "Windows":
            self.build_windows()
        else:
            self.build_configure()

    def package(self):
        # Copying headers
        if self.settings.os == "Windows":
            self.copy("jconfig.h", dst="include", src=".")
            if self.options.shared:
                self.copy(pattern="*jpeg.lib", dst="lib", src="lib", keep_path=False)
                self.copy(pattern="*turbojpeg.lib", dst="lib", src="lib", keep_path=False)
            else:
                self.copy(pattern="*jpeg-static.lib", dst="lib", src="lib", keep_path=False)
                self.copy(pattern="*turbojpeg-static.lib", dst="lib", src="lib", keep_path=False)
        self.copy("*.h", dst="include", src="sources")
        self.copy(pattern="*.dll", dst="bin", src="sources", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", src="sources", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", src="sources", keep_path=False)
        self.copy(pattern="*.a", dst="lib", src="sources", keep_path=False)

    def package_info(self):
        if self.settings.os == "Windows":
            if self.options.shared:
                self.cpp_info.libs = ['jpeg', 'turbojpeg']
            else:
                self.cpp_info.libs = ['jpeg-static', 'turbojpeg-static']
        else:
            self.cpp_info.libs = ['jpeg', 'turbojpeg']
