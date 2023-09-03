from.forms import AccountSettingsForm
import imaplib
import time
from django.shortcuts import render
import asyncio



def mark_message_as_read(imap_server, message_id):
    message_id_str = str(message_id, 'utf-8')
    imap_server.store(message_id_str, '+FLAGS', '\\Seen')
    print('Marked message as read:', message_id_str)

async def process_account(account, num_messages, stop_flag):
    IMAP_SERVER = account['IMAP_SERVER']
    USERNAME = account['USERNAME']
    PASSWORD = account['PASSWORD']
    with imaplib.IMAP4_SSL(IMAP_SERVER) as imap_server:
        imap_server.login(USERNAME, PASSWORD)
        imap_server.select('INBOX')
        _, response = imap_server.search(None, 'UNSEEN')
        message_ids = response[0].split()[-num_messages:]
        
        
        if not message_ids:
            print('No unseen messages.')
            return
        
        total_marked_messages = 0  

        for message_id in message_ids:
            if stop_flag.is_set() or total_marked_messages >= num_messages:
                return  
            mark_message_as_read(imap_server, message_id)
            total_marked_messages += 1
            await asyncio.sleep(0)  

async def process_spam_account(account, num_messages, stop_flag):
    IMAP_SERVER = account['IMAP_SERVER']
    USERNAME = account['USERNAME']
    PASSWORD = account['PASSWORD']
    with imaplib.IMAP4_SSL(IMAP_SERVER) as imap_server:
        imap_server.login(USERNAME, PASSWORD)
        
        imap_server.select('[Gmail]/&BCEEPwQwBDw-')
        _, response = imap_server.search(None, 'UNSEEN')
        message_ids = response[0].split()[-num_messages:]

        
        if not message_ids:
            print('No unseen spam messages.')
            return

        total_marked_messages = 0  

        for message_id in message_ids:
            if stop_flag.is_set() or total_marked_messages >= num_messages:
                return  
            mark_message_as_read(imap_server, message_id)
            total_marked_messages += 1
            await asyncio.sleep(0) 




async def mark_messages_as_read(request):
    if request.method == 'POST':
        start_time = time.time()
        form = AccountSettingsForm(request.POST)
        if form.is_valid():
            accounts_text = form.cleaned_data['accounts']
            num_messages = form.cleaned_data['num_messages']
            accounts_data = accounts_text.strip().split('\n')

            account_settings = []
            for i in range(0, len(accounts_data), 2):
                if i + 1 < len(accounts_data):
                    account_settings.append({
                        'IMAP_SERVER': 'imap.gmail.com',
                        'USERNAME': accounts_data[i].strip(),
                        'PASSWORD': accounts_data[i + 1].strip(),
                    })

            stop_flag = asyncio.Event() 

            tasks = []
            for account in account_settings:
                task = asyncio.create_task(process_account(account, num_messages, stop_flag))
                task = asyncio.create_task(process_spam_account(account, num_messages, stop_flag))
                tasks.append(task)

            await asyncio.gather(*tasks)

            elapsed_time = time.time() - start_time  
            print(f"Elapsed time: {elapsed_time} seconds")


    else:
        form = AccountSettingsForm()

    return render(request, 'reader/mark_messages_as_read.html', {'form': form})
