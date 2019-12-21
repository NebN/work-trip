from abc import abstractmethod
from src.persistence import Database, documents
from src.api.slack import slack

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
    def __init__(self, date_start, date_end):
        self.date_start = date_start
        self.date_end = date_end

    def execute(self, user_id, channel_id, response_url):
        with Database() as db:
            expenses = [e for e in db.get_expenses(user_id, self.date_start, self.date_end) if e.proof_url]
            if len(expenses) == 0:
                slack.post_ephemeral(channel_id, user_id,
                                     f'No attachments found between {self.date_start} and {self.date_end}')
            else:
                for exp in expenses:
                    shared = slack.file_share(channel_id=channel_id, external_id=exp.external_id)
                    if not shared:
                        file_path = documents.download(exp.proof_url)
                        title = str(exp)
                        file_id = slack.file_upload(file_path, channel_id, description=title)
                        external_id = slack.file_add(title=title, file_id=file_id)
                        exp.external_id = external_id
                        db.update_expense(exp)


class DestroyPlanet(SlackAction):
    def execute(self, user_id, channel_id, response_url):
        slack.post_message(channel_id, 'Not yet implemented, enjoy this video instead.'
                                       '\nhttps://www.youtube.com/watch?v=izhGLGPmvIU&feature=youtu.be&t=88')