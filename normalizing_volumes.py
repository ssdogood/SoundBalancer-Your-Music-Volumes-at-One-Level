import os
import argparse
import shutil
import logging
from datetime import datetime
from tabulate import tabulate
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


def check_if_mp4_and_convert_it_to_mp3(file_path):
    name, ext = os.path.splitext(file_path)

    if ext.lower() == ".mp4":
        try:
            video = VideoFileClip(file_path)
            audio = video.audio
            mp3_path = f"{name}.mp3"
            audio.write_audiofile(mp3_path)
            video.close()
            return mp3_path
        except Exception as e:
            print(f"Error converting {os.path.basename(file_path)}: {e}")
            return None
    elif ext.lower() == ".mp3":
        return file_path
    return None


def get_file_size_mb(file_path):
    """Get file size in MB."""
    size_bytes = os.path.getsize(file_path)
    return round(size_bytes / (1024 * 1024), 2)


def get_last_modified_datetime(file_path):
    """Get last modified date and time of file."""
    timestamp = os.path.getmtime(file_path)
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def get_audio_dbfs(file_path):
    """Get the current dBFS level of an audio file."""
    if not (file_path.endswith(".mp3") or file_path.endswith(".mp4")):
        return None

    path = check_if_mp4_and_convert_it_to_mp3(file_path)

    if not path:
        return None

    try:
        sound = AudioSegment.from_file(path)
        return sound.dBFS
    except Exception as e:
        print(f"Error reading {os.path.basename(file_path)}: {e}")
        return None


def get_already_normalized_files(folder_path):
    """Get set of already normalized files with normalized path separators."""
    normalized_folder = os.path.join(folder_path, "normalized")

    print(f"DEBUG: Looking for normalized folder at: {normalized_folder}")
    print(f"DEBUG: Folder exists: {os.path.isdir(normalized_folder)}")

    if not os.path.isdir(normalized_folder):
        print("DEBUG: Normalized folder not found.")
        return set()

    normalized_files = set()
    try:
        for root, dirs, files in os.walk(normalized_folder):
            for filename in files:
                full_path = os.path.join(root, filename)
                # Get relative path from normalized folder and normalize separators
                relative_path = os.path.relpath(full_path, normalized_folder)
                # Normalize path separators to forward slashes for consistent comparison
                normalized_path = relative_path.replace(os.sep, "/")
                normalized_files.add(normalized_path)
                print(f"DEBUG: Found normalized file: {normalized_path}")
    except Exception as e:
        logging.error(f"Error reading normalized folder: {e}")

    print(f"DEBUG: Total normalized files found: {len(normalized_files)}")
    return normalized_files


def get_already_normalized_files_in_folder(folder_path):
    """Get set of already normalized files in the normalized folder within the given folder."""
    normalized_folder = os.path.join(folder_path, "normalized")

    if not os.path.isdir(normalized_folder):
        return set()

    normalized_files = set()
    try:
        for filename in os.listdir(normalized_folder):
            file_path = os.path.join(normalized_folder, filename)
            if os.path.isfile(file_path):
                normalized_files.add(filename)
    except Exception as e:
        logging.error(f"Error reading normalized folder in {folder_path}: {e}")

    return normalized_files


def analyze_files(folder_path, target_dBFS):
    """Analyze all audio files and compare with target dBFS."""
    files_analysis = []

    # Get already normalized files in THIS folder
    already_normalized_here = get_already_normalized_files_in_folder(folder_path)

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Skip the normalized folder itself
        if filename == "normalized":
            continue

        if os.path.isfile(file_path):
            current_dbfs = get_audio_dbfs(file_path)

            if current_dbfs is not None:
                difference = target_dBFS - current_dbfs
                needs_change = abs(difference) >= 0.5
                file_size = get_file_size_mb(file_path)
                last_modified = get_last_modified_datetime(file_path)

                # Check if this file is already normalized in this folder's normalized directory
                is_already_normalized = filename in already_normalized_here

                files_analysis.append(
                    {
                        "file_path": file_path,
                        "filename": filename,
                        "size_mb": file_size,
                        "last_modified": last_modified,
                        "current_dbfs": round(current_dbfs, 2),
                        "target_dbfs": target_dBFS,
                        "difference": round(difference, 2),
                        "needs_change": "Yes" if needs_change else "No",
                        "already_normalized": is_already_normalized,
                    }
                )

        elif os.path.isdir(file_path):
            # Recursively analyze subfolders - each subfolder will check its own normalized folder
            files_analysis.extend(analyze_files(file_path, target_dBFS))

    return files_analysis


def display_analysis_table(files_analysis):
    """Display file analysis results in tabular format."""
    if not files_analysis:
        print("No audio files found in the folder.")
        return

    table_data = [
        [
            f["filename"],
            f["size_mb"],
            f["last_modified"],
            f["current_dbfs"],
            f["target_dbfs"],
            f["difference"],
            f["needs_change"],
        ]
        for f in files_analysis
    ]

    headers = [
        "Filename",
        "Size (MB)",
        "Last Modified",
        "Current dBFS",
        "Target dBFS",
        "Difference",
        "Needs Change",
    ]
    print("\n" + "=" * 140)
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print("=" * 140 + "\n")


def log_analysis_table(files_analysis, target_dBFS):
    """Log file analysis results to log file."""
    logging.info("-" * 160)
    logging.info("FILE ANALYSIS REPORT - Target dBFS: %s", target_dBFS)
    logging.info("-" * 160)

    if not files_analysis:
        logging.info("No audio files found in the folder.")
        return

    for f in files_analysis:
        logging.info(
            "File: %s | Size: %s MB | Last Modified: %s | "
            "Current dBFS: %s | Target dBFS: %s | Difference: %s | "
            "Needs Change: %s | Already Normalized: %s",
            f["filename"],
            f["size_mb"],
            f["last_modified"],
            f["current_dbfs"],
            f["target_dbfs"],
            f["difference"],
            f["needs_change"],
            f["already_normalized"],
        )

    logging.info("-" * 160)


def get_files_to_process(files_analysis):
    """Filter files that need processing (new files that need normalization)."""
    return [
        f
        for f in files_analysis
        if f["needs_change"] == "Yes" and not f["already_normalized"]
    ]


def get_already_processed_files(files_analysis):
    """Get files that are already normalized."""
    return [f for f in files_analysis if f["already_normalized"]]


def report_processed_files(already_processed):
    """Inform user about already converted files."""
    if not already_processed:
        return

    print("\n" + "=" * 80)
    print("✓ ALREADY NORMALIZED FILES (Skipped)")
    print("=" * 80)
    for f in already_processed:
        print(f"  • {f['filename']}")
    print("=" * 80 + "\n")
    logging.info(f"{len(already_processed)} file(s) already normalized and skipped.")


def count_files_needing_change(files_analysis):
    """Count how many files need normalization."""
    return sum(1 for f in files_analysis if f["needs_change"] == "Yes")


def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    print(f"Difference in dBFS: {change_in_dBFS}")

    if abs(change_in_dBFS) < 0.5:
        # If change is negligible, do not apply gain
        print("No significant change needed.")
        return sound, sound.dBFS, False

    return sound.apply_gain(change_in_dBFS), change_in_dBFS, True


def process_and_normalize_the_file(file_path, target_dBFS, overwrite, overwrite_yes):
    """Process and normalize a single file. Returns True if successfully normalized, False otherwise."""
    # Skip files that are not audio files
    if not (file_path.endswith(".mp3") or file_path.endswith(".mp4")):
        return False

    path = check_if_mp4_and_convert_it_to_mp3(file_path)

    if not path:
        return False

    try:
        sound = AudioSegment.from_file(path)
        normalized_sound, change_in_dBFS, significant_change = match_target_amplitude(
            sound, target_dBFS
        )

        # Only process if significant change was made
        if not significant_change:
            print(
                f"Skipping {os.path.basename(file_path)} - no significant change needed.\n"
            )
            return False

        # Get the directory where the original file is
        file_dir = os.path.dirname(file_path)
        filename = os.path.basename(file_path)

        # If overwrite is enabled, use temporary folder; otherwise use final location directly
        if overwrite or overwrite_yes:
            # Create temporary folder in the same directory as the file
            temp_folder = os.path.join(file_dir, "temp_normalized")
            os.makedirs(temp_folder, exist_ok=True)

            temp_output_path = os.path.join(temp_folder, filename)

            normalized_sound.export(
                temp_output_path,
                format="mp3",
                bitrate="128k",
                parameters=["-ar", "44100"],
            )

            # If overwrite is enabled, move temp file to final location
            normalized_folder = os.path.join(file_dir, "normalized")
            os.makedirs(normalized_folder, exist_ok=True)
            final_output_path = os.path.join(normalized_folder, filename)

            if overwrite_yes:
                shutil.move(temp_output_path, final_output_path)
                print(f"{filename} has been overwritten successfully.")
                logging.info(
                    f"Successfully normalized and overwrote {filename} by {change_in_dBFS} dBFS"
                )
                return True
            else:
                # Ask for confirmation
                print(f"Do you want to overwrite {filename}? (y/n): ", end="")
                response = input().strip().lower()

                if response == "y":
                    shutil.move(temp_output_path, final_output_path)
                    print(f"{filename} has been overwritten successfully.")
                    logging.info(
                        f"Successfully normalized and overwrote {filename} by {change_in_dBFS} dBFS"
                    )
                    return True
                else:
                    print(f"Skipping {filename}")
                    logging.info(f"User skipped {filename}")
                    os.remove(temp_output_path)
                    return False
        else:
            # Copy to final location directly
            normalized_folder = os.path.join(file_dir, "normalized")
            os.makedirs(normalized_folder, exist_ok=True)
            final_output_path = os.path.join(normalized_folder, filename)

            normalized_sound.export(
                final_output_path,
                format="mp3",
                bitrate="128k",
                parameters=["-ar", "44100"],
            )

            print(f"{filename} has been normalized by {change_in_dBFS} dBFS!")
            logging.info(f"Successfully normalized {filename} by {change_in_dBFS} dBFS")
            return True

    except Exception as e:
        print(f"Error processing {os.path.basename(file_path)}: {e}")
        logging.error(f"Failed to process {os.path.basename(file_path)}: {e}")

        # Remove temp file if exists
        if overwrite or overwrite_yes:
            file_dir = os.path.dirname(file_path)
            temp_output_path = os.path.join(
                file_dir, "temp_normalized", os.path.basename(file_path)
            )

            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)

        return False


def clean_empty_temp_folders(folder_path):
    """Remove empty temp_normalized folders."""
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if os.path.isdir(file_path):
            # Recursively clean subfolders
            clean_empty_temp_folders(file_path)

            # Remove empty temp_normalized folder
            if filename == "temp_normalized" and not os.listdir(file_path):
                try:
                    os.rmdir(file_path)
                except Exception as e:
                    logging.error(f"Failed to remove empty temp folder: {e}")


def process_files(files_to_process, folder_path, target_dBFS, overwrite, overwrite_yes):
    """Process only files that need normalization."""
    normalized_count = 0

    for file_info in files_to_process:
        if process_and_normalize_the_file(
            file_info["file_path"], target_dBFS, overwrite, overwrite_yes
        ):
            normalized_count += 1

    # Clean up empty temp folders
    clean_empty_temp_folders(folder_path)

    return normalized_count


def main():
    args = parse_args()
    folder_path = args.path
    target_dBFS = args.target
    overwrite = args.overwrite
    overwrite_yes = args.overwrite_yes

    # Convert to absolute path to handle relative paths correctly
    folder_path = os.path.abspath(folder_path)

    if not os.path.isdir(folder_path):
        print("Error: Provided path is not a directory.")
        logging.error("Error: Provided path is not a directory: %s", folder_path)
        return

    print(
        f"Starting analysis in folder: {folder_path} with target dBFS: {target_dBFS}\n"
    )
    logging.info(
        "Starting analysis in folder: %s with target dBFS: %s",
        folder_path,
        target_dBFS,
    )

    # Analyze all files (each folder will check its own normalized directory)
    files_analysis = analyze_files(folder_path, target_dBFS)

    # Display analysis in table format
    display_analysis_table(files_analysis)

    # Log analysis results to file
    log_analysis_table(files_analysis, target_dBFS)

    # Get already processed files and report
    already_processed = get_already_processed_files(files_analysis)
    report_processed_files(already_processed)

    # Get files to process (new files that need normalization)
    files_to_process = get_files_to_process(files_analysis)

    if not files_to_process:
        print("✓ No new files need normalization.")
        logging.info("No new files need normalization.")
        return

    # Process the new files
    print(
        f"\nProcessing {len(files_to_process)} new file(s) that need normalization...\n"
    )
    logging.info(
        f"Processing {len(files_to_process)} new file(s) that need normalization."
    )

    normalized_count = process_files(
        files_to_process, folder_path, target_dBFS, overwrite, overwrite_yes
    )

    # Final summary
    print("\n" + "=" * 80)
    print("✓ NORMALIZATION COMPLETE")
    print("=" * 80)
    print(f"  • Already normalized files: {len(already_processed)}")
    print(f"  • Newly normalized files: {normalized_count}")
    print(f"  • Total processed: {len(already_processed) + normalized_count}")
    print("=" * 80 + "\n")

    logging.info(
        f"Normalization complete. Already normalized: {len(already_processed)}, "
        f"Newly normalized: {normalized_count}, Total: {len(already_processed) + normalized_count}"
    )


if __name__ == "__main__":
    main()

