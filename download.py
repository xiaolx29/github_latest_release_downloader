import requests

from submodule_reattempt import ReAttempt

owner = input('owner:')
repo = input('repo:')
github_url = 'https://api.github.com/repos/{}/{}/releases/latest'.format(owner, repo)

response = requests.get(url = github_url)

print(response.json())
