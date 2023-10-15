##
## Instastista v0.1 
#-----------------------------------------------------
## Scrape all of multiple Instagram users' photos 
## or scrape any webpage for Instagram usernames
#-----------------------------------------------------
 

# For the GUI 
import tkinter as tk
# For the GUI theme
import customtkinter as ctk
# For interacting with Instagram
import instaloader
# For requesting webpages
import requests
# For searching for specific strings within text
from bs4 import BeautifulSoup
# Regular expressions for specifying string patterns to look for
import re
# For creating and interacting with JSON files
import json
# For splitting the tasks into different processing threads
import threading
# For pausing the program
import time
# For checking if a file exists in the OS filesystem
import os


# Create settings file 
def load_settings():
    global settings_file, default_settings, settings
    # The settings JSON filename
    settings_filename = "settings.json"         
    # The default settings values to be restored
    default_settings = {   
        "theme": "clam", # The GUI theme style name 
        "font_size": 12, # The GUI font-size
         "overwrite_username_file": True , # Option to overwrite username file      
         "quiet_instaloader" : False,
         "user_agent": None,
         "dirname_pattern": None,
         "filename_pattern": None,
         "download_pictures": True,
         "download_videos": False,
         "download_geotags":False,
         "download_comments": False,
         "save_metadata": False,
         "compress_json": False,
         }   
    # Try to open GUI settings file otherwise load default settings if file not found
    try:
        with open(settings_filename, "r") as file:
            settings = json.load(file)
    except FileNotFoundError:
        settings = default_settings

load_settings()

# Create themed GUI window
def create_gui():    
    global app, style, font_size, automation_running
    # Define the GUI window
    ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
    ctk.set_default_color_theme("blue")
    app = ctk.CTk()
    app.title("Instasista v0.5")
    app.geometry("600x300")
    # Set the GUI font size as variable
    font_size = settings["font_size"]   
    # Variable to keep track of the automation status
    automation_running = False

create_gui()

# Create Instaloader
ig = instaloader.Instaloader(
    # Sleep for a small bit of time when calling the library
    sleep=True,
    # Output InstaLoader logs to console
    quiet=False,
    # String that InstaLoader will use when interacting with python
    user_agent=None,
    # Name of the directory InstaLoader will use in it's interactions
    dirname_pattern=None,
    # Pattern for files InstalLoader will use
    filename_pattern=None,
    # Declare what  profile elements should be do
    download_pictures=True,
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    # Compress metadara JSON files
    compress_json=False,
    # Text pattern for post metadata files
    post_metadata_txt_pattern=None,
    # Text pattern for storyitem metadata files
    storyitem_metadata_txt_pattern=None,
    # Amout of times InstaLoader will try the task
    max_connection_attempts=3,
    # The time in which a request will timeout
    request_timeout=300.0,
    # Set to control rate of InstaLoader activities
    rate_controller=None,
    # Set the resume prefix as iterator
    resume_prefix='iterator',
    # Whether to check the date of expiry of resume files and reject them if expired.
    check_resume_bbd=True,
    # Set to download only specific posts from a sidecar post
    slide=None,
    # Set if you would like factual status codes
    fatal_status_codes=None,
    # Set if you want to download the iPhone versions of the photos
    iphone_support=True,
    # Set if you want to sanitize the paths outputted by Instaloader
    sanitize_paths=True
) 

# Create a list to keep track of download status
status_log = []

def download_media(post, username):
    # The directory name: downloads/username
    dirname = instaloader.instaloader._PostPathFormatter(post).format("downloads/" + ig.dirname_pattern, target=username)
    # The fileame: downloads/username/date.file-extension
    filename = os.path.join(dirname, ig.format_filename(post, target=username))
    # If directory doesnt exist, create it
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Download the image(s) / video thumbnail and videos within sidecars if desired
    downloaded = True
    try:
        # If Instaloader download_pictures setting is true
        if ig.download_pictures:
            # If Instagram post is a sidecar post
            if post.typename == 'GraphSidecar':
                # Create counter for looping through all sidecar nodes
                sidecar_node_count = 0
                # Create another counter to get total sidecar nodes for tracking progress of downloads
                total_sidecar_nodes = 0
                # Loop through the sidecar_node to get the total length
                for sidecar_node in post.get_sidecar_nodes():
                    # Add 1 for each sidecar not      
                    total_sidecar_nodes += 1
                # Loop through every sidecar_node in the sidecar post
                for sidecar_node in post.get_sidecar_nodes():
                    # Log the progress of the sidecar post download
                    log_status(f"/n Downloading: {sidecar_node_count} of {total_sidecar_nodes}")
                    # If the sidecar node is not a video or the video_thumbnails setting is turned on
                    if not sidecar_node.is_video or ig.download_video_thumbnails is True:
                        #  Download the sidecar node photo or photo thumbnail
                        downloaded &= ig.download_pic(filename=filename, url=sidecar_node.display_url,
                                                        mtime=post.date_local, filename_suffix=str(sidecar_node_count))
                    # Additionally, if the sidecar node is a video and download_videos setting is turned on
                    if sidecar_node.is_video and ig.download_videos is True:
                        # Download the sidecar node'video if available and desired
                        downloaded &= ig.download_video(filename=filename, url=sidecar_node.video_url,
                                                        mtime=post.date_local, filename_suffix=str(sidecar_node_count))
                    # Increase the printed counter
                    sidecar_node_count += 1
            else:
                # For single-image posts, download the photo
                downloaded &= ig.download_pic(filename=filename, url=post.url, mtime=post.date_local)            
    # Catch the error if there is an error downloading the post photo/video/sidecar
    except BaseException as exp:
        # Make the download_status variable globally available
        global download_status
        # Set the exception error as download_status
        download_status = exp
        # Return the error as download_status
        log_status(download_status)
    
    
# Function to scrape all the media via the username of an Instagram profile without the metadata
def scrape_user_photos(username):    
    # Load Instagram profile of username
    profile = instaloader.Profile.from_username(ig.context, username)
    
    log_status(f"Scraping photos for user: {username}")
    # Create tasks list
    tasks = []
    # Set up the parameters for posts_download_loop
    post_iterator = profile.get_posts()
    media_amount = profile.mediacount
    # Define a takewhile function if needed
    def takewhile_condition(post):
    # Define a condition to continue downloading posts
    # For example, download posts until a certain date
        return post.date > ig.datetime(2023, 1, 1)

    # Use the resumable_iteration function to handle resumable downloads
    download_count = False
    # Optional: Iterate through the posts and perform actions on them
    for post in post_iterator:
        # Increase the download count so we can track the profile download progress
        download_count += 1
        # Log the progress of the profile download operations
        log_status( f"/n Downloading: {download_count}/{media_amount} photos for {username}")
        # Download media of the post
        download_media(post, username)
                

# Function to scrape all media of the all the Instagram usernames in the userlist
def scrape_all_user_photos(userlist):
    # Loop through each username in the list of usernames
    for username in userlist:
        # Log which user the loop is currently processing
        log_status(f"Task: Processing {username}")
        try:
            # Pass the username to the scraping function
            scrape_user_photos(username)
            # Give it a little rest between users
            time.sleep(3)
        # Catch any general exceptions
        except BaseException as exp:
            # Log the error for debugging
            log_status(exp)


# Function to sanitize the URL and create a valid filename
# Function to sanitize a URL to a valid filename
def sanitize_url_to_filename(url):
    # Remove the protocol (http/https)
    sanitized = re.sub(r'https?://', '', url)
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[/\\:*?"><|]', '_', sanitized)
    # Replace / and \ with underscores
    sanitized = sanitized.replace("/", "_").replace("\\", "_")
    # Remove newlines
    
    # Return the sanitized URL
    return sanitized

# Function to scrape webpage for usernames
def scrape_webpage_for_usernames(url):
    url = url.strip('\n')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        "Content-Type": "application/x-www-form-urlencoded"}
    # Send a request to the URL and set the response as the page variable
    page = requests.get(url,headers)
    # print(page.text)
    # Parse the text of the page with BeautifulSoup
    soup = BeautifulSoup(page.text, 'html.parser')
    # Finding all usernames that match the @username format
    usernames = re.findall(r'@([A-Za-z0-9_.]+)', soup.text)
    # Log the usernames it was able to find
    log_status(f"Found usernames: {usernames}")
    # Sanitize the URL to be used as a filename for saving the scraped usernames
    sanitized_filename = sanitize_url_to_filename(url)
    # Update the status so we know the usernames are being saved to a file
    log_status(f"Saving usernames to file ({sanitized_filename})")
    # The directory in which the scraped username files will be saved
    directory_name = 'scraped_usernames'
    # Ensure the directory exists, or create it if it doesn't
    os.makedirs(directory_name, exist_ok=True)
    # Define the file path
    file_path = os.path.join(directory_name, f"{sanitized_filename}.txt")
    # Open the file in 'w' mode (write mode) which will overwrite the file if it already exists
    with open(file_path, 'w') as file:
        # Write the usernames to the file
        file.write(",".join(usernames))
    # Delete the input box text on the GUI
    entry.delete("0.0", "end")
    # Insert the scraped usernames into the input box
    entry.insert("0.0", ",".join(usernames))
    # Call the completion function
    complete_automation()
    

# Function to process the comma-separated list of Instagram users
def process_username_list(user_list):
    # Check if the user_list is an array
    if isinstance(user_list, list):
        # If it is a list, then strip the whitespace around each user in the list and return the result
        return [u.strip() for u in user_list]
    # Check if the user_list is a string
    elif isinstance(user_list, str):
        # If  it is then split the list by commas and return the result
        return user_list.split(',')
    else:
        # Otherwise return null
        return None

# Function to process user input to determine input type
def process_input(user_input):
    # If user input contains Instagram username (@Username)
    if re.match(r'@([A-Za-z0-9_.]+)', user_input):
        # Return input type 1: Single Instagram Username
        return [1, user_input]
    # If user input contains a CSV or list of multiple Instagram usernames
    elif ',' in user_input or isinstance(user_input, list):
        # Process user input to a list
        user_list = process_username_list(user_input)
        # Return input type 2: List of Instagram Usernames
        return [2, user_list]
    # If user input contains a URL to be scraped for Instagram usernames
    elif user_input.startswith("http"):
        # Return input type 3: Webpage URL
        return [3, user_input]
    # If user input does not contain Instagram usernames or URL
    else:
        # Return input type 0: Null
        return [0, None]


# Function to start automation
def start_automation():
    # Start updating the status
    update_status_loop()
    global automation_running
    if not automation_running:
        # Get user input from the input box on the GUI
        user_input = entry.get("0.0", "end")
        log_status(user_input)
        # Set input_type and input_value as processed user input and determined type
        [input_type, input_value] = process_input(user_input)
        
        # If the determined type is null
        if input_type == 0:
            log_status("Error: Wrong input format")
            
        # If the determined type is a single Instagram username
        elif input_type == 1:
            log_status("Scraping all user's photos")
            scrape_user_photos(input_value)
            
        # If the determined type is a list of Instagram usernames
        elif input_type == 2:
            log_status("Scraping all photos of each user in the list")
            user_list = process_username_list(input_value)
            scrape_all_user_photos(user_list)
            
        # If the determined type is a URL to be scraped
        elif input_type == 3:
            log_status("Scraping URL for Instagram usernames")
            scrape_webpage_for_usernames(input_value)
        
        # If the type is not determined
        else:
            log_status("Invalid input")
            
        automation_running = True

# Function to stop automation
def stop_automation():
    global automation_running
    automation_running = False
    log_status("Process stopped")

# Function to complete automation
def complete_automation():
    automation_running=False
    log_status("Restart automation")
    start_automation()
# Function to save settings
def save_settings():
    with open(settings_file, "w") as file:
        json.dump(settings, file)

# Create GUI elements
def create_gui_elements():
    global start_button, stop_button, entry, status_label, theme_selector, font_size_selector
    start_button = ctk.CTkButton(app, text="Start", command=start_automation)
    stop_button  = ctk.CTkButton(app, text="Stop", command=stop_automation)
    entry  = ctk.CTkTextbox(app, activate_scrollbars=True)
    status_label = ctk.CTkLabel(app, text="Status")
    app.grid_columnconfigure((0,2), weight=1)
   #app.grid_rowconfigure((2,3), weight=1)
    # Place GUI elements in a centered manner
    start_button.grid(row=2, column=0, sticky="s", padx=10)
    stop_button.grid(row=2, column=2, sticky="s", padx=10)
    entry.grid(row=0, column=0, columnspan=4, sticky="new", padx=10, pady=10)
    status_label.grid(row=1, column=0, columnspan=4, sticky="ew", padx=1, pady=10)

# Create GUI elements
create_gui_elements()
# Insert default URL
entry.insert("0.0", text="https://en.wikipedia.org/wiki/List_of_most-followed_Instagram_accounts")


# Function to print current status and update status log
def log_status(status):
    print(status)
    status_log.append(status)

# Function to periodically update the status label
def update_status_loop():
    global automation_running, status_log
    if automation_running and status_log:
        status_label.configure(text=status_log[-1])
    app.after(2000, update_status_loop) # Check every 2 seconds
    
# Start the status label update
# update_status_loop()
log_status("Enter a single Instagram username, a list of usernames, or any URL to scrape for usernames")
# Run the GUI
if __name__ == "__main__":
    app.mainloop()
   