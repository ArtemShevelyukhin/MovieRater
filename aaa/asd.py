class Employee:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __str__(self):
        return f'{self.name} {self.email}'

class RegularEmployee(Employee):
    def __init__(self, name, email, salary):
        super().__init__(name, email)
        self.salary = salary

    def calculate_payment(self):
        return self.salary

class RegularDeveloperEmployee(RegularEmployee):
    def __init__(self, name, email, salary, programming_language):
        super().__init__(name, email, salary)
        self.programming_language = programming_language
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)
        print(f'{self.name} get the task {task}')

    def process_tasks(self):
        for task in self.tasks:
            print(f'{self.name} writing code for task {task}')

        self.tasks.clear()
        print(f'{self.name} completed all tasks')

class RegularManagerEmployee(RegularEmployee):
    def __init__(self, name, email, salary, team_name):
        super().__init__(name, email, salary)
        self.team_name = team_name
        self.developers = []
        self.team_tasks = []

    def add_task_to_team(self, task):
        self.team_tasks.append(task)

    def add_developer_to_team(self, developer):
        self.developers.append(developer)

    def assign_tasks_to_developer(self, tasks):
        for task, developer in zip(self.team_tasks, self.developers):
            developer.add_task(task)

    def start_sprint(self):
        print('')
        for developer in self.developers:
            developer.process_tasks()

    def finsh_sprint(self):
        self.team_tasks.clear()

# TODO: add support for contractor employees (developer and managers)
class ContractorEMployee(Employee):

    def __init__(self, name, email, hourly_rate):
        super().__init__(name, email)
        self.hourly_rate = hourly_rate
        self.hours_worked = 0

    def calculate_payment(self):
        return self.hours_worked  * self.hourly_rate

