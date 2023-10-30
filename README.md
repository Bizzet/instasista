# instaSista v1.0
### Instagram Profile & Photo Scraper with Sexy GUI

This little script is a user-friendly way to scrape lots of Instagram photos automatically by first scraping any URL for Instagram usernames in the @username format then sequentially downloading all the photos of each Instagram user in the scraped list. Alternatively, you can enter a @username or a comma-seperated list of @usernames and it will skip the URL scraping process and get straight to downloading all the photos of each user.

### Produdly Dependent On
- Tkinter for GUI framework
- CTkinter (Custom Tkinter) for GUI styling
- BeautifulSoup for @username scraping
- InstaLoader for Instagram functions

## Overview
- Start the application
- GUI : Opens immediately 
- Start Button : Starts the process
- Stop Button : Stops the process
- Textbox : Accepts URL or Instagram @usernames
- Status Label : Displays current status of the application

## Process

#### Scrape A URL For Instagram Usernames
- Enter any URL that contains Instagram usernames in the @username format
- Press the start button
- InstaSista will use BeautifulSoup and Regular Expressions to scrape all @usernames from the page
- InstaSista will save all @usernames as a JSON file with a filename matching the URL scraped
- InstaSista will automatically load all the @usernames into the textbox replacing the URL string
- InstaSista will begin scraping the photos of each user

#### Scrape Photos of Instagram Profiles
- Enter a single Instagram username or multiple Instagram usernames separated by commas
- InstaSista will go through each profile in the username list one at a time
- Instasista will download all the photos of the user before continuing to the next user
- All photos will be saved in seperate folders
- No post metadata will be saved with the photos to prevent a cluttered mess
- InstaSista will download all the photos of each user until the process is complete


## Setup
1. Setup Python enviroment
2. Clone project to enviroment
3. Download dependencies
4. Run app.py

