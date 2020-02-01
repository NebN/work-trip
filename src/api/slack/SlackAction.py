from abc import abstractmethod
from src.persistence import Database, documents
from src.api.slack import slack
from src.util import fileutil
from src import log


class SlackAction:
    @abstractmethod
    def execute(self, user_id, channel_id, response_url):
        pass


class DeleteExpense(SlackAction):
    def __init__(self, expense_id):
        self.expense_id = expense_id

    def execute(self, user_id, channel_id, response_url):
        with Database() as db:
            expense = db.get_expense(self.expense_id)
            if not expense:
                slack.post_ephemeral(channel_id, user_id, 'Expense not found.')
            else:
                if expense.employee_user_id != user_id:
                    employee = db.get_employee(user_id)
                    slack.post_ephemeral(channel_id, user_id,
                                         f'This expense does not belong to you {employee.user_name}.')
                else:
                    if db.delete_expense(expense):
                        slack.replace_original(f'{expense} deleted successfully.', response_url)
                    else:
                        slack.post_ephemeral(channel_id, user_id, 'Something went wrong while deleting the expense.')


class DownloadAttachments(SlackAction):
    def __init__(self, date_start, date_end, merge):
        self.date_start = date_start
        self.date_end = date_end
        self.merge = merge

    def execute(self, user_id, channel_id, response_url):
        with Database() as db:
            expenses = [e for e in db.get_expenses(user_id, self.date_start, self.date_end) if e.proof_url]
            if len(expenses) == 0:
                slack.post_ephemeral(channel_id, user_id,
                                     f'No attachments found between {self.date_start} and {self.date_end}')
            else:
                if self.merge:
                    slack.post_message(channel_id=channel_id, text=f'Sending attachments from '
                                                                   f'{self.date_start} to {self.date_end}, '
                                                                   f'this might take a few moments.')
                    paths = [documents.download(e.proof_url) for e in expenses]
                    merged = fileutil.merge_to_pdf(paths, name=f'expenses_{self.date_start}_{self.date_end}.pdf')
                    slack.file_upload(merged, channel_id, description='')
                else:
                    for exp in expenses:
                        shared = slack.file_share(channel_id=channel_id, external_id=exp.external_id)
                        # Slack's free tier does not conserve all chat messages and shared files,
                        # because of this the requested file might have expired.
                        if not shared:
                            file_path = documents.download(exp.proof_url)
                            title = str(exp)
                            file_id = slack.file_upload(file_path, channel_id, description=title)
                            external_id = slack.file_add(title=title, file_id=file_id)
                            exp.external_id = external_id
                            db.update_expense(exp)


class Ask(SlackAction):
    def __init__(self, question, request_text):
        self.question = question
        self.request_text = request_text
        self.logger = log.get_logger(__name__)

    def execute(self, user_id, channel_id, response_url):
        if self.question == 'download':
            slack.ask_download(channel_id, self.request_text)
        else:
            self.logger.warn('unexpected question: %s', self.question)


class DestroyPlanet(SlackAction):
    def execute(self, user_id, channel_id, response_url):
        slack.post_message(channel_id, 'Not yet implemented, enjoy this video instead.'
                                       '\nhttps://www.youtube.com/watch?v=izhGLGPmvIU&feature=youtu.be&t=88')