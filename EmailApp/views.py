from django.shortcuts import render
from django.http import JsonResponse
from django.views import generic
from .forms import SendMailForm,AnswerMailForm
from .gmail import MailManager
from .models import Attachments
from django.conf.global_settings import MEDIA_ROOT
import os
import base64
from .sentences import recognizedsentences
from word2number import w2n
import re

def handle_uploaded_file( f):
    with open(MEDIA_ROOT + '/EmailApp/attachments/' + f, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


class HandleRecognizedSpeech(generic.View):

    def get(self,request):
        data = None
        if "open email with number" in request.GET.get('post_id').lower():
            replaced = request.GET.get('post_id').lower().replace("open email with number ","")
            print('Atleast we reached here')
            services = MailManager()
            if str.isdigit(replaced):
                number = int(replaced)
            else:
                number = w2n.word_to_num(replaced)
            print(number)
            allMessages = services.service.users().messages().list(userId='me').execute()
            messageList = []
            if 'messages' in allMessages:
                for message in allMessages['messages']:
                    messageList.append(services.service.users().messages().get(userId='me', id=message['id']).execute())
            if number < messageList.__len__():
                data = {"message" : "I am reading the message "+ replaced,
                        "url": "http://127.0.0.1:8000/messages/" + messageList[number]['threadId']
                        }
            else:
                data = {"message": "error"}
        elif request.GET.get('post_id') in recognizedsentences.keys():
            data = recognizedsentences.get(request.GET.get('post_id'))
        else:
            data = {"message":"error"}
        return JsonResponse(data,safe=False)

class HandleAjaxSubmit(generic.View):

    def get(self,request):
        services = MailManager()
        profileinfo = services.service.users().getProfile(userId='me').execute()
        receiver = request.GET.get('receiver')
        subject = request.GET.get('subject')
        message = request.GET.get('message')
        returned = services.CreateMessage(str(profileinfo['emailAddress']), str(receiver),
                                          str(subject), str(message))
        services.service.users().messages().send(userId='me', body=returned).execute()
        return JsonResponse({'status':'success'})


class HomeView(generic.View):
    template_name = "inbox.html"

    def get(self,request):
        services = MailManager()

        # this is to show who it is from
        profileInfo = services.service.users().getProfile(userId='me').execute()
        print(profileInfo)

        # this is to show what are the messages
        allMessages = services.service.users().messages().list(userId='me').execute()

        # Each message has a message id and thread id

        messageList = []
        label_list =[]
        if 'messages' in allMessages:
            for message in allMessages['messages']:
                val = services.service.users().messages().get(userId='me', id=message['id']).execute()

                # now this is the actual json with all details

                label_list = val["labelIds"]
                if 'INBOX' in label_list:
                    messageList.append(services.service.users().messages().get(userId='me', id=message['id']).execute())

        # {'id': '1784ef71848bd6f9', 'threadId': '1784ef71848bd6f9', 'labelIds': ['SENT'], 'snippet': '123', 'payload': {'partId': '', 'mimeType': 'text/plain', 'filename': '', 'headers': [{'name': 'Received', 'value': 'from 943456988985 named unknown by gmailapi.google.com with HTTPREST; Sat, 20 Mar 2021 05:28:39 -0400'}, {'name': 'Content-Type', 'value': 'text/plain; charset="us-ascii"'}, {'name': 'MIME-Version', 'value': '1.0'}, {'name': 'Content-Transfer-Encoding', 'value': '7bit'}, {'name': 'to', 'value': 'kritz.rs@gmail.com'}, {'name': 'from', 'value': 'hci.project.email@gmail.com'}, {'name': 'subject', 'value': 'hello'}, {'name': 'Date', 'value': 'Sat, 20 Mar 2021 05:28:39 -0400'}, {'name': 'Message-Id', 'value': '<CAJxKF+cK34-YVocLXxU9xPkYpLe3JVcrAsf=gCSDntTJJrVbKw@mail.gmail.com>'}], 'body': {'size': 3, 'data': 'MTIz'}}, 'sizeEstimate': 420, 'historyId': '1977', 'internalDate': '1616232519000'}

        return render(request,self.template_name,{'profileInfo':profileInfo,'allMessages':messageList,'appname':'VoiceMail'})

class TrashView(generic.View):
    template_name = "inbox.html"

    def get(self,request):
        services = MailManager()

        # this is to show who it is from
        profileInfo = services.service.users().getProfile(userId='me').execute()

        # this is to show what are the messages
        allMessages = services.service.users().messages().list(userId='me',includeSpamTrash=True).execute()

        # Each message has a message id and thread id

        messageList = []
        label_list =[]
        if 'messages' in allMessages:
            for message in allMessages['messages']:
                val = services.service.users().messages().get(userId='me', id=message['id']).execute()
                label_list = val["labelIds"]
                if 'TRASH' in label_list:
                    messageList.append(services.service.users().messages().get(userId='me', id=message['id']).execute())

        return render(request,self.template_name,{'profileInfo':profileInfo,'allMessages':messageList,'appname':'VoiceMail'})

class SentView(generic.View):
    template_name = "inbox.html"

    def get(self,request):
        services = MailManager()

        # this is to show who it is from
        profileInfo = services.service.users().getProfile(userId='me').execute()

        # this is to show what are the messages
        allMessages = services.service.users().messages().list(userId='me').execute()

        # Each message has a message id and thread id

        messageList = []
        label_list =[]
        if 'messages' in allMessages:
            for message in allMessages['messages']:
                val = services.service.users().messages().get(userId='me', id=message['id']).execute()

                # now this is the actual json with all details

                label_list = val["labelIds"]
                if 'SENT' in label_list:
                    messageList.append(services.service.users().messages().get(userId='me', id=message['id']).execute())

        return render(request,self.template_name,{'profileInfo':profileInfo,'allMessages':messageList,'appname':'VoiceMail'})



class ReadMailView(generic.FormView):
    template_name = "readmail.html"
    form_class = AnswerMailForm
    success_url = "/"

    def get(self, request, *args, **kwargs):
        services = MailManager()
        profileinfo = services.service.users().getProfile(userId='me').execute()
        #print(profileinfo)
        message = services.service.users().messages().get(userId='me', id=self.kwargs['messageid'], format="full").execute()
        # Get value of 'payload' from dictionary 'txt'
        payload = message['payload']

        #print(payload)
        # The Body of the message is in Encrypted format. So, we have to decode it.
        # Get the data and decode it with base 64 decoder.
        body=""
        if(payload['mimeType']=='multipart/alternative'):
            parts = payload.get('parts')
            print(len(parts))
            part =parts[0]
            #print(part)
            data = part['body']['data']
            data = data.replace("-","+").replace("_","/")
            decoded_data = base64.b64decode(data)
            #print(data.decode("utf-8"))
            x=decoded_data.decode("utf-8")
            cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
            cleantext = re.sub(cleanr, '', x)
            body += cleantext
            
        else:
            data = payload['body']['data']
            data = data.replace("-","+").replace("_","/")
            decoded_data = base64.b64decode(data)
            body += decoded_data.decode("utf-8")
            print(body)

        return render(request, self.template_name,{'profileInfo': profileinfo, 'message': message, 'body':body,'form': self.form_class,'appname':'VoiceMail'})

    def form_valid(self, form):
        services = MailManager()
        profileinfo = services.service.users().getProfile(userId='me').execute()
        message = services.service.users().messages().get(userId='me', id=self.kwargs['messageid']).execute()
        subject = None
        receiver = None
        for m in message['payload']['headers']:
            if str.lower(m['name']) == "subject" or str.upper(m['name']) == "SUBJECT":
                subject = m['value']
            elif str.lower(m['name']) == "from" or str.upper(m['name']) == "FROM":
                receiver = m['value']

        if form.cleaned_data['file']:
            print(form.cleaned_data['file'])
            obj = Attachments(file=form.cleaned_data['file'])
            obj.save()
            directory = os.path.dirname(os.path.abspath(str(form.cleaned_data['file'])))
            returned = services.CreateMessageWithAttachment(str(profileinfo['emailAddress']), str(receiver),str(subject), str(form.cleaned_data['message']),str(directory), str(form.cleaned_data['file']))
            services.service.users().messages().send(userId='me', body=returned).execute()
        else:
            returned = services.CreateMessage(profileinfo['emailAddress'], receiver, subject,form.cleaned_data['message'])
            services.service.users().messages().send(userId='me', body=returned).execute()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


class NewMailView(generic.FormView):
    template_name = "create.html"
    form_class = SendMailForm
    success_url = "/"

    def get(self, request, *args, **kwargs):
        services = MailManager()
        profileinfo = services.service.users().getProfile(userId='me').execute()
        return render(request, self.template_name, {'form':self.form_class,'profileInfo':profileinfo,'appname':'VoiceMail'})

    def form_valid(self, form):
        services = MailManager()
        profileinfo = services.service.users().getProfile(userId='me').execute()
        if form.cleaned_data['file']:
            obj = Attachments(file=form.cleaned_data['file'])
            obj.save()
            directory = os.path.dirname(os.path.abspath(str(form.cleaned_data['file'])))
            returned = services.CreateMessageWithAttachment(str(profileinfo['emailAddress']),str(form.cleaned_data['receivers']),str(form.cleaned_data['subject']),str(form.cleaned_data['message']),str(directory),str(form.cleaned_data['file']))
            services.service.users().messages().send(userId='me', body=returned).execute()
        else:
            returned = services.CreateMessage(str(profileinfo['emailAddress']),str(form.cleaned_data['receivers']),str(form.cleaned_data['subject']),str(form.cleaned_data['message']))
            services.service.users().messages().send(userId='me',body=returned).execute()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


class DownloadAttachment(generic.View):

    def get(self,request,messageId):
        services = MailManager()
        message = services.service.users().messages().get(userId='me',id=messageId).execute()
        filename = None
        for part in message['payload']['parts']:
            if part['filename'] is not '':
                attachment = services.service.users().messages().attachments().get(userId='me', id=part['body']['attachmentId'], messageId=messageId).execute()
                file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                basedir = os.path.abspath(os.path.dirname(__file__)) + '/static/downloads/'
                if not os.path.isdir(basedir):
                    os.mkdir(basedir)
                f = open(basedir + part['filename'], 'w')
                f.write(str(file_data))
                f.close()
                filename = part['filename']
        return render(request,'downloaded.html',{'filename':filename})

