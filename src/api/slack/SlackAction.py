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
                    file_path = documents.download(exp.proof_url)
                    slack.upload_file(file_path, channel_id,
                                      description=f'id={exp.id} {exp.payed_on} {exp.amount} {exp.description}')

