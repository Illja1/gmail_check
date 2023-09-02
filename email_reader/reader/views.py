from.forms import AccountSettingsForm
import time
import asyncio
import imaplib
from django.shortcuts import render,redirect
from asgiref.sync import sync_to_async



def success_page(request):
        if 'account_settings' in request.session:
            account_settings = request.session['account_settings']
            form = AccountSettingsForm(initial={'accounts': account_settings})
        else:
            form = AccountSettingsForm(request.POST or None)
        return render(request, 'reader/success.html', {'form': form})



def mark_message_as_read(imap_server, message_ids):
    message_ids_str = [str(message_id, 'utf-8') for message_id in message_ids]
    imap_server.store(','.join(message_ids_str), '+FLAGS', '\\Seen')
    print('Marked messages as read:', message_ids_str)


async def process_account(account, num_messages):
    IMAP_SERVER = account['IMAP_SERVER']
    USERNAME = account['USERNAME']
    PASSWORD = account['PASSWORD']
    with imaplib.IMAP4_SSL(IMAP_SERVER) as imap_server:
        try:
            imap_server.login(USERNAME, PASSWORD)
            imap_server.select('INBOX')
            _, response = imap_server.search(None, 'UNSEEN')
            message_ids = response[0].split()[-num_messages:]
            imap_server.select('SPAM')
            _, spam_response = imap_server.search(None, 'UNSEEN')
            spam_message_ids = spam_response[0].split()[-num_messages:]
            message_ids.extend(spam_message_ids)
            if not message_ids:
                return False
            mark_message_as_read(imap_server, message_ids)
            await asyncio.sleep(5)
            return True
        except imaplib.IMAP4.error as e:
            print(f"Error processing account: {account['USERNAME']}. Error message: {str(e)}")
            return False


async def mark_messages_as_read(request):
    if request.method == 'POST':
        start_time = await asyncio.get_event_loop().run_in_executor(None, time.time)
        form = AccountSettingsForm(request.POST)
        if form.is_valid():
            accounts_text = form.cleaned_data['accounts']
            num_messages = form.cleaned_data['num_messages']
            accounts_data = accounts_text.strip().split('\n')
            print(len(accounts_data))
            account_settings = []
            for i in range(0, len(accounts_data), 2):
                if i + 1 < len(accounts_data):
                    email = accounts_data[i].strip()
                    password = accounts_data[i + 1].strip()
                    account_settings.append({
                        'IMAP_SERVER': 'imap.gmail.com',
                        'USERNAME': email,
                        'PASSWORD': password,
                    })
            tasks = []
            for account in account_settings:
                task = asyncio.create_task(process_account(account, num_messages))
                tasks.append(task)
                await asyncio.sleep(5)
            await asyncio.gather(*tasks)
            elapsed_time = await asyncio.get_event_loop().run_in_executor(None, lambda: time.time() - start_time)
            print(f"Elapsed time: {elapsed_time} seconds")
            if all(tasks):
                request.session['account_settings'] = accounts_text.strip()
                return redirect('success')
    else:
        form = AccountSettingsForm()
    return render(request, 'reader/mark_messages_as_read.html', {'form': form})
#time = 340.4146966934204 if number on message - 16k
