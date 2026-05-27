# SoundBalancer-Your-Music-Volumes-at-One-Level

This original program was written by Pedram Porbaha and his repo is pporbaha/SoundBalancer-Your-Music-Volumes-at-One-Level. This is a fork from that repo. 
## Overview
This Python utility addresses the common issue of varying audio levels in music collections. It normalizes the volume of MP3 and MP4 files to a consistent level, making it ideal for listeners who wish to enjoy their music without the need to manually adjust the volume for each track.

## Features
- **Automatic Volume Normalization**: Set a target decibel level for all your audio files.
- **MP4 to MP3 Conversion**: Seamlessly converts MP4 files to MP3 format during the normalization process.
- **Batch Processing**: Processes an entire folder of audio files in one go.

## Prerequisites
Before running this script, ensure you have the following dependencies installed:
- `pydub`
- `moviepy`
- `argparse`
- `shutil`

Additionally, you'll need FFmpeg installed on your system. It is recommended to install full rather than minimal.
## Usage
`$ python normalizing_volumes.py -p "<path of source directory>"`

For help you can type:
`$ python normalizing_volumes.py -h`

The script will create a subfolder named `normalized_songs` within your source folder, where it will place all the normalized audio files.

## Contributions
Contributions are welcome! If you'd like to improve the script or add new features, please feel free to fork the repository and submit a pull request.

## License
This project is open-sourced under the MIT License. See the LICENSE file for more details.

