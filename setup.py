from setuptools import find_packages, setup

with open("README.rst") as f:
    README = f.read()

pkgs = find_packages()
pkgs.append('nitrolib.resources')

if __name__ == "__main__":
    setup(
        name="nitrolib",
        author="martmists",
        author_email="mail@martmists.com",
        license="MIT",
        zip_safe=False,
        version="0.0.2",
        description="NitroLib is a library for working wih the various systems "
                    "developed by Intelligent Systems for the Nitro consoles.",
        long_description=README,
        url="https://github.com/NintendoDevTools/nitrolib",
        packages=pkgs,
        install_requires=["pyusb"],
        entry_points={
            # TODO: Proper CLI interface
            "console_scripts": ["nitro = nitrolib.__main__:main"]
        },
        keywords=[],
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: System :: Hardware :: Hardware Drivers",
        ],
        package_data={
            "nitrolib.resources": ["*.bin"]
        },
        include_package_data=True,
    )
