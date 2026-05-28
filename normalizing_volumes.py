import os
import argparse
import shutil
import logging
from pydub import AudioSegment
from moviepy import VideoFileClip

# Configure logging
logging.basicConfig(
    filename="normalization_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Normalize audio files (MP3/MP4) in a folder and subfolders."
    )
    parser.add_argument(
        "-p", "--path", help="Path to the folder containing audio files", required=True
    )
    parser.add_argument(
        "-t",
        "--target",
        type=float,
        default=-18.0,
        help="Target dBFS level (default: -18.0)",
    )
    parser.add_argument(
        "-o", "--overwrite", action="store_true", help="Overwrite existing files"
    )
    parser.add_argument(
        "-oy",
        "--overwrite-yes",
        action="store_true",
        help="Overwrite without confirmation",
    )
    return parser.parse_args()


def check_if_mp4_and_convert_it_to_mp3(filename, output_folder):
    name, ext = os.path.splitext(filename)
    path = os.path.join(output_folder, filename)

    if ext.lower() == ".mp4":
        try:
            video = VideoFileClip(path)
            audio = video.audio
            mp3_path = os.path.join(output_folder, f"{name}.mp3")
            audio.write_audiofile(mp3_path)
            video.close()
            return mp3_path
        except Exception as e:
            print(f"Error converting {filename}: {e}")
            return None
    elif ext.lower() == ".mp3":
        return path
    return None


def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    print(f"Difference in dBFS: {change_in_dBFS}")
    if abs(change_in_dBFS) < 0.5:
        # If change is negligible, do not apply gain
        print("No significant change needed.")
        return sound, sound.dBFS, False
    return sound.apply_gain(change_in_dBFS), change_in_dBFS, True


def process_and_normalize_the_file(
    filename, folder_path, target_dBFS, overwrite, overwrite_yes
):
    # Skip files that are not audio files
    if not (filename.endswith(".mp3") or filename.endswith(".mp4")):
        return

    path = check_if_mp4_and_convert_it_to_mp3(filename, folder_path)
    if not path:
        return

    try:
        sound = AudioSegment.from_file(path)
        normalized_sound, change_in_dBFS, significant_change = match_target_amplitude(
            sound, target_dBFS
        )

        # Only process if significant change was made
        if not significant_change:
            print(f"Skipping {filename} - no significant change needed.\n")
            return

        # If overwrite is enabled, use temporary folder; otherwise use final location directly
        if overwrite or overwrite_yes:
            # Create temporary folder
            temp_folder = os.path.join(folder_path, "temp_normalized")
            os.makedirs(temp_folder, exist_ok=True)

            temp_output_path = os.path.join(temp_folder, filename)

            normalized_sound.export(
                temp_output_path,
                format="mp3",
                bitrate="128k",
                parameters=["-ar", "44100"],
            )

            # If overwrite is enabled, move temp file to final location
            final_output_path = os.path.join(folder_path, "normalized_songs", filename)

            if overwrite_yes:
                shutil.move(temp_output_path, final_output_path)
                print(f"{filename} has been overwritten successfully.")
            else:
                # Ask for confirmation
                print(f"Do you want to overwrite {filename}? (y/n): ", end="")
                response = input().strip().lower()
                if response == "y":
                    shutil.move(temp_output_path, final_output_path)
                    print(f"{filename} has been overwritten successfully.")
                else:
                    print(f"Skipping {filename}")
                    os.remove(temp_output_path)
                    return
        else:
            # Copy to final location directly
            final_output_path = os.path.join(folder_path, "normalized_songs", filename)

            normalized_sound.export(
                final_output_path,
                format="mp3",
                bitrate="128k",
                parameters=["-ar", "44100"],
            )

        print(f"{filename} has been normalized by {change_in_dBFS} dBFS!")
        logging.info(f"Successfully normalized {filename}")

    except Exception as e:
        print(f"Error processing {filename}: {e}")
        logging.error(f"Failed to process {filename}: {e}")
        # Remove temp file if exists
        if overwrite or overwrite_yes:
            temp_output_path = os.path.join(folder_path, "temp_normalized", filename)
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)


def process_folder(folder_path, target_dBFS, overwrite, overwrite_yes):
    normalized_folder = os.path.join(folder_path, "normalized_songs")
    os.makedirs(normalized_folder, exist_ok=True)

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        # Skip the normalized_songs folder itself
        if filename == "normalized_songs":
            continue
        if os.path.isfile(file_path):
            if filename.endswith(".mp4"):
                file_size = os.path.getsize(file_path)
                if file_size > 1024 * 1024 * 1024:
                    print(
                        f"Warning: {filename} is larger than 1 GB. Do you want to proceed? (y/n): ",
                        end="",
                    )
                    response = input().strip().lower()
                    if response != "y":
                        print(f"Skipping {filename}")
                        continue

            process_and_normalize_the_file(
                filename, folder_path, target_dBFS, overwrite, overwrite_yes
            )
        elif os.path.isdir(file_path):
            process_folder(file_path, target_dBFS, overwrite, overwrite_yes)


def main():
    args = parse_args()
    folder_path = args.path
    target_dBFS = args.target
    overwrite = args.overwrite
    overwrite_yes = args.overwrite_yes

    if not os.path.isdir(folder_path):
        print("Error: Provided path is not a directory.")
        return

    print(
        f"Starting normalization in folder: {folder_path} with target dBFS: {target_dBFS}"
    )

    process_folder(folder_path, target_dBFS, overwrite, overwrite_yes)

    print(
        "Normalization complete. All MP4 files have been converted and all audio files have been normalized. Enjoy the music!"
    )


if __name__ == "__main__":
    main()

