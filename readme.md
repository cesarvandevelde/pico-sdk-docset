# Dash docset for Raspberry Pi Pico SDK

This repository contains the necessary files to generate a [Dash][1] docset for
the [Raspberry Pi Pico SDK][2]. The original Doxygen files from the Pico SDK
repository were modified to make the output more suitable for viewing in Dash.


## Generating the docset

To generate the docset, you will need `python3`, `doxygen`, and `docsetutil`.
These utilities can be installed via [Homebrew][3], if necessary. The build
script does not require any extra modules outside of Python standard library.
To build, clone the repository and run the following commands:

```
git submodule init --update
python3 make_docset.py
```


[1]: https://kapeli.com/dash
[2]: https://github.com/raspberrypi/pico-sdk
[3]: https://brew.sh
