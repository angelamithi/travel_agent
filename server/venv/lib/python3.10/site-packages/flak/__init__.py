import importlib.resources

def get():
    data = importlib.resources.files(__package__).joinpath("data.txt").read_text(encoding='utf-8')
    with open(file='test.txt', mode='w', encoding='utf-8') as f:
        f.write(data)
