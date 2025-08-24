#!/usr/bin/env python3
"""
Test script to debug email processing issues
"""

import os
import imaplib
import email
import ssl
from email.header import decode_header

def test_email_processing():
    email_address = "johnnie_watson_3rd@mac.com"
    app_password = "zqmt-oukn-nkif-rvcr"
    imap_server = "imap.mail.me.com"
    imap_port = 993
    
    try:
        # Connect to IMAP
        print("Connecting to IMAP server...")
        context = ssl.create_default_context()
        connection = imaplib.IMAP4_SSL(imap_server, imap_port, ssl_context=context)
        connection.login(email_address, app_password)
        print("Connected successfully")
        
        # List all folders
        print("Listing all folders...")
        status, folders = connection.list()
        if status != 'OK':
            print("Failed to list folders")
            return
        
        print("Available folders:")
        for folder in folders:
            folder_str = folder.decode('utf-8') if isinstance(folder, bytes) else str(folder)
            print(f"  {folder_str}")
        
        # Find Mingus folder
        print("\nLooking for Mingus folders...")
        mingus_folders = []
        for folder in folders:
            folder_str = folder.decode('utf-8') if isinstance(folder, bytes) else str(folder)
            folder_name = folder_str.split('"')[-2] if '"' in folder_str else folder_str.split()[-1]
            if 'mingus' in folder_name.lower():
                mingus_folders.append(folder_name)
        
        if not mingus_folders:
            print("No Mingus folders found")
            return
        
        print(f"Found Mingus folders: {mingus_folders}")
        
        # Try the regular Mingus folder first
        mingus_folder = "Mingus"
        print(f"Using folder: {mingus_folder}")
        
        # Select folder and get first email
        connection.select(mingus_folder)
        
        # Try different search criteria
        print("Trying different search criteria...")
        
        # Try ALL emails
        status, messages = connection.search(None, 'ALL')
        if status != 'OK':
            print("Failed to search ALL emails")
            return
        
        all_emails = messages[0].split()
        print(f"ALL search found {len(all_emails)} emails")
        
        # Try RECENT emails
        status, messages = connection.search(None, 'RECENT')
        if status == 'OK':
            recent_emails = messages[0].split()
            print(f"RECENT search found {len(recent_emails)} emails")
        else:
            print("RECENT search failed")
            recent_emails = []
        
        # Try UNSEEN emails
        status, messages = connection.search(None, 'UNSEEN')
        if status == 'OK' and messages and messages[0]:
            unseen_emails = messages[0].split()
            print(f"UNSEEN search found {len(unseen_emails)} emails")
        else:
            print("UNSEEN search failed")
            unseen_emails = []
        
        # Use the search that found the most emails
        if len(recent_emails) > len(all_emails):
            email_ids = recent_emails
            print("Using RECENT emails")
        elif len(unseen_emails) > len(all_emails):
            email_ids = unseen_emails
            print("Using UNSEEN emails")
        else:
            email_ids = all_emails
            print("Using ALL emails")
        if not email_ids:
            print("No emails found")
            return
        
        print(f"Found {len(email_ids)} email IDs")
        print(f"First few email IDs: {email_ids[:5]}")
        
        # Try the first few email IDs
        for i, email_id in enumerate(email_ids[:3]):
            print(f"\nTrying email ID {i+1}: {email_id}")
            
            # Try different fetch commands
            print(f"Trying different fetch commands for email {email_id}...")
            
            # Try RFC822
            status, data = connection.fetch(email_id, '(RFC822)')
            if status == 'OK' and data and len(data) > 0 and len(data[0]) > 1:
                if not isinstance(data[0][1], int):
                    raw_email = data[0][1]
                    print(f"RFC822 successful - Raw email type: {type(raw_email)}")
                    try:
                        email_message = email.message_from_bytes(raw_email)
                        print(f"Successfully parsed email: {email_message.get('Subject', 'No subject')}")
                        break
                    except Exception as e:
                        print(f"Error parsing RFC822 email: {e}")
            
            # Try BODY
            status, data = connection.fetch(email_id, '(BODY)')
            if status == 'OK' and data and len(data) > 0:
                print(f"BODY fetch response: {data}")
                
                # Try to fetch the actual body content
                try:
                    status, body_data = connection.fetch(email_id, '(BODY[1])')
                    if status == 'OK' and body_data and len(body_data) > 0:
                        print(f"BODY[1] fetch successful - type: {type(body_data[0])}")
                        if len(body_data[0]) > 1 and isinstance(body_data[0][1], bytes):
                            body_content = body_data[0][1]
                            print(f"Body content length: {len(body_content)}")
                            print(f"Body content preview: {body_content[:200]}...")
                            
                            # Try to decode as email
                            try:
                                email_message = email.message_from_bytes(body_content)
                                print(f"Successfully parsed email from BODY[1]: {email_message.get('Subject', 'No subject')}")
                                break
                            except Exception as e:
                                print(f"Error parsing BODY[1] as email: {e}")
                except Exception as e:
                    print(f"Error fetching BODY[1]: {e}")
            
            # Try UID
            status, data = connection.fetch(email_id, '(UID)')
            if status == 'OK' and data and len(data) > 0:
                print(f"UID fetch response: {data}")
            
            print("All fetch methods failed for this email")
            continue
        else:
            print("Could not find any valid emails to process")
            return
        

        
        print(f"Email subject: {email_message.get('Subject', 'No subject')}")
        print(f"Email from: {email_message.get('From', 'No from')}")
        print(f"Email date: {email_message.get('Date', 'No date')}")
        print(f"Is multipart: {email_message.is_multipart()}")
        
        # Try to get payload
        if email_message.is_multipart():
            print("Processing multipart email...")
            for part in email_message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                
                content_type = part.get_content_type()
                print(f"Content type: {content_type}")
                
                try:
                    payload = part.get_payload(decode=True)
                    print(f"Payload type: {type(payload)}")
                    print(f"Payload value: {payload}")
                    
                    if isinstance(payload, bytes):
                        text = payload.decode('utf-8', errors='ignore')
                        print(f"Decoded text length: {len(text)}")
                    elif isinstance(payload, int):
                        text = str(payload)
                        print(f"Integer payload: {text}")
                    else:
                        text = str(payload)
                        print(f"Other payload: {text}")
                        
                except Exception as e:
                    print(f"Error processing payload: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print("Processing single part email...")
            try:
                payload = email_message.get_payload(decode=True)
                print(f"Payload type: {type(payload)}")
                print(f"Payload value: {payload}")
                
                if isinstance(payload, bytes):
                    text = payload.decode('utf-8', errors='ignore')
                    print(f"Decoded text length: {len(text)}")
                elif isinstance(payload, int):
                    text = str(payload)
                    print(f"Integer payload: {text}")
                else:
                    text = str(payload)
                    print(f"Other payload: {text}")
                    
            except Exception as e:
                print(f"Error processing payload: {e}")
                import traceback
                traceback.print_exc()
        
        connection.logout()
        print("Test completed")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email_processing()
