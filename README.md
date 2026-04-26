# README.md

`simpleGals` is trying to be a very simple command-line driven static HTML image
gallery generating tool. simpleGals just like to have fun, it doesn't want you
getting bogged down with all the tedious overhead associated with fancy gals,
running software that has to get patched, or paying another subscription.
simpleGals ain't like that.

simpleGals isn't for album management. You feed simpleGals directories of images
and in return you get some simple HTML files with thumbnails.


# Tech Stack

- [Python](https://www.python.org/) >= 3.10
- [term-image](git+https://github.com/AnonymouX47/term-image.git)
- A terminal emulator with **any** of the following:

  - support for the [Kitty graphics protocol](https://sw.kovidgoyal.net/kitty/graphics-protocol/)
  - support for the [iTerm2 inline image protocol](https://iterm2.com/documentation-images.html)
  - Unicode and direct-color (truecolor) support
- My [bitmath](git+https://github.com/timlnx/bitmath.git) library for file size printing and math

(I told you, it's simple)


# Experience

The fanciest part of simpleGals is the tui setup utility. Launching `sgui` opens
the application in the current working directory, `sgui` (and the batch-mode
`simpleGals` interface) will create a directory called `out` and expects to find
a directory called `in`, these directories will be created if they do not
already exist. Image metadata and caching files are saved in a `.meta`
directory.

A basic template ships with simpleGals. Your can fork this template and instruct
simpleGals to use your template instead with the `--template,-t <TEMPLATE_DIR>`
option flag, or in the setup panel of `sgui`.


# `sgui`

The sgui launches with a scrollable file tree ('file panel') of discovered
images in the `in` directory listed on the left, just the file names, about 20%
of the screen up to a max width of ~=30 characters

* setting: `file_panel_width`
* desc: width in characters or percent of horizontal area
* types:
    - `int` for absolute character value (e.g., `30` = 30 characters)
    - `int%` for max width percent (e.g., `30%` = 30% of horizontal space)
* default: `30`

Move the selection cursor with with the up/down arrow keys, pausing or stopping
on a file name will marquee scroll the file name if it was truncated. The ctrl+n
and ctrl+p shortcuts also work for next and previous if you are in the file panel.

* setting: `scroll_rate`
* desc: scroll rate in chars/second
* type: `float`
* default: `2.0`

On the right using the remainder of the visible space is the general gallery
settings input panel. This panel is also where previewing and editing properties
of individual images takes place.

Pressing escape at any time shifts focus to the general gallery settings where
parameters like max columns/rows/per page/description information can be
provided. Press escape again to go back to the selection mode.

When moving the selection cursor between images in the file panel there is a
brief delay before the thumbnail is loaded the first time so you can page
through several in a row without attempting to generate thumbnails of each image
rapidly. Once a thumbnail is generated the delay is `0` if the last-modified
metadata has not changed for the input/thumbnail files

* setting: `preview_delay`
* description: delay before generating image metadata thumbnail the first time
* type: `int`
* default: `75ms`

Image thumbnails are displayed in the console using the `term-image` library. A
preview will take up no more than 55% of the available horizontal/vertical space
on the panel on the right.

Pressing tab switches cursor focus between the file panel and the main usage window.

# Settings

Settings are saved in JSON format.

Gallery metadata in the `.meta` directory includes a `cache/` directory with thumbnail images for the sgui browser. The file names are simply mapped back to the source images based on sha checksum (TODO: OR SOME OTHER FAST AND RELIABLE SIGNATURE METHOD). A simple YAML file records source image names (relative to the `in/` directory) and original image checksums, modification times, and preview generation times.





# Reference Material

* base library: https://github.com/AnonymouX47/term-image
* example usage: https://github.com/AnonymouX47/termvisage 
