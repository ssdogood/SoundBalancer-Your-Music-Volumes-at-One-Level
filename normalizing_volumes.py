import os
import argparse
from pydub import AudioSegment
from moviepy.editor import VideoFileClip

def parse_args():
    parser = argparse.ArgumentParser(description="Normalize audio files (MP3/MP4) in a folder and subfolders.")
    parser.add_argument('-p', '--path', help='Path to the folder containing audio files', required=True)
    parser.add_argument('-t', '--target', type=float, default=-18.0, help='Target dBFS level (default: -18.0)')
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
    return sound.apply_gain(change_in_dBFS), change_in_dBFS

def process_and_normalize_the_file(filename, folder_path, target_dBFS):
    if filename.endswith(".mp3") or filename.endswith(".mp4"):
        path = check_if_mp4_and_convert_it_to_mp3(filename, folder_path)
        if not path:
            return

        try:
            sound = AudioSegment.from_file(path)
            normalized_sound, change_in_dBFS = match_target_amplitude(sound, target_dBFS)
            output_path = os.path.join(folder_path, "normalized_songs", filename)
            normalized_sound.export(output_path, format="mp3", bitrate="128k", parameters=["-ar", "44100"])
            print(f"{filename} has been normalized by {change_in_dBFS} dBFS!")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

def process_folder(folder_path, target_dBFS):
    normalized_folder = os.path.join(folder_path, "normalized_songs")
    os.makedirs(normalized_folder, exist_ok=True)

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            if filename.endswith(".mp4"):
                file_size = os.path.getsize(file_path)
                if file_size > 1024 * 1024 * 1024:  # 1 GB
                    print(f"Warning: {filename} is larger than 1 GB. Do you want to proceed? (y/n): ", end='')
                    response = input().strip().lower()
                    if response != 'y':
                        print(f"Skipping {filename}")
                        continue
            process_and_normalize_the_file(filename, folder_path, target_dBFS)
        elif os.path.isdir(file_path):
            process_folder(file_path, target_dBFS)

def main():
    args = parse_args()
    folder_path = args.path
    target_dBFS = args.target

    if not os.path.isdir(folder_path):
        print("Error: Provided path is not a directory.")
        return

    print(f"Starting normalization in folder: {folder_path} with target dBFS: {target_dBFS}")
    process_folder(folder_path, target_dBFS)
    print("Normalization complete. All MP4 files have been converted and all audio files have been normalized. Enjoy the music!")

if __name__ == "__main__":
    main()