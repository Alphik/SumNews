<<<<<<< HEAD
###### imports for reading websites.
import requests
from bs4 import BeautifulSoup
###### import for creating folders.
import os
###### import for day and time.
from datetime import datetime
###### imports for diable unessery warnings
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
###### imports for zip
# import shutil

###### imports for summarize the article content
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

###### For running schedule
import schedule
import time

##### For sending Email
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header


URL = 'https://www.ynet.co.il/'


###### main function.
def get_news(USER_INPUT,user_email):
    response = requests.get(URL)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        headlines = soup.select('.slotTitle a, .textDiv a')
        folder_path = str(create_folder_with_timestamp(USER_INPUT))
        for headline in headlines:
            title = get_title(headline)
            content = full_content(headline)
            if USER_INPUT in (title or content):
                relevant_news(title,content,folder_path)
            else:
                print("no news good news")
    nfolder = folder_path.replace("\\", "\\\\")
    pass_sender = pass_for_email()
    send_files_from_folder(nfolder, 'sumnews4you@gmail.com', pass_sender, user_email, USER_INPUT)

    # print(f"Here are your news {folder_path}")



def pass_for_email():
    with open('epass.txt', 'r') as file:
        return file.read()


###### get article url
def get_article_url(headline):
    article_url = headline['href']
    return article_url


###### get article title
def get_title(headline):
    # print(f"Article title: {headline.get_text(strip=True)}")
    return headline.get_text(strip=True)


###### get article full content
def full_content(headline):
    arturl = get_article_url(headline)
    response = requests.get(arturl)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        hebrew_elements = soup.find_all(['div', 'span'],
                                        class_=['text_editor_paragraph', 'public-DraftStyleDefault-block',
                                                'public-DraftStyleDefault-rtl'])
        # Extract text from the found elements
        hebrew_text = []
        for i, element in enumerate(hebrew_elements):
            if i%2 != 0:
                hebrew_text.append(element.get_text(strip=True))
        hebrew_text = "\n".join(hebrew_text)
        return hebrew_text , arturl
    else:
        return f"Failed to retrieve content. Status code: {response.status_code}"


###### get summarize article content
def summarize_hebrew_text(text, sentences_count=3):
    if sentences_count == 0:
        hedlind = text.split(' ')
        hedlind_sum = hedlind[0]+ '_' + hedlind[1]
        return hedlind_sum
    # Initialize a parser with the provided Hebrew text
    parser = PlaintextParser.from_string(text, Tokenizer('hebrew'))

    # Initialize LSA summarizer and summarize the text
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)

    # Combine the summarized sentences into a single string
    summarized_text = ' '.join([str(sentence) for sentence in summary])

    return summarized_text


###### create results folder
def create_folder_with_timestamp(base_folder):
    # Get the current directory
    current_dir = os.getcwd()

    # Get the current date and time
    timestamp = datetime.now().strftime("%H-%M-%S_%d.%m.%Y")
    timestamp_day = datetime.now().strftime("%d.%m.%Y")

    # Construct the folder path relative to current directory and results folder
    results = os.path.join('results', timestamp_day)
    folder_name = f"{base_folder}_{timestamp}"
    folder_path = os.path.join(current_dir, results, folder_name)

    # Create the new directory
    try:
        os.makedirs(folder_path, exist_ok=True)
        print(f"Folder '{folder_path}' created successfully.")
        return folder_path
    except Exception as e:
        print(f"An error occurred: {e}")


# ###### Zip the result folder
# def zip_folder(folder_path, output_zip_path):
#
#     try:
#         # Create a zip file from the folder
#         shutil.make_archive(output_zip_path, 'zip', folder_path)
#         print(f"Folder '{folder_path}' zipped successfully as '{output_zip_path}.zip'.")
#         try:
#             shutil.rmtree(folder_path)
#             print(f"Successfully deleted {folder_path}")
#         except Exception as e:
#             print(f"Error deleting {folder_path}: {e}")
#     except Exception as e:
#         print(f"An error occurred: {e}")


###### Save relevant news in the result folder
def relevant_news(headline, content,folder_path):
    # timestamp = datetime.now().strftime("%f")[-2:-1]
    summarized_text = summarize_hebrew_text(content[0],3)
    summarized_headline = summarize_hebrew_text(headline,0)
    # הגדרת נתיב מוחלט
    file_path = f'{folder_path}\\{summarized_headline}.txt'.replace(',','')
    print(file_path)
    # פתיחת קובץ במצב כתיבה
    with open(file_path, "w") as file:
        file.write(f"כתבה מאתר  {URL}:\n")
        file.write(f"לינק לכתבה:\n {content[1]}\n")
        file.write(f"כותרת:\n {headline}\n")
        # file.write(f"Article content: \n {content[0]}")
        file.write(f"סיכום הכתבה:\n {summarized_text}\n")
        file.close()

    print(f"Article from {URL}:")
    print(f"Article title: {headline}")
    print(f"Link to article title: {content[1]}")
    print(f"Article content: \n {content[0]}")
    print(f"Article summarized:\n {summarized_text}")
    # print(summarized_text)
    print('-' * 100, '\n')


def send_files_from_folder(folder_path, sender_email, sender_password, recipient_email,user_input):
    # For connecting to the gmail server
    smtp_server = 'smtp.gmail.com'
    port = 587

    subj = folder_path.split('\\\\')
    subjn =subj[-1]

    # Creating new email message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = f'SumNews for you - {subjn}'

    # Checking all the files in the required folder
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)):
            # Adding the files to the mail as attachment
            with open(os.path.join(folder_path, filename), "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)

                # Handling Hebrew filenames with Base64 encoding
                encoded_filename = Header(filename, 'utf-8').encode()
                part.add_header('Content-Disposition', f'attachment; filename="{encoded_filename}"')
                message.attach(part)

    # Sending the email
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, recipient_email, text)
    print(f'The news {subjn} are sent to {recipient_email}')


def time_calc():
    next_run = schedule.next_run()
    time_now = datetime.now()
    time_to_next_run = str(next_run - time_now)[:8]
    formatted_time = next_run.strftime("%d-%m-%Y %H:%M:%S")
    return formatted_time, time_to_next_run


def schedule_task():
    how_often = input("How often do you want to run the script? (hourly/daily/once): ").strip().lower()
    options = ['hourly', 'daily', 'once']
    if how_often not in options:
        print("Invalid input. Please enter hourly, daily or once.")
        schedule_task()
    USER_INPUT = input("enter your search word:").strip()
    user_email = input('Enter your email:')
    if how_often == 'hourly':
        schedule.every(2).minutes.do(lambda: get_news(USER_INPUT,user_email))
        # schedule.every().hour.do(get_news(USER_INPUT))  # Run every hour
        get_news(USER_INPUT,user_email)
    elif how_often == 'daily':
        schedule.every().day.at("09:00").do(lambda: get_news(USER_INPUT,user_email))
        get_news(USER_INPUT,user_email)
    elif how_often == 'once':
        get_news(USER_INPUT,user_email)
        exit()

    while True:
        schedule.run_pending()
        time.sleep(5)
        timec = time_calc()
        print(f'The next run is at: {timec[0]} \nTime till next run: {timec[1]}')



schedule_task()
=======
###### imports for reading websites.
import requests
from bs4 import BeautifulSoup
###### import for creating folders.
import os
###### import for day and time.
from datetime import datetime
###### imports for diable unessery warnings
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
###### imports for zip
# import shutil

###### imports for summarize the article content
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

###### For running schedule
import schedule
import time

##### For sending Email
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header


URL = 'https://www.ynet.co.il/'


###### main function.
def get_news(USER_INPUT,user_email):
    response = requests.get(URL)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        headlines = soup.select('.slotTitle a, .textDiv a')
        folder_path = str(create_folder_with_timestamp(USER_INPUT))
        for headline in headlines:
            title = get_title(headline)
            content = full_content(headline)
            if USER_INPUT in (title or content):
                relevant_news(title,content,folder_path)
            else:
                print("no news good news")
    nfolder = folder_path.replace("\\", "\\\\")
    pass_sender = pass_for_email()
    send_files_from_folder(nfolder, 'sumnews4you@gmail.com', pass_sender, user_email, USER_INPUT)

    # print(f"Here are your news {folder_path}")



def pass_for_email():
    with open('epass.txt', 'r') as file:
        return file.read()


###### get article url
def get_article_url(headline):
    article_url = headline['href']
    return article_url


###### get article title
def get_title(headline):
    # print(f"Article title: {headline.get_text(strip=True)}")
    return headline.get_text(strip=True)


###### get article full content
def full_content(headline):
    arturl = get_article_url(headline)
    response = requests.get(arturl)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        hebrew_elements = soup.find_all(['div', 'span'],
                                        class_=['text_editor_paragraph', 'public-DraftStyleDefault-block',
                                                'public-DraftStyleDefault-rtl'])
        # Extract text from the found elements
        hebrew_text = []
        for i, element in enumerate(hebrew_elements):
            if i%2 != 0:
                hebrew_text.append(element.get_text(strip=True))
        hebrew_text = "\n".join(hebrew_text)
        return hebrew_text , arturl
    else:
        return f"Failed to retrieve content. Status code: {response.status_code}"


###### get summarize article content
def summarize_hebrew_text(text, sentences_count=3):
    if sentences_count == 0:
        hedlind = text.split(' ')
        hedlind_sum = hedlind[0]+ '_' + hedlind[1]
        return hedlind_sum
    # Initialize a parser with the provided Hebrew text
    parser = PlaintextParser.from_string(text, Tokenizer('hebrew'))

    # Initialize LSA summarizer and summarize the text
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)

    # Combine the summarized sentences into a single string
    summarized_text = ' '.join([str(sentence) for sentence in summary])

    return summarized_text


###### create results folder
def create_folder_with_timestamp(base_folder):
    # Get the current directory
    current_dir = os.getcwd()

    # Get the current date and time
    timestamp = datetime.now().strftime("%H-%M-%S_%d.%m.%Y")
    timestamp_day = datetime.now().strftime("%d.%m.%Y")

    # Construct the folder path relative to current directory and results folder
    results = os.path.join('results', timestamp_day)
    folder_name = f"{base_folder}_{timestamp}"
    folder_path = os.path.join(current_dir, results, folder_name)

    # Create the new directory
    try:
        os.makedirs(folder_path, exist_ok=True)
        print(f"Folder '{folder_path}' created successfully.")
        return folder_path
    except Exception as e:
        print(f"An error occurred: {e}")


# ###### Zip the result folder
# def zip_folder(folder_path, output_zip_path):
#
#     try:
#         # Create a zip file from the folder
#         shutil.make_archive(output_zip_path, 'zip', folder_path)
#         print(f"Folder '{folder_path}' zipped successfully as '{output_zip_path}.zip'.")
#         try:
#             shutil.rmtree(folder_path)
#             print(f"Successfully deleted {folder_path}")
#         except Exception as e:
#             print(f"Error deleting {folder_path}: {e}")
#     except Exception as e:
#         print(f"An error occurred: {e}")


###### Save relevant news in the result folder
def relevant_news(headline, content,folder_path):
    # timestamp = datetime.now().strftime("%f")[-2:-1]
    summarized_text = summarize_hebrew_text(content[0],3)
    summarized_headline = summarize_hebrew_text(headline,0)
    # הגדרת נתיב מוחלט
    file_path = f'{folder_path}\\{summarized_headline}.txt'.replace(',','')
    print(file_path)
    # פתיחת קובץ במצב כתיבה
    with open(file_path, "w") as file:
        file.write(f"כתבה מאתר  {URL}:\n")
        file.write(f"לינק לכתבה:\n {content[1]}\n")
        file.write(f"כותרת:\n {headline}\n")
        # file.write(f"Article content: \n {content[0]}")
        file.write(f"סיכום הכתבה:\n {summarized_text}\n")
        file.close()

    print(f"Article from {URL}:")
    print(f"Article title: {headline}")
    print(f"Link to article title: {content[1]}")
    print(f"Article content: \n {content[0]}")
    print(f"Article summarized:\n {summarized_text}")
    # print(summarized_text)
    print('-' * 100, '\n')


def send_files_from_folder(folder_path, sender_email, sender_password, recipient_email,user_input):
    # For connecting to the gmail server
    smtp_server = 'smtp.gmail.com'
    port = 587

    subj = folder_path.split('\\\\')
    subjn =subj[-1]

    # Creating new email message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = f'SumNews for you - {subjn}'

    # Checking all the files in the required folder
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)):
            # Adding the files to the mail as attachment
            with open(os.path.join(folder_path, filename), "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)

                # Handling Hebrew filenames with Base64 encoding
                encoded_filename = Header(filename, 'utf-8').encode()
                part.add_header('Content-Disposition', f'attachment; filename="{encoded_filename}"')
                message.attach(part)

    # Sending the email
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, recipient_email, text)
    print(f'The news {subjn} are sent to {recipient_email}')


def time_calc():
    next_run = schedule.next_run()
    time_now = datetime.now()
    time_to_next_run = str(next_run - time_now)[:8]
    formatted_time = next_run.strftime("%d-%m-%Y %H:%M:%S")
    return formatted_time, time_to_next_run


def schedule_task():
    how_often = input("How often do you want to run the script? (hourly/daily/once): ").strip().lower()
    options = ['hourly', 'daily', 'once']
    if how_often not in options:
        print("Invalid input. Please enter hourly, daily or once.")
        schedule_task()
    USER_INPUT = input("enter your search word:").strip()
    user_email = input('Enter your email:')
    if how_often == 'hourly':
        schedule.every(2).minutes.do(lambda: get_news(USER_INPUT,user_email))
        # schedule.every().hour.do(get_news(USER_INPUT))  # Run every hour
        get_news(USER_INPUT,user_email)
    elif how_often == 'daily':
        schedule.every().day.at("09:00").do(lambda: get_news(USER_INPUT,user_email))
        get_news(USER_INPUT,user_email)
    elif how_often == 'once':
        get_news(USER_INPUT,user_email)
        exit()

    while True:
        schedule.run_pending()
        time.sleep(5)
        timec = time_calc()
        print(f'The next run is at: {timec[0]} \nTime till next run: {timec[1]}')



schedule_task()
>>>>>>> 36c9162 (Initial commit)
