import argparse
import os
import re
import sys
from tqdm import tqdm

# Function to sanitize filenames by removing forbidden characters and extra spaces
def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip().replace(' ', '_')

# Define command-line arguments
parser = argparse.ArgumentParser("iptv_filtering_script")
parser.add_argument("--m3u", help="Path to a local M3U file.", type=str, required=True)
parser.add_argument("--output", help="Output directory.", type=str, required=True)
parser.add_argument("--regex", help="Regex pattern to filter groups. Case insensitive.", type=str)
parser.add_argument("--concat", help="Concatenate all group playlists into one file.", action="store_true")
args = parser.parse_args()

m3u_file = args.m3u
output_folder = args.output
groups_regex = args.regex if args.regex else "."

group_titles = []

# Check if the M3U file exists
if os.path.isfile(m3u_file):
    with open(m3u_file, "r", encoding="utf-8") as f:  # Force UTF-8 encoding to handle special characters
        content = f.readlines()
        if content[0].strip("\n") == "#EXTM3U":
            content.pop(0)  # Remove the first line containing "#EXTM3U"

            # Extract unique group names from the M3U file
            for line in content:
                if 'group-title="' in line:
                    group_titles.append(line.split('group-title="')[-1].split('"')[0])
            group_titles = sorted(set(group_titles))  # Remove duplicates and sort the list

            # Apply regex filtering if specified
            pattern = re.compile(groups_regex, re.IGNORECASE)
            group_titles = [group for group in group_titles if pattern.search(group)]

            # Merge EXT info with media link into a single line
            concatenated_content = [content[i].strip() + ' stream_link=' + content[i+1].strip()
                                    for i in range(0, len(content)-1, 2)]

            # If --concat option is provided, create a single playlist containing all groups
            if args.concat:
                os.makedirs(output_folder, exist_ok=True) 
                concat_file = f"{output_folder}/combined_playlist.m3u"
                with open(concat_file, "w+", encoding="utf-8") as f:
                    f.writelines("#EXTM3U\n")  # Write header only once

                    filtered_content = [line for line in concatenated_content if any(group in line for group in group_titles)]

                    # Show progress using tqdm
                    with tqdm(total=len(filtered_content), desc=f"Creating {concat_file}", unit=" line") as pbar:
                        for line in filtered_content:
                            f.writelines(f'{line.split(" stream_link=")[0]}\n')
                            f.writelines(f'{line.split(" stream_link=")[-1]}\n')
                            pbar.update(1)

            # Otherwise, create separate files for each group
            else:
                for group in group_titles:
                    safe_group = sanitize_filename(group)  # Ensure valid directory name
                    os.makedirs(f"{output_folder}/{safe_group}", exist_ok=True)

                    filtered_content = [line for line in concatenated_content if group in line]
                    total_lines = len(filtered_content)

                    if total_lines > 0:
                        with open(f"{output_folder}/{safe_group}/channels.m3u", "w+", encoding="utf-8") as f:
                            f.writelines("#EXTM3U\n")  # Write header for each file

                            # Show progress using tqdm
                            with tqdm(total=total_lines, desc=f"Creating {output_folder}/{safe_group}/channels.m3u", unit=" line") as pbar:
                                for line in filtered_content:
                                    f.writelines(f'{line.split(" stream_link=")[0]}\n')
                                    f.writelines(f'{line.split(" stream_link=")[-1]}\n')
                                    pbar.update(1)

        else:
            print(f"⚠️ File {m3u_file} is an invalid M3U file.")
            sys.exit(-1)
else:
    print(f"⚠️ File {m3u_file} does not exist.")
    sys.exit(-1)
