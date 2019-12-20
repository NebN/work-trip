from . import slack
from src.persistence import documents, Database


def download_files(user_id, channel_id, date_start, date_end):
    with Database() as db:
        expenses = [e for e in db.get_expenses(user_id, date_start, date_end) if e.proof_url]
        for exp in expenses:
            file_path = documents.download(exp.proof_url)
            slack.upload_file(file_path, channel_id,
                              description=f'id={exp.id} {exp.payed_on} {exp.amount} {exp.description}')


def delete_expense(user_id, channel_id, expense_id):
    with Database() as db:
        expense = db.get_expense(expense_id)
        if not expense:
            slack.send_message(channel_id, 'Expense not found.')
        else:
            if expense.employee_user_id != user_id:
                employee = db.get_employee(user_id)
                slack.send_message(channel_id, f'This expense does not belong to you {employee.user_name}.')
            else:
                if db.delete_expense(expense):
                    slack.send_message(channel_id, f'Expense [{expense}] deleted successfully.')
                else:
                    slack.send_message(channel_id, 'Something went wrong while deleting the expense.')
