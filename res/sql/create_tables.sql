create table employee (
	user_id text primary key not null,
	user_name text unique not null,
	channel_id text unique
);

create table email (
	address text primary key not null,
	employee_user_id text not null references employee(user_id),
	verified boolean default (false)
);

create table expense (
    id serial primary key,
    employee_user_id text not null references employee(user_id),
    payed_on date not null,
    amount numeric(8, 2) not null,
    description text,
    proof_url text
);

create table expense_pending (
    id serial primary key,
    employee_user_id text not null references employee(user_id),
    payed_on date not null,
    amount numeric(8, 2) not null,
    description text,
    proof_url text,
    outcome text
);
